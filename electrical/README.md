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

## Where outputs go — two write paths

1. **Atopile writes BOM / netlist / reports directly** via
   `paths.output_base` in `ato.yaml`. Set it to
   `../../../artifacts/electrical/<board>-rev<N>` and atopile drops
   `.bom.csv`, the netlist subfolder, `.variables.md`, etc., straight
   into `artifacts/electrical/`.

2. **`export.py` promotes the live PCB**. Atopile keeps the placed
   layout in `<project>/layouts/<target>/<target>.kicad_pcb` —
   that's the file with footprints, traces, and pour. To make it
   available in `artifacts/electrical/<board>-rev<N>.kicad_pcb`,
   every board ships an `export.py` that runs `ato build` and then
   copies the live PCB forward.

```yaml
# <board>/<project>/ato.yaml
builds:
  default:
    entry: main.ato:App
    paths:
      output_base: ../../../artifacts/electrical/<board>-rev<N>
```

```bash
# Author the schematic in <project>/main.ato.
# Place + route in pcbnew on <project>/layouts/default/default.kicad_pcb.
# When ready to publish:
python export.py
# -> writes artifacts/electrical/<board>-rev<N>.bom.csv (etc., from atopile)
# -> copies layouts/.../default.kicad_pcb -> artifacts/electrical/<board>-rev<N>.kicad_pcb
```

> **The empty `.<timestamp>.kicad_pcb` mystery.** Atopile writes a
> pre-build backup stub to `<output_base>.<timestamp>.kicad_pcb` on
> every build. It has zero footprints (it's a snapshot taken before
> the build placed anything). Gitignored at the template level.

See
[`.claude/agent-packs/electrical/electrical_lead.md`](../.claude/agent-packs/electrical/electrical_lead.md)
for the full pattern, the suffix table, and the worked example
script.

## See also

- [`../artifacts/electrical/`](../artifacts/electrical/) — where outputs go
- [`../artifacts/README.md`](../artifacts/README.md) — source-vs-output split
- [`../dev-docs/architecture/external-tools.md`](../dev-docs/architecture/external-tools.md) — tool stack rationale
- [`../.claude/agent-packs/electrical/electrical_lead.md`](../.claude/agent-packs/electrical/electrical_lead.md) — full authoring convention
