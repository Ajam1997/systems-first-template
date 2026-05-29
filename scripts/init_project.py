#!/usr/bin/env python3
"""One-command project initializer for the systems-first template.

Takes a fresh-cloned template with `config/*.yml` filled in and brings
it to a working state:

  1. Resolves the GitHub repo (env / git remote)
  2. Syncs labels from .github/labels.yml
  3. Creates Milestones from config/stages.yml (idempotent)
  4. Activates the discipline agent packs declared in
     config/disciplines.yml (copies agent-packs/<name>/*.md -> .claude/agents/)
  5. (optional) Seeds a starter UN-001 Issue
  6. Runs scripts/generate_docs.py to fill the AUTO sections

Idempotent — running twice is safe. Each step skips work that's already
done and reports what it did vs what was already there.

Usage:
  python scripts/init_project.py --dry-run        # show plan, no writes
  python scripts/init_project.py                  # apply (config must be set)
  python scripts/init_project.py --activate-profile A    # Software profile
  python scripts/init_project.py --activate-profile B    # Mechanical/Hardware
  python scripts/init_project.py --activate-profile C    # Mixed-discipline IoT
  python scripts/init_project.py --seed-sample    # also file UN-001 Issue
  python scripts/init_project.py --skip-labels    # skip label sync step
  python scripts/init_project.py --skip-agents    # leave .claude/agents/ alone

Env:
  GITHUB_TOKEN — required (or `gh auth` configured)
  REPO_OWNER, REPO_NAME — optional; auto-detected from git remote
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout/stderr so unicode arrows + checkmarks don't crash on
# Windows cp1252 consoles. Python 3.7+ TextIOWrapper.reconfigure.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.github_client import GitHubClient
from scripts.sync_labels import (
    apply_changes as labels_apply,
    list_remote_labels as labels_list_remote,
    load_desired_labels as labels_load,
    reconcile as labels_reconcile,
)

REPO_ROOT = Path(__file__).parent.parent
CONFIG = REPO_ROOT / "config"
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
PACKS_DIR = REPO_ROOT / ".claude" / "agent-packs"
LABELS_PATH = REPO_ROOT / ".github" / "labels.yml"

# Preset profile YAML — used by --activate-profile to write a clean
# config/disciplines.yml + config/stages.yml without trying to surgically
# uncomment the multi-profile template file. Each preset is a self-contained
# minimal YAML body; users edit further after writing.

PROFILE_DISCIPLINES = {
    "A": """\
# config/disciplines.yml — Profile A (Software)
# Activated by `init_project.py --activate-profile A`.
disciplines:
  - name: systems_lead
    active: true
    evidence_kinds: [review, inspection]
    responsible_for: requirements tree, architecture, interfaces, budgets

  - name: software_lead
    active: true
    evidence_kinds: [pytest, unittest, e2e, kpm, inspection]
    responsible_for: src/, tests/, software performance KPMs
""",
    "B": """\
# config/disciplines.yml — Profile B (Mechanical / Hardware)
# Activated by `init_project.py --activate-profile B`.
disciplines:
  - name: systems_lead
    active: true
    evidence_kinds: [review, inspection]
    responsible_for: requirements tree, architecture, interfaces, mass+power+thermal budgets

  - name: mechanical_lead
    active: true
    evidence_kinds: [fea, simulation, bench, dvt, evt, pvt, review, dfm]
    responsible_for: CAD assemblies, FEA, manufacturing drawings, tolerance analysis

  - name: manufacturing_lead
    active: true
    evidence_kinds: [dfm, dvt, evt, pvt, review]
    responsible_for: supplier qualification, DFM/DFA reviews, EVT/PVT planning
""",
    "C": """\
# config/disciplines.yml — Profile C (Mixed-discipline IoT)
# Activated by `init_project.py --activate-profile C`.
disciplines:
  - name: systems_lead
    active: true
    evidence_kinds: [review, inspection]
    responsible_for: requirements, interfaces, budgets, integration

  - name: software_lead
    active: true
    evidence_kinds: [pytest, unittest, e2e, inspection]
    responsible_for: cloud-side software, mobile app

  - name: firmware_lead
    active: true
    evidence_kinds: [unittest, hil, bench, simulation, review]
    responsible_for: embedded firmware, RTOS, hardware-software interfaces

  - name: electrical_lead
    active: true
    evidence_kinds: [spice, bench, dvt, evt, emc, review]
    responsible_for: schematics, PCB layout, signal/power integrity, RF compliance

  - name: mechanical_lead
    active: true
    evidence_kinds: [fea, simulation, bench, dvt, evt, dfm, review]
    responsible_for: enclosure, thermal path, antenna mounting, drop-test fixtures

  - name: manufacturing_lead
    active: true
    evidence_kinds: [dfm, evt, pvt, review]
    responsible_for: supplier qualification, EVT/PVT, BOM management

  - name: regulatory_lead
    active: true
    evidence_kinds: [emc, regulatory, review]
    responsible_for: FCC Part 15, CE-RED, RoHS, REACH, applicable safety standards
""",
}

PROFILE_STAGES = {
    "A": """\
# config/stages.yml — Software preset
stages:
  1:
    title: "Stage 1 — Scaffold & Foundation"
    user_needs: [UN-001, UN-002]
    exit_criteria: project structure in place, all agents discoverable
  2:
    title: "Stage 2 — Core Engine"
    user_needs: []
    exit_criteria: primary functionality demonstrable on fixtures
  3:
    title: "Stage 3 — Integration"
    user_needs: []
    exit_criteria: end-to-end pipeline runs on real inputs
  4:
    title: "Stage 4 — V&V"
    user_needs: []
    exit_criteria: all KPMs measured, all user needs validated
  5:
    title: "Stage 5 — Release"
    user_needs: []
    exit_criteria: production deploy + monitoring in place
""",
    "B": """\
# config/stages.yml — Hardware preset (DVT/EVT/PVT gated)
stages:
  1:
    title: "Stage 1 — Concept"
    user_needs: []
    exit_criteria: concept selection, top-level UNs defined, budgets locked
  2:
    title: "Stage 2 — Preliminary Design (PDR)"
    user_needs: []
    exit_criteria: PDR passed, FRs decomposed, interfaces defined
  3:
    title: "Stage 3 — Critical Design (CDR)"
    user_needs: []
    exit_criteria: CDR passed, all NFRs satisfied in simulation/analysis
  4:
    title: "Stage 4 — Engineering Build (EB)"
    user_needs: []
    exit_criteria: first physical build available for bench testing
  5:
    title: "Stage 5 — Design Verification Test (DVT)"
    user_needs: []
    exit_criteria: all DVT procedures pass on EB units
  6:
    title: "Stage 6 — Engineering Verification Test (EVT)"
    user_needs: []
    exit_criteria: EVT build qualified, ECOs frozen
  7:
    title: "Stage 7 — Production Verification Test (PVT)"
    user_needs: []
    exit_criteria: PVT lot qualifies, AQL met, mass production approved
  8:
    title: "Stage 8 — Production"
    user_needs: []
    exit_criteria: shipping to customers
""",
    "C": """\
# config/stages.yml — Mixed-discipline IoT preset (modified hardware flow)
stages:
  1:
    title: "Stage 1 — System Architecture"
    user_needs: []
    exit_criteria: top-level decomposition; cross-discipline interfaces defined
  2:
    title: "Stage 2 — Preliminary Design"
    user_needs: []
    exit_criteria: PCB schematics, mechanical CAD draft, firmware skeleton
  3:
    title: "Stage 3 — Critical Design"
    user_needs: []
    exit_criteria: CDR passed across all disciplines
  4:
    title: "Stage 4 — Engineering Build + Bring-up"
    user_needs: []
    exit_criteria: first integrated build powers on; firmware boots
  5:
    title: "Stage 5 — DVT"
    user_needs: []
    exit_criteria: DVT pass across mech/elec/firmware
  6:
    title: "Stage 6 — Regulatory Pre-compliance"
    user_needs: []
    exit_criteria: EMC pre-compliance scan; RoHS/REACH BOM check
  7:
    title: "Stage 7 — EVT"
    user_needs: []
    exit_criteria: EVT build qualified; full regulatory compliance pass
  8:
    title: "Stage 8 — PVT + Production"
    user_needs: []
    exit_criteria: PVT lot qualifies; shipping
""",
}


def banner(title: str) -> None:
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


def step(msg: str) -> None:
    print(f"\n-> {msg}")


def info(msg: str) -> None:
    print(f"    {msg}")


def warn(msg: str) -> None:
    print(f"  ! {msg}")


# --- Step 0: Validate ------------------------------------------------

def write_profile(profile: str, dry_run: bool) -> tuple[dict, dict]:
    """Overwrite config/disciplines.yml + config/stages.yml from a preset.

    Returns the parsed (disciplines, stages) dicts so downstream steps
    can preview the post-activation state even in dry-run mode (where
    the disk writes are skipped).
    """
    if profile not in PROFILE_DISCIPLINES:
        sys.exit(f"Unknown profile {profile!r}. Valid: A (software), B (mechanical), C (mixed IoT).")
    disc_path = CONFIG / "disciplines.yml"
    stages_path = CONFIG / "stages.yml"
    step(f"Activating Profile {profile} (overwrites disciplines.yml + stages.yml)")
    info(f"  target: {disc_path.relative_to(REPO_ROOT)}")
    info(f"  target: {stages_path.relative_to(REPO_ROOT)}")
    disc_text = PROFILE_DISCIPLINES[profile]
    stages_text = PROFILE_STAGES[profile]
    if dry_run:
        info("(dry-run -- no writes; downstream steps preview Profile " + profile + ")")
    else:
        disc_path.write_text(disc_text, encoding="utf-8")
        stages_path.write_text(stages_text, encoding="utf-8")
        info(f"  wrote {profile}-profile content to both files")
    disc = yaml.safe_load(disc_text) or {}
    stages = yaml.safe_load(stages_text) or {}
    return disc, stages


def validate_configs(preloaded: tuple[dict, dict] | None = None) -> tuple[dict, dict]:
    """Ensure required configs exist and have at least one active discipline.

    If preloaded is given (e.g. from a --activate-profile in-memory parse
    during dry-run), validate that instead of reading from disk. This
    keeps dry-run output coherent with what a live run would produce.

    Returns (disciplines_yaml, stages_yaml).
    """
    step("Validating config/")
    if preloaded is not None:
        disc, stages = preloaded
    else:
        disc_path = CONFIG / "disciplines.yml"
        stages_path = CONFIG / "stages.yml"
        if not disc_path.exists():
            sys.exit(f"Missing {disc_path}. This isn't a systems-first template clone.")
        if not stages_path.exists():
            sys.exit(f"Missing {stages_path}.")

        disc = yaml.safe_load(disc_path.read_text(encoding="utf-8")) or {}
        stages = yaml.safe_load(stages_path.read_text(encoding="utf-8")) or {}

    active = [d for d in (disc.get("disciplines") or []) if d.get("active")]
    if not active:
        sys.exit(
            "No active disciplines in config/disciplines.yml.\n"
            "  Re-run with one of:\n"
            "    python scripts/init_project.py --activate-profile A   # Software\n"
            "    python scripts/init_project.py --activate-profile B   # Mechanical/Hardware\n"
            "    python scripts/init_project.py --activate-profile C   # Mixed-discipline IoT\n"
            "  Or edit config/disciplines.yml manually and uncomment a profile."
        )
    info(f"{len(active)} active discipline(s): {', '.join(d['name'] for d in active)}")

    n_stages = len(stages.get("stages") or {})
    if n_stages == 0:
        sys.exit(
            "No stages in config/stages.yml.\n"
            "  Re-run with --activate-profile to seed both files, or edit manually."
        )
    info(f"{n_stages} stage(s) declared")
    return disc, stages


# --- Step 1: Labels --------------------------------------------------

def sync_labels_step(client: GitHubClient, dry_run: bool) -> None:
    step("Syncing labels from .github/labels.yml")
    desired = labels_load(LABELS_PATH)
    repo_id = f"{client.owner}/{client.repo}"
    existing = labels_list_remote(repo_id)
    creates, updates, deletes = labels_reconcile(desired, existing, allow_extra=False)

    if not (creates or updates or deletes):
        info("labels already in sync")
        return
    info(f"plan: +{len(creates)} create, ~{len(updates)} update, -{len(deletes)} delete")
    if dry_run:
        info("(dry-run — no changes)")
        return
    labels_apply(repo_id, creates, updates, deletes)


# --- Step 2: Milestones ---------------------------------------------

def create_milestones_step(client: GitHubClient, stages: dict, dry_run: bool) -> None:
    step("Creating GitHub Milestones from config/stages.yml")
    existing = {ms["title"]: ms for ms in client.list_milestones(state="all")}
    created = 0
    skipped = 0
    for stage_num, stage_data in (stages.get("stages") or {}).items():
        title = stage_data.get("title") or f"Stage {stage_num}"
        if title in existing:
            info(f"  [ok] {title} (already exists, #{existing[title]['number']})")
            skipped += 1
            continue
        desc = (stage_data.get("exit_criteria") or "").strip()
        if dry_run:
            info(f"  + would create: {title}")
        else:
            ms = client.create_milestone(title, description=desc)
            info(f"  + created: {title} (#{ms['number']})")
        created += 1
    info(f"summary: {created} new, {skipped} already existed")


# --- Step 3: Activate agent packs -----------------------------------

def activate_agent_packs(disc: dict, dry_run: bool) -> None:
    step("Activating discipline agent packs into .claude/agents/")
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    activated = 0
    skipped = 0
    missing = 0
    for d in (disc.get("disciplines") or []):
        if not d.get("active"):
            continue
        name = d["name"]
        # Each discipline's pack lives at agent-packs/<pack>/<agent>.md.
        # By convention, agent files have the same basename as the discipline.
        # Search all packs for matching basename.
        pack_files = list(PACKS_DIR.rglob(f"{name}.md"))
        if not pack_files:
            warn(f"no pack file found for discipline '{name}' "
                 f"(looked for agent-packs/*/{name}.md)")
            missing += 1
            continue
        # Prefer the first match (usually one pack contains the lead)
        src = pack_files[0]
        dst = AGENTS_DIR / f"{name}.md"
        if dst.exists():
            info(f"  [ok] {name}.md (already activated)")
            skipped += 1
            continue
        if dry_run:
            info(f"  + would copy {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
        else:
            shutil.copy2(src, dst)
            info(f"  + activated {name}.md from {src.parent.name} pack")
        activated += 1
    info(f"summary: {activated} activated, {skipped} already present, {missing} missing")


# --- Step 4: Seed sample Issues (optional) --------------------------

SAMPLE_UN_BODY = """**Acceptance:** The systems-first scaffolding works end-to-end on this repo.

**KPM:** NONE

**Stage:** 1

**Validated By:**
- inspection: `python scripts/init_project.py` completes without errors
- inspection: `python -m scripts.generate_docs` fills the AUTO sections in dev-docs/

*This is a starter Issue filed by `init_project.py --seed-sample`. Edit or close once your real UN-001 is filed.*
"""


def seed_sample_issues(client: GitHubClient, dry_run: bool) -> None:
    step("Seeding sample UN-001 Issue")
    existing = client.find_issue_by_title("[UN-001]")
    if existing:
        info(f"UN-001 already exists (#{existing['number']}) — skipping")
        return
    if dry_run:
        info("would file: [UN-001] Scaffolding works end-to-end")
        return
    issue = client.create_issue(
        "[UN-001] Scaffolding works end-to-end",
        SAMPLE_UN_BODY,
        ["type: user-need", "status: defined"],
    )
    info(f"filed UN-001 as #{issue['number']}")


# --- Step 5: Regen docs ---------------------------------------------

def run_generate_docs(dry_run: bool) -> None:
    step("Regenerating docs from current Issue state")
    if dry_run:
        info("would run: python -m scripts.generate_docs")
        return
    result = subprocess.run(
        [sys.executable, "-m", "scripts.generate_docs"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        warn(f"generate_docs failed (exit {result.returncode})")
        warn(result.stderr.strip().split("\n")[-1] if result.stderr else "(no stderr)")
        return
    for line in result.stdout.strip().split("\n"):
        info(line)


# --- Main -----------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="Show plan; make no changes.")
    ap.add_argument("--seed-sample", action="store_true",
                    help="File a starter UN-001 Issue to verify the chain works.")
    ap.add_argument("--skip-labels", action="store_true")
    ap.add_argument("--skip-milestones", action="store_true")
    ap.add_argument("--skip-agents", action="store_true")
    ap.add_argument("--skip-regen", action="store_true")
    ap.add_argument("--activate-profile", choices=["A", "B", "C"],
                    help="Overwrite config/disciplines.yml + config/stages.yml with "
                         "Profile A (Software), B (Mechanical/Hardware), or "
                         "C (Mixed-discipline IoT) before validating. Idempotent.")
    args = ap.parse_args()

    banner("Systems-First Template — Project Initializer")

    preloaded = None
    if args.activate_profile:
        preloaded = write_profile(args.activate_profile, args.dry_run)

    disc, stages = validate_configs(preloaded=preloaded)

    client = GitHubClient()
    step(f"GitHub repo: {client.owner}/{client.repo}")

    if not args.skip_labels:
        sync_labels_step(client, args.dry_run)
    else:
        info("(--skip-labels)")

    if not args.skip_milestones:
        create_milestones_step(client, stages, args.dry_run)
    else:
        info("(--skip-milestones)")

    if not args.skip_agents:
        activate_agent_packs(disc, args.dry_run)
    else:
        info("(--skip-agents)")

    if args.seed_sample:
        seed_sample_issues(client, args.dry_run)

    if not args.skip_regen:
        run_generate_docs(args.dry_run)
    else:
        info("(--skip-regen)")

    banner("Done" + (" (dry-run)" if args.dry_run else ""))
    if args.dry_run:
        print("Re-run without --dry-run to apply.")
        return
    print("Next steps:")
    print("  1. File your real UN-001 Issue via the New Issue UI")
    print("  2. Edit requirements/requirement-map.yml to link FRs/NFRs/IFs/KPMs")
    print("  3. Commit + push — workflows pick up from there")


if __name__ == "__main__":
    main()
