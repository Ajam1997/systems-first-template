# PHOTONFORGE Marketplace Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the `Ajam1997/PHOTONFORGE` marketplace repo (systems-first-core + 6 discipline packs + the `systems-first` pip package), release v0.1.0, and migrate `systems-first-template` and `photo-workflow` to consume it.

**Architecture:** One marketplace repo holds 7 process plugins and a pip package. The package absorbs the 10 machinery scripts (reconciling six files that diverged between the two repos) and exposes 9 `sf-*` console commands. Consuming repos delete their local copies and pin the package by git tag; agents install via the plugin marketplace.

**Tech Stack:** Python 3.11, setuptools, pytest, requests + PyYAML, Claude Code plugin manifests (plugin.json / marketplace.json), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-07-10-systems-first-marketplace-design.md` (same repo).

## Global Constraints

- All repos live under GitHub account `Ajam1997`; PHOTONFORGE / PHOTONFOUNDRY / kicad-pcba are **private** (already created 2026-07-10; PHOTONFOUNDRY and kicad-pcba are already populated — out of scope here).
- Package name `systems-first`, import name `systems_first`, `requires-python >= 3.11`, deps exactly `requests>=2.31`, `PyYAML>=6.0`.
- Console commands (spec §5): `sf-docs`, `sf-comment`, `sf-kpm-rollup`, `sf-pr-rollup`, `sf-wiki`, `sf-labels`, `sf-artifacts`, `sf-sysml`, `sf-init`.
- Agent names must stay exactly: `systemmaster`, `verification`, `validation`, `systems_lead`, `software_lead`, `electrical_lead`, `mechanical_lead`, `firmware_lead`, `manufacturing_lead`, `regulatory_lead`.
- PHOTONFORGE versions in lockstep: every plugin.json version == pyproject version == git tag (v0.1.0 for this release).
- `nightly-drift` (photo-workflow workflow + `scripts/check_drift.py`) is dead — delete, never migrate.
- photo-workflow keeps its local-only scripts: `check_doc_references.py`, `validate_generated_docs.py`, `doc_parser.py`, all shell/host scripts, and everything else not in the 10-file migration list. They are self-contained (verified: no imports of migrated modules).
- Local paths: template repo `F:\Files\50-59-software-and-dev\51-code-and-repos\PHOTONForge\systems-first-template`, photo-workflow `...\PHOTONForge\photo-workflow`, PHOTONFORGE clone target `...\PHOTONForge\PHOTONFORGE`.
- Windows shell: use Git Bash (`bash`) for the commands below; they are written for POSIX sh.

## Diverged-file reconciliation rule (used by Tasks 2–3)

The 10 migrated files exist in both repos; 6 diverged. Seed rule, per file:

| Module | Seed from | Why |
|---|---|---|
| `init_project.py`, `kpm_rollup.py`, `sync_labels.py`, `validate_artifacts.py` | either (identical) | byte-identical in both repos |
| `export_sysml.py`, `github_client.py` | **template** | template is ahead (SysML export, KPM-rollup client features) |
| `generate_docs.py`, `migrate_wiki.py`, `github_comment.py`, `pr_rollup.py` | **photo-workflow** | photo-workflow's copies are the live, CI-proven docs chain (doc-overhaul phases landed there only) |

After seeding, the executor MUST diff each diverged file against the non-seed copy and port any changes that are engine-generic (bug fixes, new subcommands, format changes). Changes that reference photo-workflow content (photography wording, PHOTON cartridge, specific FR/KPM lists) stay behind. Acceptance test for the docs chain is byte-identical photo-workflow regen (Task 10), so when in doubt on the docs chain, photo-workflow's behavior wins.

---

### Task 1: PHOTONFORGE clone + package skeleton

**Files:**
- Create: `PHOTONFORGE/packages/systems-first/pyproject.toml`
- Create: `PHOTONFORGE/packages/systems-first/src/systems_first/__init__.py`
- Create: `PHOTONFORGE/packages/systems-first/tests/test_smoke.py`
- Create: `PHOTONFORGE/.gitignore`

**Interfaces:**
- Produces: installable (empty) `systems-first` package; `systems_first.__version__ == "0.1.0"`; a venv at `PHOTONFORGE/.venv` used by all later tasks.

- [ ] **Step 1: Clone the empty repo**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge"
git clone https://github.com/Ajam1997/PHOTONFORGE.git PHOTONFORGE
cd PHOTONFORGE
git checkout -b main 2>/dev/null || true   # repo is empty; ensure branch name main
```

- [ ] **Step 2: Write the failing smoke test**

`packages/systems-first/tests/test_smoke.py`:

```python
"""Package-level smoke tests: version, importability of every module."""
import importlib

import systems_first

ALL_MODULES = [
    "systems_first.generate_docs",
    "systems_first.github_client",
    "systems_first.github_comment",
    "systems_first.kpm_rollup",
    "systems_first.pr_rollup",
    "systems_first.migrate_wiki",
    "systems_first.sync_labels",
    "systems_first.validate_artifacts",
    "systems_first.export_sysml",
    "systems_first.init_project",
]


def test_version():
    assert systems_first.__version__ == "0.1.0"


def test_all_modules_import():
    for name in ALL_MODULES:
        importlib.import_module(name)
```

- [ ] **Step 3: Write pyproject.toml and package init**

`packages/systems-first/pyproject.toml` (console scripts included now; the modules arrive in Tasks 2–3):

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "systems-first"
version = "0.1.0"
description = "Systems-first process machinery: Issues-as-truth doc generation, KPM rollup, requirement write-back, SysML export"
requires-python = ">=3.11"
dependencies = ["requests>=2.31", "PyYAML>=6.0"]

[project.scripts]
sf-docs = "systems_first.generate_docs:main"
sf-comment = "systems_first.github_comment:main"
sf-kpm-rollup = "systems_first.kpm_rollup:main"
sf-pr-rollup = "systems_first.pr_rollup:main"
sf-wiki = "systems_first.migrate_wiki:main"
sf-labels = "systems_first.sync_labels:main"
sf-artifacts = "systems_first.validate_artifacts:main"
sf-sysml = "systems_first.export_sysml:main"
sf-init = "systems_first.init_project:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`packages/systems-first/src/systems_first/__init__.py`:

```python
"""systems-first: process machinery for systems-first projects."""
__version__ = "0.1.0"
```

`/.gitignore` (repo root):

```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
build/
```

- [ ] **Step 4: Create venv, install editable, run the test — expect partial fail**

```bash
cd packages/systems-first
uv venv ../../.venv --python 3.11
source ../../.venv/Scripts/activate
uv pip install -e . pytest
pytest tests/test_smoke.py -v
```

Expected: `test_version` PASS, `test_all_modules_import` FAIL (`ModuleNotFoundError: systems_first.generate_docs`) — the red state Tasks 2–3 turn green.

- [ ] **Step 5: Commit**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add -A
git commit -m "feat(package): systems-first package skeleton, v0.1.0, sf-* entry points declared"
```

---

### Task 2: Migrate the template-seeded and identical modules

**Files:**
- Create: `PHOTONFORGE/packages/systems-first/src/systems_first/{github_client,export_sysml,init_project,kpm_rollup,sync_labels,validate_artifacts}.py` (copied then edited)

**Interfaces:**
- Consumes: template repo `scripts/*.py` (seed copies), photo-workflow `scripts/github_client.py` + `scripts/export_sysml.py` (delta sources).
- Produces: `systems_first.github_client.GitHubClient` importable by Task 3's modules; 4 CLI mains (`kpm_rollup`, `sync_labels`, `validate_artifacts`, `export_sysml`, `init_project` — each already defines `main()`).

- [ ] **Step 1: Copy seeds and rewrite imports**

```bash
T="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/systems-first-template/scripts"
DST="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE/packages/systems-first/src/systems_first"
for f in github_client export_sysml init_project kpm_rollup sync_labels validate_artifacts; do
  cp "$T/$f.py" "$DST/$f.py"
done
sed -i 's/from scripts\./from systems_first./g; s/import scripts\./import systems_first./g' "$DST"/*.py
grep -rn "scripts\." "$DST" && echo "LEFTOVER scripts. references — fix manually" || echo "clean"
```

- [ ] **Step 2: Port photo-workflow deltas for the two diverged files**

```bash
P="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/photo-workflow/scripts"
git diff --no-index "$T/github_client.py" "$P/github_client.py" > /tmp/ghc.diff || true
git diff --no-index "$T/export_sysml.py"  "$P/export_sysml.py"  > /tmp/sysml.diff || true
```

Read both diffs. Port photo-workflow-side changes that are engine-generic (per the reconciliation rule at the top of this plan) into the copies in `$DST`, adapting import lines to `systems_first.`. Do NOT port photo-workflow-specific content. Record every ported / skipped hunk in the commit message body.

- [ ] **Step 3: Run smoke test — imports for these six must pass**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE/packages/systems-first"
source ../../.venv/Scripts/activate
python -c "import systems_first.github_client, systems_first.export_sysml, systems_first.init_project, systems_first.kpm_rollup, systems_first.sync_labels, systems_first.validate_artifacts; print('ok')"
```

Expected: `ok`. (`pytest tests/test_smoke.py` still fails on the four Task-3 modules — correct.)

- [ ] **Step 4: Commit**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add -A
git commit -m "feat(package): migrate github_client, export_sysml + 4 identical modules

Seeded from systems-first-template; photo-workflow deltas ported:
<list ported hunks>; skipped as project-specific: <list>"
```

---

### Task 3: Migrate the docs-chain modules (photo-workflow seeds)

**Files:**
- Create: `PHOTONFORGE/packages/systems-first/src/systems_first/{generate_docs,migrate_wiki,github_comment,pr_rollup}.py`

**Interfaces:**
- Consumes: `systems_first.github_client.GitHubClient` (Task 2).
- Produces: `main()` in each module (entry points already declared in Task 1's pyproject).

- [ ] **Step 1: Copy photo-workflow seeds and rewrite imports**

```bash
P="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/photo-workflow/scripts"
DST="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE/packages/systems-first/src/systems_first"
for f in generate_docs migrate_wiki github_comment pr_rollup; do
  cp "$P/$f.py" "$DST/$f.py"
done
sed -i 's/from scripts\./from systems_first./g; s/import scripts\./import systems_first./g' "$DST"/*.py
grep -rn "scripts\." "$DST" && echo "LEFTOVER — fix manually" || echo "clean"
```

- [ ] **Step 2: Port template-side deltas**

```bash
T="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/systems-first-template/scripts"
for f in generate_docs migrate_wiki github_comment pr_rollup; do
  git diff --no-index "$P/$f.py" "$T/$f.py" > "/tmp/$f.diff" || true
done
```

Read each diff; port template-side engine-generic changes (e.g. features added for kpm-rollup/SysML workflows). photo-workflow behavior wins any conflict on these four (Task 10's byte-identical regen depends on it). Record ported / skipped hunks in the commit message.

- [ ] **Step 3: Full smoke test passes**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE/packages/systems-first"
source ../../.venv/Scripts/activate
pytest tests/test_smoke.py -v
```

Expected: 2/2 PASS.

- [ ] **Step 4: Commit**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add -A
git commit -m "feat(package): migrate docs chain (generate_docs, migrate_wiki, github_comment, pr_rollup)

Seeded from photo-workflow (live CI versions); template deltas ported:
<list>; skipped: <list>"
```

---

### Task 4: Console-command smoke tests

**Files:**
- Create: `PHOTONFORGE/packages/systems-first/tests/test_cli_smoke.py`

**Interfaces:**
- Consumes: the 9 entry points from pyproject (Task 1) + modules (Tasks 2–3).
- Produces: proof every `sf-*` command launches.

- [ ] **Step 1: Write the test**

```python
"""Every console command must launch. --help must not crash.

Exit code 0 = argparse help; 2 = argparse usage error (acceptable: the
command parsed argv and responded). Anything else = broken entry point.
"""
import subprocess
import sys

import pytest

COMMANDS = [
    "systems_first.generate_docs",
    "systems_first.github_comment",
    "systems_first.kpm_rollup",
    "systems_first.pr_rollup",
    "systems_first.migrate_wiki",
    "systems_first.sync_labels",
    "systems_first.validate_artifacts",
    "systems_first.export_sysml",
    "systems_first.init_project",
]


@pytest.mark.parametrize("mod", COMMANDS)
def test_cli_help(mod):
    proc = subprocess.run(
        [sys.executable, "-m", mod, "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode in (0, 2), (
        f"{mod} --help exited {proc.returncode}\n"
        f"stdout: {proc.stdout[:500]}\nstderr: {proc.stderr[:500]}"
    )
```

- [ ] **Step 2: Run — fix any module that crashes on --help**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE/packages/systems-first"
source ../../.venv/Scripts/activate
pytest tests/ -v
```

Expected: all PASS. If a module exits nonzero because it hits the network / requires `GITHUB_TOKEN` before parsing argv, refactor **only** its `main()` so argument parsing happens before client construction (do not change behavior otherwise), then re-run.

- [ ] **Step 3: Verify the installed console scripts themselves**

```bash
uv pip install -e . --force-reinstall
sf-docs --help >/dev/null 2>&1; echo "sf-docs: $?"
sf-comment --help >/dev/null 2>&1; echo "sf-comment: $?"
sf-init --help >/dev/null 2>&1; echo "sf-init: $?"
```

Expected: each prints `0` (or `2`), never a traceback.

- [ ] **Step 4: Commit**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add -A
git commit -m "test(package): CLI smoke tests for all nine sf-* commands"
```

---

### Task 5: Marketplace-repo CI

**Files:**
- Create: `PHOTONFORGE/.github/workflows/ci.yml`

**Interfaces:**
- Consumes: package + tests from Tasks 1–4.
- Produces: green CI on every push/PR; JSON-manifest validation for Tasks 6–8.

- [ ] **Step 1: Write the workflow**

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package + pytest
        run: pip install -e packages/systems-first pytest
      - name: Package tests
        run: pytest packages/systems-first/tests -v

  manifests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate all plugin/marketplace JSON parses
        run: |
          python - <<'EOF'
          import json, pathlib, sys
          bad = []
          for p in pathlib.Path(".").rglob("*.json"):
              if ".venv" in p.parts: continue
              try: json.loads(p.read_text(encoding="utf-8"))
              except Exception as e: bad.append(f"{p}: {e}")
          if bad: sys.exit("\n".join(bad))
          print("all JSON manifests parse")
          EOF
```

- [ ] **Step 2: Push and verify CI runs green**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add -A && git commit -m "ci: package tests + manifest validation"
git push -u origin main
export GH_CONFIG_DIR="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/gh-config"
"/c/Program Files/GitHub CLI/gh.exe" run watch --repo Ajam1997/PHOTONFORGE --exit-status || "/c/Program Files/GitHub CLI/gh.exe" run list --repo Ajam1997/PHOTONFORGE --limit 3
```

Expected: both jobs green.

---

### Task 6: systems-first-core plugin (agents + two skills)

**Files:**
- Create: `PHOTONFORGE/plugins/core/.claude-plugin/plugin.json`
- Create: `PHOTONFORGE/plugins/core/agents/{systemmaster,verification,validation,systems_lead}.md` (copied from template)
- Create: `PHOTONFORGE/plugins/core/skills/start-work/SKILL.md` + `references/checklist.md`
- Create: `PHOTONFORGE/plugins/core/skills/write-back/SKILL.md`

**Interfaces:**
- Consumes: template `.claude/agents/*.md`, `.claude/agent-packs/software/systems_lead.md`, `dev-docs/start-work-checklist.md`; `sf-comment` CLI (Task 3).
- Produces: plugin `systems-first-core@0.1.0` with agents named exactly `systemmaster`, `verification`, `validation`, `systems_lead` and skills `start-work`, `write-back`.

- [ ] **Step 1: plugin.json**

```json
{
  "name": "systems-first-core",
  "version": "0.1.0",
  "description": "Systems-first process core: systemmaster, verification, validation, systems_lead agents + session-start and write-back skills. Pair with a discipline pack (systems-first-software, -electrical, ...) and the systems-first pip package.",
  "author": { "name": "Alex" },
  "keywords": ["systems-engineering", "requirements", "verification", "validation", "kpm"],
  "license": "MIT"
}
```

- [ ] **Step 2: Copy the four agents; update script references**

```bash
T="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/systems-first-template"
CORE="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE/plugins/core"
mkdir -p "$CORE/agents"
cp "$T/.claude/agents/systemmaster.md" "$T/.claude/agents/verification.md" "$T/.claude/agents/validation.md" "$CORE/agents/"
cp "$T/.claude/agent-packs/software/systems_lead.md" "$CORE/agents/"
grep -rn "scripts/github_comment.py\|scripts\.\|python -m scripts" "$CORE/agents"
```

For every hit from that grep, rewrite the reference to the console command (e.g. `scripts/github_comment.py` → `sf-comment`, `python -m scripts.kpm_rollup` → `sf-kpm-rollup`). Keep frontmatter fields (`name`, `tools`, `model`, `memory`, `color`) untouched.

- [ ] **Step 3: start-work skill**

Copy the template's checklist as the reference file, then write the router:

```bash
mkdir -p "$CORE/skills/start-work/references"
cp "$T/dev-docs/start-work-checklist.md" "$CORE/skills/start-work/references/checklist.md"
```

`skills/start-work/SKILL.md`:

```markdown
---
name: start-work
description: Use at the start of every working session in a systems-first project - selects the right agent and skill from computed repo state before the first invocation. Trigger on session start, "where were we", "what should I work on", or resuming mid-flight work.
---

# Start Work

Derive the session's starting point from OBJECTIVE state, not memory or
narrative logs. The failing checks ARE the to-do list.

## 1. Compute state (run all, in parallel where possible)

```bash
git status -sb && git log --oneline -5
gh issue list --label in-progress --limit 10
gh run list --limit 3          # CI health
sf-kpm-rollup --check 2>/dev/null || true   # KPM margins (needs GITHUB_TOKEN)
```

## 2. Classify the session and route

Read `references/checklist.md` and follow it: it maps the situation
(new idea / plan exists / implementing / resuming / debugging / claiming
done / cross-cutting review) to the agent and superpowers skill to start
with, and covers worktree isolation and parallel-dispatch decisions.

## 3. Trust computed state over the log

If an Issue comment's `**Next action:**` line disagrees with what the
commands in step 1 show, the commands win - re-verify before acting.
```

- [ ] **Step 4: write-back skill**

`skills/write-back/SKILL.md`:

```markdown
---
name: write-back
description: Use whenever an agent must record verification, validation, KPM, or regression evidence against a requirement Issue in a systems-first project - posts structured comments via sf-comment. Trigger after tests pass/fail against an FR, after a KPM benchmark, or after milestone E2E validation.
---

# Agent Write-back Protocol

**Canonical source of truth: GitHub Issues.** Docs are render targets.
Never edit AUTO-managed files by hand; never move status labels (that is
`sf-pr-rollup`'s job on PR merge). Never call the GitHub API directly -
always go through `sf-comment` (reads `GITHUB_TOKEN` from the environment;
requirement IDs like FR-X.Y / UN-XXX / KPM-X.Y resolve live via Issue
search).

## Commands

```bash
# verification: test pass
sf-comment verify-fr FR-1.2 "pytest: 5/5 passed, 1.8s avg" \
  --next-action "merge ready; @software_lead to open PR"
# verification: regression
sf-comment regress-fr FR-1.2 "test_sharpness failed: expected 0.85 got 0.72" \
  --next-action "@software_lead revisit blur kernel threshold"
# verification: KPM benchmark
sf-comment update-kpm KPM-1.2 "1.8s on target hardware - 2026-07-10" passing \
  --next-action "no action; KPM inside budget"
# validation: E2E pass
sf-comment validate-un UN-010 "all 3 scenarios passed" \
  --next-action "stage closes; ready for next stage"
# validation: E2E failure
sf-comment validation-failure UN-010 "wrong clusters on burst shots" \
  --next-action "@systems_lead to reassess FR-1.1 threshold"
```

## Hard rules

1. Every comment ends with a `**Next action:** ...` line (enables
   resume-mid-flight).
2. Every comment carries a `via: @<agent>` footer so the writer's origin
   is legible to the next reader.
3. Post measurements and evidence only - status labels move on PR merge.
```

- [ ] **Step 5: Commit**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add -A
git commit -m "feat(core): systems-first-core plugin - 4 agents + start-work/write-back skills"
```

---

### Task 7: Six thin discipline packs

**Files:**
- Create: `PHOTONFORGE/plugins/{software,electrical,mechanical,firmware,manufacturing,regulatory}/.claude-plugin/plugin.json`
- Create: `PHOTONFORGE/plugins/<d>/agents/<d>_lead.md` for each

**Interfaces:**
- Consumes: template `.claude/agent-packs/<d>/<d>_lead.md`.
- Produces: plugins `systems-first-<d>@0.1.0`, each shipping exactly one lead agent.

- [ ] **Step 1: Copy the leads and stamp manifests**

```bash
T="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/systems-first-template"
PF="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
for d in software electrical mechanical firmware manufacturing regulatory; do
  mkdir -p "$PF/plugins/$d/.claude-plugin" "$PF/plugins/$d/agents"
  cp "$T/.claude/agent-packs/$d/${d}_lead.md" "$PF/plugins/$d/agents/"
  cat > "$PF/plugins/$d/.claude-plugin/plugin.json" <<EOF
{
  "name": "systems-first-$d",
  "version": "0.1.0",
  "description": "Systems-first $d discipline pack: the ${d}_lead agent. Requires systems-first-core.",
  "author": { "name": "Alex" },
  "license": "MIT"
}
EOF
done
grep -rn "scripts/github_comment.py\|python -m scripts" "$PF/plugins/"*/agents/ || echo clean
```

Rewrite any grep hits to `sf-*` commands, as in Task 6 Step 2. Note: `systems_lead.md` is NOT copied into the software pack — it moved to core (spec §3).

- [ ] **Step 2: Wire the electrical pack to kicad-pcba**

Append to `plugins/electrical/agents/electrical_lead.md` (after the existing body, before any closing notes):

```markdown
## Tool pairing: kicad-pcba

For PCB/PCBA implementation work, use the `kicad-pcba` plugin
(install: `claude plugin marketplace add Ajam1997/PHOTONFOUNDRY`, then
`claude plugin install kicad-pcba@photonfoundry`). Its skill sequence
(pcb-spec -> pcb-schematic -> pcb-libraries -> pcb-layout -> pcba-parts ->
pcb-production) maps onto this project's stage gates, and its machine-
checked `docs/gates.json` output is this discipline's verification-evidence
source: cite gate results in `sf-comment verify-fr` / `update-kpm` posts
rather than re-asserting them.
```

- [ ] **Step 3: Commit**

```bash
cd "$PF"
git add -A
git commit -m "feat(packs): six thin discipline packs; electrical pack wired to kicad-pcba"
```

---

### Task 8: Marketplace manifest, README, release v0.1.0

**Files:**
- Create: `PHOTONFORGE/.claude-plugin/marketplace.json`
- Create: `PHOTONFORGE/README.md`

**Interfaces:**
- Consumes: all 7 plugins (Tasks 6–7), package (Tasks 1–4).
- Produces: installable marketplace `photonforge`; git tag `v0.1.0` (the pin every consumer uses).

- [ ] **Step 1: marketplace.json**

```json
{
  "name": "photonforge",
  "owner": { "name": "Alex", "url": "https://github.com/Ajam1997" },
  "metadata": {
    "description": "Process plugin marketplace for systems-first project development. Tool plugins live in the sibling PHOTONFOUNDRY marketplace.",
    "version": "0.1.0"
  },
  "plugins": [
    { "name": "systems-first-core",          "source": "./plugins/core",          "description": "systemmaster, verification, validation, systems_lead + start-work/write-back skills" },
    { "name": "systems-first-software",      "source": "./plugins/software",      "description": "software_lead discipline pack" },
    { "name": "systems-first-electrical",    "source": "./plugins/electrical",    "description": "electrical_lead discipline pack (pairs with kicad-pcba from PHOTONFOUNDRY)" },
    { "name": "systems-first-mechanical",    "source": "./plugins/mechanical",    "description": "mechanical_lead discipline pack" },
    { "name": "systems-first-firmware",      "source": "./plugins/firmware",      "description": "firmware_lead discipline pack" },
    { "name": "systems-first-manufacturing", "source": "./plugins/manufacturing", "description": "manufacturing_lead discipline pack" },
    { "name": "systems-first-regulatory",    "source": "./plugins/regulatory",    "description": "regulatory_lead discipline pack" }
  ]
}
```

- [ ] **Step 2: README.md**

```markdown
# PHOTONFORGE

**Process plugin marketplace for systems-first project development** — the
"how projects are run" layer. Granular design toolkits (kicad-pcba, ...)
live in the sibling tool marketplace,
[PHOTONFOUNDRY](https://github.com/Ajam1997/PHOTONFOUNDRY).

## What ships here

| Piece | What it is |
|---|---|
| `systems-first-core` plugin | systemmaster, verification, validation, systems_lead agents + start-work / write-back skills |
| `systems-first-<discipline>` plugins | one thin pack per discipline (software, electrical, mechanical, firmware, manufacturing, regulatory) — each ships its lead agent |
| `packages/systems-first` | pip package with the machinery CLIs: sf-docs, sf-comment, sf-kpm-rollup, sf-pr-rollup, sf-wiki, sf-labels, sf-artifacts, sf-sysml, sf-init |

Everything in this repo versions in lockstep: one `vX.Y.Z` tag = one
coherent release of all plugins + the package.

## Install (per project)

```bash
claude plugin marketplace add Ajam1997/PHOTONFORGE
claude plugin install systems-first-core@photonforge
claude plugin install systems-first-software@photonforge   # + packs for your disciplines
pip install "systems-first @ git+https://github.com/Ajam1997/PHOTONFORGE@v0.1.0#subdirectory=packages/systems-first"
```

New project? Start from the
[systems-first-template](https://github.com/Ajam1997/systems-first-template),
which walks through this setup and scaffolds requirements/, dev-docs/, and CI.

## Upgrading a project

Bump the tag in the project's CI `pip install` line(s) and reinstall the
plugins. Read the release notes for the tag before bumping — doc formats
regenerate on the new version's rules.
```

- [ ] **Step 3: Local install verification**

```bash
claude plugin marketplace add "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
claude plugin install systems-first-core@photonforge
claude plugin install systems-first-software@photonforge
claude plugin list
```

Expected: both plugins listed. Then in any Claude Code session: the agent list shows `systemmaster`, `verification`, `validation`, `systems_lead`, `software_lead`, and skills `start-work` / `write-back` are invocable. (Spec acceptance criterion 2.)

- [ ] **Step 4: Commit, tag, push**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add -A
git commit -m "feat: marketplace manifest + README — PHOTONFORGE v0.1.0"
git tag v0.1.0
git push origin main v0.1.0
```

---

### Task 9: HUMAN STEP — CI read token for the private package

GitHub Actions' default `github.token` cannot read a *different* private
repo, so template and photo-workflow CI cannot `pip install` from private
PHOTONFORGE without a credential. **Alex must:**

1. Create a fine-grained PAT: github.com → Settings → Developer settings →
   Fine-grained tokens → scope it to **only** the `PHOTONFORGE` repo,
   permission **Contents: Read-only**, expiry 1 year.
2. Add it as an Actions secret named `PHOTONFORGE_READ_TOKEN` on **both**
   `Ajam1997/systems-first-template` and `Ajam1997/PHOTONFORGE_Photo-Workflow`
   (repo → Settings → Secrets and variables → Actions).

- [ ] Confirm with Alex that both secrets exist before starting Task 10/11.
  (Prompt-and-wait; agents cannot and must not create credentials.
  Alternative that removes this step entirely: flip PHOTONFORGE public.)

The pip line used in CI from here on (note the token in the URL):

```yaml
run: pip install "systems-first @ git+https://x-access-token:${{ secrets.PHOTONFORGE_READ_TOKEN }}@github.com/Ajam1997/PHOTONFORGE@v0.1.0#subdirectory=packages/systems-first"
```

---

### Task 10: Migrate photo-workflow (pilot + acceptance test)

**Files:**
- Delete: `photo-workflow/scripts/{generate_docs,github_client,github_comment,kpm_rollup,pr_rollup,migrate_wiki,sync_labels,validate_artifacts,export_sysml,init_project,check_drift}.py`
- Delete: `photo-workflow/.github/workflows/nightly-drift.yml`
- Delete: `photo-workflow/.claude/agents/{software_lead,systemmaster,systems_lead,validation,verification}.md`
- Modify: `photo-workflow/.github/workflows/{regen-docs,wiki-publish,pr-close-issues}.yml`
- Modify: `photo-workflow/CLAUDE.md`

**Interfaces:**
- Consumes: package v0.1.0 (Task 8), `PHOTONFORGE_READ_TOKEN` secret (Task 9).
- Produces: photo-workflow running entirely on the plugin + package. Spec acceptance criteria 3 and 4.

- [ ] **Step 1: Branch + BEFORE snapshot of generated docs (byte-identical baseline)**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/photo-workflow"
git checkout main && git pull && git checkout -b feat/photonforge-migration
export GH_CONFIG_DIR="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/gh-config"
export GITHUB_TOKEN=$("/c/Program Files/GitHub CLI/gh.exe" auth token)
.venv/Scripts/python.exe -m scripts.generate_docs
cp -r dev-docs /tmp/devdocs-BEFORE
git checkout -- dev-docs   # restore; snapshot lives in /tmp
```

- [ ] **Step 2: Install the package into the project venv, AFTER snapshot, diff**

```bash
.venv/Scripts/python.exe -m pip install "systems-first @ git+https://github.com/Ajam1997/PHOTONFORGE@v0.1.0#subdirectory=packages/systems-first"
.venv/Scripts/sf-docs
cp -r dev-docs /tmp/devdocs-AFTER
git checkout -- dev-docs
diff -r /tmp/devdocs-BEFORE /tmp/devdocs-AFTER && echo "BYTE-IDENTICAL ✓"
```

Expected: `BYTE-IDENTICAL ✓` (spec acceptance criterion 3). Any diff = a
reconciliation bug in Task 3 — fix in PHOTONFORGE, re-tag (`v0.1.0` may be
moved with `git tag -f` ONLY while nothing else consumes it), reinstall,
re-diff. Do not proceed until identical.

- [ ] **Step 3: Delete migrated scripts + dead drift machinery + local agents**

```bash
git rm scripts/{generate_docs,github_client,github_comment,kpm_rollup,pr_rollup,migrate_wiki,sync_labels,validate_artifacts,export_sysml,init_project,check_drift}.py
git rm .github/workflows/nightly-drift.yml
git rm .claude/agents/software_lead.md .claude/agents/systemmaster.md .claude/agents/systems_lead.md .claude/agents/validation.md .claude/agents/verification.md
grep -rn "scripts\.\(generate_docs\|github_client\|github_comment\|kpm_rollup\|pr_rollup\|migrate_wiki\|sync_labels\|validate_artifacts\|export_sysml\|init_project\|check_drift\)" --include="*.py" --include="*.yml" . | grep -v ".venv"
```

The grep enumerates every remaining reference; the next two steps must clear them all. (`check_doc_references.py`, `validate_generated_docs.py`, `doc_parser.py` and all shell scripts stay.)

- [ ] **Step 4: Repoint the three workflows**

In `.github/workflows/regen-docs.yml`: replace

```yaml
      - name: Install dependencies
        run: pip install requests PyYAML
```

with

```yaml
      - name: Install systems-first package
        run: pip install "systems-first @ git+https://x-access-token:${{ secrets.PHOTONFORGE_READ_TOKEN }}@github.com/Ajam1997/PHOTONFORGE@v0.1.0#subdirectory=packages/systems-first"
```

and `run: python -m scripts.generate_docs` → `run: sf-docs`.
(`python -m scripts.validate_generated_docs` stays — local script.)

In `.github/workflows/pr-close-issues.yml`: add the same Install step
before the run step, and `python -m scripts.pr_rollup` → `sf-pr-rollup`.

In `.github/workflows/wiki-publish.yml`: add the same Install step;
`python scripts/migrate_wiki.py --push` → `sf-wiki --push`; and update the
`paths:` trigger entry `- "scripts/migrate_wiki.py"` to
`- ".github/workflows/wiki-publish.yml"` (the script no longer exists in
this repo).

- [ ] **Step 5: Update CLAUDE.md**

- Roster preamble: add one line — `Agents ship via the PHOTONFORGE marketplace (systems-first-core + systems-first-software plugins); local .claude/agents/ copies were removed 2026-07.`
- Agent Write-back Protocol section: `scripts/github_comment.py` → `sf-comment`; every example `python scripts/github_comment.py <sub> ...` → `sf-comment <sub> ...`.
- Project Layout: scripts/ line — remove doc-automation names, note `doc machinery now in the systems-first package (sf-* CLIs)`; workflows line — drop `nightly-drift`.

- [ ] **Step 6: Install plugins for the project + verify**

```bash
claude plugin marketplace add Ajam1997/PHOTONFORGE
claude plugin install systems-first-core@photonforge
claude plugin install systems-first-software@photonforge
```

Then start a Claude Code session in photo-workflow: agent list must show all five roster agents (from plugins now); `start-work` and `write-back` skills invocable.

- [ ] **Step 7: Commit, push, PR; watch CI**

```bash
git add -A
git commit -m "feat: migrate to PHOTONFORGE plugins + systems-first package v0.1.0

- delete 10 migrated machinery scripts + dead nightly-drift/check_drift
- workflows install systems-first@v0.1.0, call sf-docs/sf-pr-rollup/sf-wiki
- local .claude/agents removed; agents ship via systems-first-core/-software
- CLAUDE.md: write-back protocol now via sf-comment

Docs impact: CLAUDE.md updated; dev-docs regen verified byte-identical pre/post"
git push -u origin feat/photonforge-migration
"/c/Program Files/GitHub CLI/gh.exe" pr create --fill --repo Ajam1997/PHOTONFORGE_Photo-Workflow
```

Expected: docs-integrity + tests workflows green on the PR (acceptance criterion 4). After merge: regen-docs and wiki-publish runs green on main.

---

### Task 11: Migrate systems-first-template

**Files:**
- Delete: `systems-first-template/.claude/agents/`, `.claude/agent-packs/`, the 10 `scripts/*.py`
- Modify: `.github/workflows/{kpm-rollup,pr-close-issues,regen-docs,sysml-export,validate-artifacts,wiki-publish}.yml`
- Modify: `README.md`, `dev-docs/getting-started.md`, `scripts/README.md`

**Interfaces:**
- Consumes: package v0.1.0 + plugins (Task 8), `PHOTONFORGE_READ_TOKEN` secret (Task 9).
- Produces: the template scaffolding-only; setup docs point at the marketplace.

- [ ] **Step 1: Branch and delete**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/systems-first-template"
git checkout main && git pull && git checkout -b feat/photonforge-migration
git rm -r .claude/agents .claude/agent-packs
git rm scripts/{generate_docs,github_client,github_comment,kpm_rollup,pr_rollup,migrate_wiki,sync_labels,validate_artifacts,export_sysml,init_project}.py
grep -rn "python -m scripts\.\|scripts/[a-z_]*\.py\|agent-packs" --include="*.yml" --include="*.md" . | grep -v docs/superpowers | head -40
```

The grep lists every doc/workflow reference to clean in the next steps.

- [ ] **Step 2: Repoint all six workflows**

In each of `kpm-rollup.yml`, `pr-close-issues.yml`, `regen-docs.yml`,
`sysml-export.yml`, `validate-artifacts.yml`, `wiki-publish.yml`: insert
after the `actions/setup-python` step —

```yaml
      - name: Install systems-first package
        run: pip install "systems-first @ git+https://x-access-token:${{ secrets.PHOTONFORGE_READ_TOKEN }}@github.com/Ajam1997/PHOTONFORGE@v0.1.0#subdirectory=packages/systems-first"
```

(replacing any existing `pip install requests PyYAML`-style step), and map
the run lines: `python -m scripts.kpm_rollup` → `sf-kpm-rollup`,
`python -m scripts.pr_rollup` → `sf-pr-rollup`, `python -m scripts.generate_docs`
→ `sf-docs`, export_sysml invocation → `sf-sysml`, validate_artifacts
invocation → `sf-artifacts`, migrate_wiki invocation → `sf-wiki` (preserve
each line's existing flags verbatim). Also update any `paths:` triggers
naming deleted scripts to name the workflow file itself instead.

- [ ] **Step 3: Update setup docs**

- `README.md`: replace agent-harness bullets that describe `.claude/agents`
  + `agent-packs` with the marketplace flow (the four `claude plugin` /
  `pip install` lines from Task 8's README Install section, plus: "add
  `Ajam1997/PHOTONFOUNDRY` for design toolkits like kicad-pcba"), and
  update the Status paragraph to mention the plugin split.
- `dev-docs/getting-started.md` and `scripts/README.md`: same substitution
  wherever local agents/scripts are referenced; scripts/README.md now
  documents only what remains in `scripts/`.

- [ ] **Step 4: Commit, push, PR; verify CI**

```bash
git add -A
git commit -m "feat: consume PHOTONFORGE marketplace + systems-first package v0.1.0

- agents + agent-packs + 10 machinery scripts move to Ajam1997/PHOTONFORGE
- 6 workflows install the package and call sf-* CLIs
- setup docs: marketplace install flow"
git push -u origin feat/photonforge-migration
"/c/Program Files/GitHub CLI/gh.exe" pr create --fill --repo Ajam1997/systems-first-template
```

Expected: CI green. After merge, trigger `regen-docs` via workflow_dispatch and confirm a green run (acceptance criterion 1 & 4 equivalents for the template).

---

## Acceptance checklist (mirrors spec §10)

- [ ] 1. Package tests green in PHOTONFORGE CI (Task 5).
- [ ] 2. core + software install from the marketplace; all agents resolve; both skills invoke (Task 8 Step 3, Task 10 Step 6).
- [ ] 3. photo-workflow `dev-docs/` regen byte-identical pre/post migration (Task 10 Step 2).
- [ ] 4. photo-workflow CI green with zero references to deleted scripts (Task 10 Step 7).
