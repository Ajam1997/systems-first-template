# Systems-First Template

A GitHub template for **systems-engineering-first project development**, usable
across software, electrical, mechanical, firmware, and mixed-discipline
projects. Built on top of GitHub Issues + Milestones + a Claude Code agent
harness. SysML-flavored without leaving GitHub.

> **Status:** seedling. Pass 1 (software-flavored skeleton) under construction.
> Mechanical and electrical discipline packs to follow.

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

## Quick start (when Pass 1 lands)

```bash
# 1. Use this template on GitHub → "Use this template" → new private repo
# 2. Clone your copy
# 3. Customize config/
nano config/disciplines.yml    # which discipline leads are active
nano config/stages.yml         # your project's phase model
nano config/evidence-kinds.yml # what counts as V&V evidence in your domain
# Resource budgets (mass/power/cost/thermal/schedule) are aggregated KPMs
# in requirements/requirement-map.yml — file them as you add UNs.
# 4. Bootstrap the repo (creates Milestones, syncs labels, activates agents)
python scripts/init_project.py --dry-run     # preview
python scripts/init_project.py --seed-sample # apply + file UN-001
# 5. Open in Claude Code and let the agent harness scaffold the rest.
```

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
- `scripts/` — 10 scripts: `init_project`, `generate_docs`, `pr_rollup`, `migrate_wiki`, `kpm_rollup`, `export_sysml`, `validate_artifacts`, `github_comment`, `sync_labels`, `github_client`. See `scripts/README.md`.
- `.claude/agents/` — active agent roster (populated from agent-packs by `init_project.py`)
- `.claude/agent-packs/` — discipline-specific lead agents (software, mechanical; electrical/firmware/manufacturing/regulatory are roadmapped placeholders)
- `.github/` — Issue templates, workflows (regen-docs, pr-close-issues, wiki-publish, kpm-rollup, sysml-export), labels

## License

To be decided per project. The template itself is MIT (placeholder).
