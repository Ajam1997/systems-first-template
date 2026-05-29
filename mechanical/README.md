# mechanical/

**Source files** for mechanical work — hand-authored, agent-diffable.
Build123d Python is the primary code-CAD library. Outputs land in
[`../artifacts/mechanical/`](../artifacts/mechanical/) (written
directly by each part script's `export_step()` call).

## Source vs output

| Lives here (source) | Lives in `artifacts/mechanical/` (output) |
|---|---|
| `parts/<part>.py` — Build123d Python part | `<part>-rev<N>.step` — exported STEP |
| `assemblies/<asm>.py` — Build123d Python assembly | `<asm>-rev<N>.step` |
| `drawings/<drawing>.py` — Build123d + ezdxf drawing | `drawings/<drawing>-rev<N>.dxf` + `.pdf` |
| (no source-side equivalent) | `snapshots/<part>-rev<N>.png` — preview render |
| (no source-side equivalent) | `<part>-rev<N>.md` — artifact manifest (for parts large enough to need vault storage) |

## Layout

```
mechanical/
├── parts/        # Build123d Python sources, one .py per part
├── assemblies/   # Multi-part assemblies (use Build123d joints/mates)
└── drawings/     # Build123d + ezdxf annotated drawings
```

## Conventions

- One Python file per part (`parts/<part>.py`); name matches the
  manifest at `artifacts/mechanical/<part>.md`.
- Each `.py` file should be runnable standalone: `python parts/<part>.py`
  exports the STEP to `artifacts/mechanical/<part>-rev<N>.step` and the
  snapshot to `artifacts/mechanical/snapshots/<part>.png`.
- Parametric variables (dimensions, tolerances) live at the top of the
  file with named constants — agents can re-tune without re-deriving
  geometry.

## Drawings

The drawings toolkit lives at `tools/drawings/` and incubates here
until the API stabilizes. When the first mechanical part needs a
drawing, write the toolkit then. See
`dev-docs/architecture/external-tools.md` → "Deferred — the drawings
toolkit" for the extraction plan.

## See also

- `.claude/agent-packs/mechanical/mechanical_lead.md` — full authoring convention
- `dev-docs/architecture/external-tools.md` — tool stack rationale
