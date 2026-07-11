# SysMLv2 Export — Mapping Spec

`sf-sysml` (from the `systems-first` package) renders the project's requirement tree as a
single `.sysml` file in SysMLv2 textual notation. This document
specifies the YAML → SysMLv2 mapping the CLI implements.

The export is a **render target**, not a source of truth. Authoring
stays in GitHub Issues and `requirements/requirement-map.yml`. The
`.sysml` file is regenerated from those on demand or in CI.

## Why this exists

SysMLv2 (OMG, 2024) is a text-first formal modeling language with an
emerging tool ecosystem (Eclipse Syson, Cameo, Catia Magic). Where the
template's YAML + Issues captures the *shape* of SysML relationships
informally, a `.sysml` file lets you:

- Open the model in Syson or any conformant tool for diagram rendering
- Run formal validation (constraint solver, type checking)
- Export to vendor-portable formats for tool migration
- Use commercial integration paths (round-trip with CAD, simulation)

The template can ship the `.sysml` without requiring projects to adopt
any SysMLv2 tooling — projects that don't need it ignore the generated
file. See METHODOLOGY.md "The V-model and where KPMs live" for the
philosophical fit.

## Mapping table

| YAML element | SysMLv2 element | Notes |
|---|---|---|
| `user_needs.<UN-ID>` | `requirement def <UN_ID>` | Top-level requirements; doc string from Issue title or Acceptance field |
| `functional_requirements.<FR-ID>` (or as a child of a UN) | `requirement def <FR_ID> :> <parent UN>` | `:>` is SysMLv2 specialization = «derive». Multi-parent FRs derive from each parent UN. |
| `non_functional_requirements.<NFR-ID>` | `requirement def <NFR_ID> :> <parent UN>` | Same shape as FR |
| `interface_requirements.<IF-ID>` | `interface def <IF_ID>` with `end side_a; end side_b;` | Dual-sided. Sides are simplified `end` declarations; richer port typing is future work. |
| `kpms.<KPM-ID>` | `constraint def <KPM_ID>` with `target_value`, `target_op`, `unit`, `aggregation` attributes | The rollup expression is currently emitted as a `//` comment; full executable expressions per tool's solver dialect are future work. |
| `stages.<N>` | `verification case def Stage_<N>_<sanitized_title>` containing `verify <UN_ID>;` lines | One verification case per milestone. |

## ID normalization

SysMLv2 identifiers can't contain hyphens or dots. The script normalizes:

| Input | Output |
|---|---|
| `UN-001` | `UN_001` |
| `FR-1.4` | `FR_1_4` |
| `KPM-pcb-mass` | `KPM_pcb_mass` |
| `Stage 4 — Host Integration` | `Stage_4___Host_Integration` |

The original ID is preserved in comments above each definition so the
generated file remains traceable to the YAML.

## File output

Default path: `model/system.sysml`

One file per project. The whole tree lives in one `package` block named
after the repo (PascalCased from `REPO_NAME` env var → git remote →
repo directory name). Single-file output is simplest for Syson import
and CI validation; future versions may split per stage if files get
unwieldy.

## What's currently *not* mapped

These are deliberate omissions for Pass 1.7 — add when a real use case
demands them:

- **Behavior diagrams** — state machines, activity diagrams. The template
  has these as hand-authored Mermaid in `dev-docs/architecture/`.
  SysMLv2 has `state def` and `action def`; mapping would require either
  hand-authored SysMLv2 snippets or a Mermaid→SysMLv2 parser. Punt.
- **Executable constraint expressions** — KPM aggregation is emitted as a
  comment, not a SysMLv2 calculation. Each target tool's solver dialect
  varies; the YAML stays authoritative for `sf-kpm-rollup` math.
- **Port typing on interfaces** — IFs render with bare `end side_a` /
  `end side_b`. Real interface typing (flow ports, signal types) needs
  more schema in `interface_requirements/` than the YAML currently
  carries. Punt to Pass 3.
- **Allocations** — SysMLv2 has `«allocate»` relationships between
  requirements and parts. Requires modeling parts (`part def`), which
  the YAML doesn't carry. Future: when an `artifacts/` manifest format
  lands (Pass 2), parts can be inferred and allocations emitted.
- **Constraints linking KPMs to requirements** — beyond the rollup
  comments, KPMs don't carry an explicit `«verify»` link to the
  requirement they measure. The KPM Issue's `Linked Requirements` field
  is the human-readable surface; emitting it as a SysMLv2 constraint
  binding would be a Pass 2 polish.

## Limitations & caveats

**The syntax is the part most likely to need tuning.** SysMLv2 textual
notation is still maturing across tools. The script's renderer functions
(`render_user_need`, `render_kpm`, etc.) are small and isolated — if
Syson or your target tool rejects something, tune the renderer for that
construct without touching the mapping logic.

**Validate against your tool before committing the output.** The script
produces plausible SysMLv2 text but doesn't run a parser pass. The
suggested loop:

1. Run `sf-sysml --offline`
2. Open `model/system.sysml` in Syson (or run `syson-cli validate`)
3. If something's rejected, note the rule and adjust the relevant
   renderer
4. Re-run, repeat

**No round-trip yet.** This is `.yaml → .sysml`, never `.sysml → .yaml`.
Edits to the generated file are lost on next run. The header banner
warns hand-editors.

## When to regenerate

Trigger the export when:
- `requirements/requirement-map.yml` changes
- A new UN/FR/NFR/IF/KPM Issue is filed and you want its title + body in the doc strings
- Before opening Syson for a session

Automation options:
- **Manual** — `sf-sysml` whenever
- **CI** — `.github/workflows/sysml-export.yml` runs on push to main, commits the result with `[skip ci]`. Optional; not enabled by default.

## See also

- `sf-sysml` (`systems-first` package) — the renderer (small enough to read end-to-end)
- `requirements/requirement-map.yml` — the source of truth
- `METHODOLOGY.md` "The V-model and where KPMs live" — why KPMs deserve formal constraint blocks
- [Eclipse Syson](https://github.com/eclipse-syson/syson) — primary target SysMLv2 tool
- [OMG SysMLv2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation) — the reference impl + spec authority
