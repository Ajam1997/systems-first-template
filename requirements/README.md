# `requirements/`

The requirements layer of the SysML model, kept entirely in text.

## Files

- **`requirement-map.yml`** — the decomposition tree. Maps each user
  need (UN-XXX) to its functional requirements, non-functional
  requirements, interface requirements, KPMs, and budget references.
  Maps each stage to its user needs. This is the SysML requirement
  diagram, in YAML form.

- **`interfaces/IF-X.Y.md`** — one markdown file per interface
  requirement. Each describes the boundary between two subsystems
  or disciplines, with explicit dual ownership, the data/energy/
  signal flow across it, and the V&V evidence that the interface
  works.

## Why these aren't Issues

The Issues *are* the canonical store of each requirement's body, status,
acceptance criteria, and V&V evidence. The files here serve a different
purpose:

- `requirement-map.yml` captures the **relationships** between
  requirements that don't naturally live on a single Issue.
- `interfaces/*.md` capture the **detail** of cross-discipline
  boundaries, which often need diagrams (ICDs, pinouts, mechanical
  drawings, protocol specs) too heavy for an Issue body.

Both are read by `sf-docs` and `sf-pr-rollup`.
They render into the architecture doc; they don't compete with the
Issues for authority over status.

## Editing rules

- **Decomposition (parent/child links)** — edit `requirement-map.yml`.
- **Status, body, acceptance** — edit the Issue, never the docs.
- **Interface detail** — edit `interfaces/IF-X.Y.md` directly.

## Format

See `dev-docs/architecture/requirement-map-format.md` (Pass 1) for the
schema.
