# `dev-docs/`

Developer documentation. **This is the source.** What's rendered to the
GitHub Wiki by `scripts/migrate_wiki.py` comes from here.

## Contents

### Hand-authored (you edit these directly)
- `architecture/` — design documents, contracts, SysML diagrams, briefs
- `SystemReviews/` — operator-invoked deep reviews (`@systemmaster`)
- `research/` — investigations, prototypes, decision-making notes

### AUTO-managed (regenerated from Issues by `scripts/generate_docs.py`)
- `requirements-summary.md` — UN/FR/NFR/IF list with status and decomposition
- `roadmap.md` — milestone-driven phase table with progress
- `kpm-dashboard.md` — KPM table with last-measured and status
- `v-and-v-matrix.md` (or rendered into architecture doc) — V&V coverage table

Hand edits inside `<!-- AUTO:key -->` sentinels are clobbered on next
regen. Edits outside the sentinels survive.

### Configuration
- `_wiki-nav.yml` — wiki sidebar definition. The single source of nav.

## Rules

- Edit Issues to change requirement state, body, or labels.
- Edit hand-authored `.md` files in `architecture/`, `SystemReviews/`,
  `research/` directly.
- Don't edit AUTO sections.
- Don't edit the wiki directly unless the page is marked
  `<!-- WIKI:LOCAL-ONLY -->` on line 1.

## Why this matters

This is rule 2 of the five rules in `METHODOLOGY.md`:

> Docs render from Issues. Hand edits inside AUTO sentinels lose; edits
> outside them survive forever.

If you find yourself wanting to edit an AUTO section, fix the Issue
instead. The doc will follow on next regen.
