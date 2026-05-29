# External Tooling Stack

Tool selection for the disciplines that produce non-text engineering
artifacts (electrical, mechanical, firmware). This doc captures the
*design intent* behind the stack — what's optimized, what's deferred,
and where the rough edges are — so future contributors don't have to
re-derive the decision tree.

> **Scope.** This doc is opinionated about the *preferred* stack for
> projects starting from this template. It is not a mandate. A project
> may pick differently for documented reasons (existing licenses,
> supplier constraints, etc.); document the choice in your project's
> `CLAUDE.md`.

---

## Optimization axes

The stack is optimized for an **agent-driven workflow**. The five axes
that drove every choice:

1. **Text-as-source.** Agents can diff and review their own work.
   Binary formats are opaque to PR review.
2. **Python / CLI bindings.** Agents can invoke the tool headlessly,
   not just operate the GUI.
3. **Standard-format outputs.** STEP, gerber, DXF, ODB++ — so a tool
   choice is never a one-way door.
4. **CI-friendliness.** Self-hosted runners with the toolchain in a
   Docker container can verify artifacts on every PR.
5. **Cost + license model.** FOSS or trivial-cost. Per-seat licenses
   block self-hosted CI runners.

Things explicitly **not** optimized for: GUI polish, vendor-bundled
library catalogs, BOM-management plugins. Those can be added per
project as needed.

---

## The stack

| Discipline | Concern | Tool | Source format | Notes |
|---|---|---|---|---|
| **Electrical** | Schematic capture | **Atopile** | `.ato` (native code) | Compiles to KiCad netlist; agents author end-to-end |
| | PCB layout | **KiCad pcbnew** | `.kicad_pcb` (sexp text) | Python API for agent-driven placement/routing |
| | Verification in CI | `kicad-cli` | n/a (consumer) | DRC, ERC, gerber + 3D STEP export, headless |
| | Circuit simulation | **ngspice** | `.sp`, `.cir` text | Already integrated with KiCad |
| | Schematic fallback | **KiCad eeschema** | `.kicad_sch` (sexp text) | When Atopile isn't the right fit or for legacy import |
| **Mechanical** | Parts + assemblies | **Build123d** | `.py` (native code) | Modern code-CAD on OCCT; agents author end-to-end |
| | Parts fallback | **CadQuery** | `.py` (native code) | Mature alternative; same OCCT core |
| | Drawings | **Build123d + ezdxf** | `.py` (native code) | Code-authored DXF with full annotation layer + title block. *Toolkit lives per-project until API stabilizes — see "Deferred" below.* |
| | Drawings fallback | **FreeCAD TechDraw** | XML + GUI state | Use when a human needs a parametric history GUI |
| | FEA | **CalculiX via FreeCAD FEM** | text input deck | Scriptable; CI-friendly |
| | Thermal / CFD | ParaView + OpenFOAM | text input deck | Heavyweight; gate on scheduled workflows, not PRs |
| **Firmware** | RTOS | Zephyr or FreeRTOS | C/C++ + Kconfig | Both have strong agent-driveable build systems |
| | Build | west / cmake / PlatformIO | text | Standard |
| | HIL | pytest-embedded | Python | Agent-authorable tests |
| **EMC pre-compliance** | Field simulation | **OpenEMS** | Octave / Python | Steep learning curve; expect human-paired |

### Lingua franca

**STEP** is the cross-discipline interchange format. KiCad exports
STEP for the 3D PCB; Build123d imports STEP for the enclosure
designer; both pass STEP to manufacturers.

DXF is the secondary interchange — drawings to fab shops, 2D outlines
between MCAD and ECAD.

---

## Integration patterns

Four ways an agent can produce a non-text artifact. Each tool in the
stack fits one or two patterns; this table makes the fit explicit.

| # | Pattern | When | Examples in this stack |
|---|---|---|---|
| 1 | **Code-generated** | Artifact *is* a Python file (or compiles from one). Agent authors directly. | Atopile, Build123d, CadQuery, ezdxf drawings, SKiDL netlists |
| 2 | **CLI-driven** | Agent invokes a headless tool to transform / verify. | `kicad-cli`, `FreeCADCmd`, `ngspice`, CalculiX |
| 3 | **MCP-driven** | Agent talks to a long-running tool via Model Context Protocol. | `kicad-mcp` for live schematic edits (when needed); CAD MCPs are emerging |
| 4 | **Human-paired** | Tool has no headless mode. Agent produces the *manifest + delta description*; human executes. | Fusion 360, SolidWorks, Altium (when a project inherits one) |

The artifact manifest pattern (`artifacts/<discipline>/<name>.md`)
works for all four. Pattern 4 just means the manifest's `storage`
field points at the vault, and the snapshot is hand-rendered.

---

## Rough edges (transparent)

These are known weak spots. None are blockers. Each has a documented
workaround.

### Atopile maturity
- Young project, small community, API will churn.
- **Mitigation:** pin Atopile version per project in `requirements.txt`.
  KiCad eeschema is the always-available fallback.

### MCAD ↔ ECAD round-trip
- Forward: KiCad → STEP → Build123d works cleanly.
- Reverse: Build123d → KiCad (board outline updates from mech) is a
  hand-export step.
- **Mitigation:** treat mechanical as upstream of electrical when
  possible; lock board outlines early.

### Drawings toolkit not in the template yet
- The Build123d + ezdxf drawings pipeline is the recommended approach,
  but the integration code itself is **deferred** — see "Deferred" below.

### CI tool installation
- `kicad-cli`, `FreeCADCmd`, OpenSCAD, OpenEMS all need to be present
  on the runner. GitHub-hosted runners don't ship them.
- **Mitigation:** self-hosted runner with a Docker image carrying the
  toolchain. Stub Dockerfile lives at `deploy/runner.Dockerfile` (when
  added — currently TBD).

### EMC / FEA wall-clock time
- Full sweeps take minutes to hours. Inappropriate for PR gating.
- **Mitigation:** smoke checks on PR, full sweeps on a scheduled
  workflow.

### TechDraw limitations
- TechDraw is GUI-first; scripting is fragile.
- **Mitigation:** use Build123d + ezdxf (Pattern 1) as the primary
  drawings path. TechDraw only when a parametric history GUI is
  genuinely needed.

### Proprietary tools as escape hatch
- Solidworks, Altium, Fusion 360, Allegro, etc. have no realistic
  headless mode for agent authorship.
- **Mitigation:** Pattern 4 (Human-paired). Agent produces the
  manifest and the delta description; human executes in the GUI.

---

## Deferred — the drawings toolkit

The **Build123d + ezdxf drawings pipeline** is the right pattern but
the integration code (~300–500 LOC: title block, auto-dimensions
from named features, multi-view orthographic projection helpers) is
**deferred to per-project incubation until the API stabilizes**.

Current plan:
1. First project that needs a mechanical drawing (likely
   `feline-enrichment-device`) writes the toolkit under
   `tools/drawings/` in that project's repo.
2. Iterate against ~3–5 real parts. Patterns will emerge.
3. **Extraction criterion:** when the third project would copy-paste
   the same module, lift it to the template (or its own PyPI package,
   decide then).

Until extracted, projects that need drawings should look at the
incubating toolkit in `feline-enrichment-device/tools/drawings/` (or
the latest project incubating it).

---

## When to override the stack

Pick differently when:

- **Suppliers demand specific file formats.** A contract manufacturer
  that only accepts Altium files forces Altium. The stack's STEP and
  gerber outputs cover most low-volume fab shops (JLCPCB, OSH Park,
  SendCutSend, PCBWay).
- **Existing license sunk cost.** A current Fusion 360 / SolidWorks /
  Altium seat that's already paid for: keep using it for human-paired
  work (Pattern 4). Don't agent-author against it; the leverage isn't
  there.
- **High-speed PCB or aerospace-grade FEA.** Allegro / Ansys are
  industry-grade and have agent integration ceilings the template
  can't fix. Use Pattern 4.

Document any override in your project's `CLAUDE.md` so future agents
in the project see the constraint.

---

## See also

- [artifact-manifest.md](artifact-manifest.md) — manifest format that bridges all four integration patterns
- [doc-source-of-truth.md](doc-source-of-truth.md) — who writes what across disciplines
- [vv-matrix.md](vv-matrix.md) — V&V evidence format
- `.claude/agent-packs/electrical/electrical_lead.md` — electrical lead's tool-specific authoring conventions
- `.claude/agent-packs/mechanical/mechanical_lead.md` — mechanical lead's tool-specific authoring conventions
