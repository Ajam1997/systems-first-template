# `model/` — Generated SysMLv2 model

This directory holds the project's requirement tree rendered as
SysMLv2 textual notation. **The file in here is generated.** Do not
hand-edit.

## What's here

- **`system.sysml`** — the project's entire requirement tree as a
  single SysMLv2 `package` block. Includes user needs, functional /
  non-functional / interface requirements, KPM constraint blocks with
  aggregation metadata, and stage milestone verification cases.

## Regeneration

Manual:
```powershell
sf-sysml            # uses live Issue bodies
sf-sysml --offline  # YAML-only, no GitHub
```

Automatic: `.github/workflows/sysml-export.yml` runs on push to main
that touches `requirements/requirement-map.yml` or the export script,
and commits the result with `[skip ci]`. Disable by deleting that
workflow file if you'd rather only generate on demand.

## Source of truth

The mapping spec lives in `dev-docs/architecture/sysml-export.md`.
The source is `requirements/requirement-map.yml` plus the live state
of GitHub Issues. Edit those; the generated file follows.

## Tooling

The generated file targets SysMLv2 textual notation (OMG 2024 spec).
Open it in:

- **[Eclipse Syson](https://github.com/eclipse-syson/syson)** —
  open-source SysMLv2 modeling environment (EPL 2.0)
- **[OMG SysMLv2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation)** —
  the reference implementation
- Commercial tools that support SysMLv2 (Cameo, Catia Magic, etc.)

If your target tool rejects something, tune the relevant renderer
function in `sf-sysml` (`systems-first` package) — the mapping (what
becomes what) is stable; the syntax is the part most likely to need
adjustment as SysMLv2 tools mature.
