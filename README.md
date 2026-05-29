# Systems-First Template

A GitHub template for **systems-engineering-first project development**, usable
across software, electrical, mechanical, firmware, and mixed-discipline
projects. Built on top of GitHub Issues + Milestones + a Claude Code agent
harness. SysML-flavored without leaving GitHub.

> **Status:** structurally complete (Passes 1–3 landed). 7 discipline-lead
> agent packs ship (systems, software, mechanical, electrical, firmware,
> manufacturing, regulatory). Roadmap → Pass 4: `critical_path` aggregation
> in `kpm_rollup`, per-discipline example manifests beyond mechanical, and
> pilot validation on a real project.

---

## What this is

A working scaffold for a project that wants:

- **Requirements as data** — user needs, functional requirements,
  non-functional requirements, interface requirements, KPMs (including
  computed/rolled-up KPMs that subsume the "budgets" concept) — all
  live as GitHub Issues with structured bodies and decomposition links
  in `requirements/requirement-map.yml`.
- **A single source of truth, three render targets** — Issues are
  canonical. `generate_docs.py` regenerates `dev-docs/`. `migrate_wiki.py`
  publishes to the GitHub Wiki. `export_sysml.py` produces a SysMLv2
  `.sysml` file for Eclipse Syson / Cameo / any conformant tool. Hand
  edits to AUTO sections lose.
- **Verification & Validation traceability** — every requirement carries
  an explicit list of evidence sources (test, simulation, bench,
  inspection, review) in its Issue body. A V&V matrix table renders
  automatically and shows the coverage gap.
- **V-model KPM rollup** — KPMs sit at every level of the decomposition,
  not just at user-need level. `scripts/kpm_rollup.py` aggregates child
  measurements into parent values (sum / max / min), flags margin
  erosion, replaces the older "budget" concept.
- **Stage-gated delivery via GitHub Milestones** — one milestone per
  phase. Closes automatically when its user-needs roll up to verified.
- **SysML-style diagrams** — Mermaid-based state machines, activity
  diagrams, block-definition diagrams in `dev-docs/architecture/`.
  Renders natively in GitHub and the wiki.
- **Non-text artifact manifests** — `artifacts/<discipline>/<name>.md`
  carries a reference + SHA-256 + snapshot PNG for CAD assemblies,
  schematics, firmware binaries, anything else that doesn't diff in
  git. Spec: `dev-docs/architecture/artifact-manifest.md`. Validator:
  `scripts/validate_artifacts.py`.
- **A Claude Code agent harness** — declarative discipline leads
  (`systems_lead`, `software_lead`, `mechanical_lead`,
  `electrical_lead`, `firmware_lead`, `manufacturing_lead`,
  `regulatory_lead`), plus universal `verification`, `validation`,
  and `systemmaster` agents. Mix and match per project via
  `config/disciplines.yml` or `init_project.py --activate-profile`.

## Who this is for

You, if:

- You're designing a *system* (not just shipping code) — something with
  multiple disciplines, interfaces, and verification phases.
- You want the rigor of MBSE/SysML without paying for Cameo or Capella.
- You want to use Claude Code as an iterative drafting partner that does
  more than autocomplete — that maintains your requirements tree, V&V
  matrix, and architecture diagrams as you go.
- You're a solo engineer or small team where ceremony has to earn its
  keep, but architectural discipline still matters.

## What this is not

- Not a CAD tool, schematic editor, or simulator. Those keep their own
  files; this template tracks the *requirements*, *interfaces*, *V&V*,
  and *architecture* of whatever you build with them.
- Not a heavyweight modeling environment. If you need SysMLv2 with
  formal semantics, look at Cameo or Capella. This trades formal rigor
  for ergonomics and zero tooling install.
- Pass 1 (software), Pass 2 (mechanical + artifact manifest format),
  and Pass 3 (electrical, firmware, manufacturing, regulatory agent
  packs) are landed. Pass 4 plans `critical_path` aggregation in
  `kpm_rollup` for end-to-end-latency-style KPMs and discipline-pack
  example manifests beyond mechanical.

## Origin

Extracted from [PHOTONForge](https://github.com/Ajam1997/PHOTONFORGE_Photo-Workflow),
an offline photography pipeline project that grew into a systems-engineering
exercise. The patterns proven there — Issue-canonical requirements,
auto-rendered docs, V&V matrix, SysML-Mermaid diagrams, milestone-aware
rollup, Superpowers-paired agent roster — are generalized here for any
engineering discipline.

See `METHODOLOGY.md` for the design philosophy and `dev-docs/` for the
detailed how-tos as they get written.

## Quick start

> **First time on a new machine?** Start with
> [`dev-docs/getting-started.md`](dev-docs/getting-started.md) — it
> walks you from nothing installed through tools, tokens, wiki setup,
> and the first bootstrap. ~30–45 min.
>
> If your tools are already set up, the short version is below.

This is an **agent-driven** workflow — you don't customize the YAML
files by hand. You paste a bootstrap prompt into Claude Code and let
the agent harness do the scoping, profile activation, UN drafting,
and render-chain setup conversationally.

```bash
# 1. On GitHub: "Use this template" → create new private repo
# 2. Locally:
gh repo clone <owner>/<your-new-repo>
cd <your-new-repo>
pip install -r requirements.txt
# 3. Copy the bootstrap worksheet and fill it by hand:
cp prompts/bootstrap.md prompts/bootstrap_<your-name>.md
$EDITOR prompts/bootstrap_<your-name>.md   # fill Section A
git add prompts/bootstrap_<your-name>.md
git commit -m "chore(inception): scoping worksheet by <your-name>"
# 4. Open Claude Code and paste the filled file:
code .
# Paste the entire contents of prompts/bootstrap_<your-name>.md into
# a new Claude Code session. Claude reads Section A and executes
# Section B: profile activation, UN drafting, render chain.
```

The bootstrap workflow is **copy-fill-commit-paste**, not interactive.
The filled `bootstrap_<your-name>.md` is committed as the project's
permanent inception record — "this is how it started." See
[prompts/bootstrap.md](prompts/bootstrap.md) for the worksheet and
[prompts/bootstrap-faq.md](prompts/bootstrap-faq.md) if you get stuck
on a field.

If you'd rather skip the conversation and drive the bootstrap by hand:

```bash
nano config/disciplines.yml config/stages.yml config/evidence-kinds.yml
python scripts/init_project.py --activate-profile A    # or B / C
python scripts/init_project.py --seed-sample           # files UN-001
```

But the prompt path is the recommended one — it's what the template
is built around.

## Layout

See `METHODOLOGY.md` for what each directory is for. Brief tour:

- `config/` — three YAML files (disciplines, stages, evidence kinds) that adapt the template to your project
- `requirements/` — the requirement decomposition tree (`requirement-map.yml`) + interface ICDs (`interfaces/IF-*.md`)
- `artifacts/` — text manifests for non-text engineering artifacts (CAD, PCB, firmware, large datasets). Format spec: `dev-docs/architecture/artifact-manifest.md`. Validator: `scripts/validate_artifacts.py`. Worked example: `artifacts/mechanical/EXAMPLE-motor-mount.md`.
- `verification/` — DVT/EVT/PVT/bench/simulation test plans + result links
- `model/` — auto-generated SysMLv2 textual notation (`system.sysml`); read by Syson, Cameo, etc.
- `verification/` — test plans (markdown) and result links
- `dev-docs/` — developer documentation source; rendered to the wiki
- `docs/` — placeholder for end-user / customer-facing docs
- `prompts/` — paste-into-Claude prompts that drive multi-step agent workflows the template can't fully script. Start with `prompts/bootstrap.md`.
- `scripts/` — 10 scripts: `init_project`, `generate_docs`, `pr_rollup`, `migrate_wiki`, `kpm_rollup`, `export_sysml`, `validate_artifacts`, `github_comment`, `sync_labels`, `github_client`. See `scripts/README.md`.
- `.claude/agents/` — active agent roster (populated from agent-packs by `init_project.py`)
- `.claude/agent-packs/` — discipline-specific lead agents: software, mechanical, electrical, firmware, manufacturing, regulatory (all landed in Pass 3)
- `.github/` — Issue templates, workflows (regen-docs, pr-close-issues, wiki-publish, kpm-rollup, sysml-export), labels

## License

To be decided per project. The template itself is MIT (placeholder).
