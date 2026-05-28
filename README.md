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

- **Requirements as data** — user needs, functional requirements, non-functional
  requirements, interface requirements, KPMs/budgets — all live as GitHub
  Issues with structured bodies and decomposition links.
- **A single source of truth** — Issues are canonical. Docs are auto-rendered
  from Issues. The wiki is a one-way export. Hand edits to AUTO sections lose.
- **Verification & Validation traceability** — every requirement carries an
  explicit list of evidence sources (test, simulation, bench, inspection,
  review) in its Issue body. A V&V matrix table renders automatically and
  shows the coverage gap.
- **Stage-gated delivery via GitHub Milestones** — one milestone per phase.
  A milestone closes automatically when its user-needs roll up to verified.
- **SysML-style diagrams** — Mermaid-based state machines, activity
  diagrams, block-definition diagrams. Renders natively in GitHub & wiki.
- **A Claude Code agent harness** — declarative discipline leads
  (`systems_lead`, `mechanical_lead`, `electrical_lead`, `firmware_lead`,
  `software_lead`, `manufacturing_lead`, `regulatory_lead`), plus universal
  `verification`, `validation`, and `systemmaster` agents.

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
- Not finished. Pass 1 is software-shaped. Hardware/EE/ME discipline
  packs are roadmapped.

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
# Resource budgets (mass/power/cost/thermal/schedule) are KPMs
# in requirements/requirement-map.yml — file them as you add UNs.
# 4. Create your first user need
gh issue create --label "type: user-need,status: defined,stage: 1" \
  --title "[UN-001] First user need"
# 5. Open in Claude Code and let the agent harness scaffold the rest.
```

## Layout

See `METHODOLOGY.md` for what each directory is for. Brief tour:

- `requirements/` — the requirement decomposition tree
- `artifacts/` — links + pointers + snapshots for non-text engineering artifacts
- `verification/` — test plans (markdown) and result links
- `dev-docs/` — developer documentation source; rendered to the wiki
- `docs/` — placeholder for end-user / customer-facing docs
- `scripts/` — `generate_docs.py`, `pr_rollup.py`, `migrate_wiki.py`
- `.claude/agents/` — agent roster
- `.github/` — Issue templates, workflows, labels

## License

To be decided per project. The template itself is MIT (placeholder).
