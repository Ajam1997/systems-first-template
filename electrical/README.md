# electrical/

**Source files** for electrical work — hand-authored, agent-diffable.
Outputs land in [`../artifacts/electrical/`](../artifacts/electrical/)
(direct write from `ato build` via `paths.output_base`).

## Source vs output

| Lives here (source) | Lives in `artifacts/electrical/` (output) |
|---|---|
| `<board>/<project>/main.ato` — Atopile schematic source | `<board>-rev<N>.bom.csv` — BOM |
| `<board>/<project>/<board>.kicad_sch` — KiCad fallback | `<board>-rev<N>.pcba.step` — 3D PCB |
| `<board>/<project>/layouts/<target>/<target>.kicad_pcb` — live layout | `<board>-rev<N>.gerber.zip` — fab gerbers |
| `<board>/<project>/ato.yaml` — project config | `<board>-rev<N>.<timestamp>.kicad_pcb` — layout snapshot |
| `<board>/<project>/build/` (gitignored) — intermediate atopile state | `<board>-rev<N>.pcba.png` — top + bottom render |

## Layout convention

```
electrical/
└── <board-name>/
    └── <atopile-project>/      # e.g. main-board/
        ├── main.ato            # Atopile schematic source (preferred)
        ├── ato.yaml            # project config — pin output_base here
        ├── layouts/
        │   └── default/
        │       └── default.kicad_pcb   # KiCad layout, edit in pcbnew
        ├── build/              # gitignored — `ato build` intermediates
        └── README.md           # board-specific notes
```

For pure-KiCad boards (no Atopile), drop the `<atopile-project>/` layer
and put `<board>.kicad_sch` + `<board>.kicad_pcb` directly under
`<board-name>/`.

## Configuring atopile to write fab outputs into `artifacts/`

In `<board>/<project>/ato.yaml`:

```yaml
builds:
  default:
    entry: main.ato:App
    paths:
      # Relative to this project root. Adjust ../ depth to reach repo root.
      output_base: ../../../artifacts/electrical/<board>-rev<N>
```

After `ato build`, fab-ready outputs land in `artifacts/electrical/`
prefixed with `<board>-rev<N>`. See
[`.claude/agent-packs/electrical/electrical_lead.md`](../.claude/agent-packs/electrical/electrical_lead.md)
for the full convention and the full atopile suffix table.

## See also

- [`../artifacts/electrical/`](../artifacts/electrical/) — where outputs go
- [`../artifacts/README.md`](../artifacts/README.md) — source-vs-output split
- [`../dev-docs/architecture/external-tools.md`](../dev-docs/architecture/external-tools.md) — tool stack rationale
- [`../.claude/agent-packs/electrical/electrical_lead.md`](../.claude/agent-packs/electrical/electrical_lead.md) — full authoring convention
