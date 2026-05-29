# Methodology — Systems-First Project Development

This template encodes one opinionated way to run an engineering project:
**requirements before artifacts, traceability before output, evidence
before claims.** It's MBSE/SysML-flavored, but the rigor is enforced by
small scripts and GitHub primitives — not by buying a modeling tool.

This document is the design philosophy. Read once, refer to it when a
decision feels arbitrary.

---

## The five loops

```
                       ┌─────────────────────────────────────┐
                       ▼                                     │
   STAKEHOLDER → REQUIREMENTS → DESIGN → BUILD → VERIFY → VALIDATE
       NEEDS                                                  │
        ▲                                                     │
        └─────────────────────────────────────────────────────┘
```

Five loops run continuously, at different cadences:

1. **Requirements loop** — needs and requirements get added, decomposed,
   refined as the system matures. Cadence: weeks-to-months.
2. **Design loop** — architecture, interface definitions, behavior and
   structure diagrams. Cadence: days-to-weeks.
3. **Build loop** — code, CAD, schematics, PCB, firmware. Cadence:
   hours-to-days for software; days-to-weeks for hardware.
4. **Verification loop** — does each requirement's implementation work?
   Cadence: matches the build loop for the artifact in question.
5. **Validation loop** — does the integrated system meet the original
   user need? Cadence: per stage / per milestone.

The template's job is to keep all five loops in sync **as data**, not as
documents-that-go-stale.

---

## Five rules that don't bend

### 1. Issues are canonical for status

A requirement's *state* (`defined → in-progress → verified → validated`)
lives on its GitHub Issue's labels. Nothing else. Not the doc, not the
wiki, not a spreadsheet. If a requirement is "verified" but the Issue
says "defined," the requirement is defined.

`scripts/pr_rollup.py` is the sole writer of `status: verified` and
`status: validated`. Humans can flip labels by hand; the convention
is don't, but the system survives if they do.

### 2. Docs render from Issues

`scripts/generate_docs.py` regenerates the AUTO sections of the living
docs (`requirements-summary.md`, `roadmap.md`, `kpm-dashboard.md`,
`v&v-matrix`) from current Issue state. Hand edits inside AUTO sentinels
(`<!-- AUTO:key -->`) lose on the next regen. Hand edits *outside*
sentinels survive forever.

If a needed edit doesn't fit outside the sentinel, the Issue is the wrong
source — fix the Issue, not the doc.

### 3. Wiki is one-way export

The wiki is your private memory aid. `scripts/migrate_wiki.py --push`
renders `dev-docs/` into the wiki. Direct wiki edits are preserved only
if the wiki page is tagged `<!-- WIKI:LOCAL-ONLY -->` on line 1.

The wiki is rendered, not authored. Read on the wiki; write in `dev-docs/`.

### 4. Every requirement has a Verified By and a Validated By

Empty is fine when a requirement is freshly filed. But the V&V matrix
renders a `✗` next to it until those lines exist, and that's the worklist.

`Verified By:` answers *"how do we know the implementation does what the
requirement says?"* — usually a test, simulation, or measurement.

`Validated By:` answers *"how do we know the requirement was the right
one?"* — usually a KPM measurement, an E2E demonstration, or a customer
acceptance check.

For user needs, `Verified By` rolls up from their decomposed FRs/NFRs.
For KPMs, `Validated By` is typically empty (KPMs *are* the validation).

### 5. Every handoff leaves a breadcrumb

Agent comments end with `**Next action:** ...`. Engineer briefs end with
`## Open questions if you stop mid-step`. PR descriptions tell the next
reader where to pick up.

The cost is one line per artifact. The benefit is being able to resume
mid-flight work — yours or another agent's — without re-deriving context.

---

## The artifact hierarchy

Five Issue types form the spine:

| Type | What it is | Example | Owner |
|---|---|---|---|
| `type: user-need` | A capability a stakeholder wants. Black-box. | "Photos receive descriptive filenames" | product / systems lead |
| `type: fr` (functional) | A specific behavior the system must perform | "Generate semantic filename from image content" | discipline lead |
| `type: nfr` (non-functional) | A constraint the system must respect | "Runs offline, no network calls" | systems lead |
| `type: if` (interface) | A boundary between two subsystems / disciplines | "Motor mount thermal interface" | dual ownership |
| `type: kpm` (key performance measure) | A measurable that gates acceptance. Can be a leaf measurement or a computed rollup of child KPMs. | "Inference ≤ 2.5 s/image" (leaf); "System mass ≤ 250 g" (sum-aggregated) | discipline lead (leaves); systems lead (rollups) |

Budgets are a specialization of KPMs — a budget is a KPM with
`aggregation: sum` and a list of subsystem allocations as children.
See `requirements/requirement-map.yml` for the schema.

Decomposition lives in `requirements/requirement-map.yml`:

```yaml
user_needs:
  UN-001:
    functional_requirements: [FR-1.1, FR-1.2]
    non_functional_requirements: [NFR-2.1]
    interface_requirements: [IF-1.3]
    kpms: [KPM-1.1]
```

The `requirement-map.yml` is the SysML *requirement diagram* in YAML form.
It's the «derive», «contain», «satisfy» relationships, plain text.

### Non-text artifacts: the manifest pattern

CAD assemblies, PCB layouts, firmware binaries, and large simulation
results don't fit in Issues or YAML — they're binary, opaque to git
diff, and often live in vendor-specific formats.

The template's answer: store a **text manifest** in
`artifacts/<discipline>/<name>.md`, store the actual artifact in your
vault / git-LFS / shared drive. The manifest carries:

- A reference URI to where the artifact actually lives
- A SHA-256 hash so silent vault overwrites get caught on PR review
- A snapshot PNG so reviewers don't need the CAD/EDA tool
- The requirement IDs this artifact «satisfy»s
- An append-only change log

Full schema: `dev-docs/architecture/artifact-manifest.md`. Worked
example: `artifacts/mechanical/EXAMPLE-motor-mount.md`. Validator:
`scripts/validate_artifacts.py`.

This format is discipline-neutral — same manifest shape works for
mechanical STEP files, electrical schematics, firmware `.elf` binaries,
or anything else that doesn't diff in git.

---

## The V-model and where KPMs live

The classic systems-engineering V-model decomposes top-down on the left
side and verifies bottom-up on the right side. KPMs sit at **every level**
of the V, not just at the top.

```
   User Needs ───────────────────► Acceptance Test (UN-level KPMs)
       │                                     ▲
       ▼                                     │
   FRs / NFRs / IFs ─────► System Test (FR/NFR/IF-level KPMs)
       │                            ▲
       ▼                            │
   Implementation ───► Unit Test (component-level KPMs)
```

Putting KPMs only at the user-need level would force acceptance testing
to catch every regression — too late, with no way to localize the
failure. The template puts KPMs as children of *any* requirement level.

KPMs come in two flavors:

- **Independent KPMs** are measured directly on the implementation —
  the leaves of the V's right side.
- **Computed (aggregated) KPMs** derive their value from child KPMs.
  System-level mass is the sum of subsystem masses. Peak power is the
  max of subsystem peaks. End-to-end latency is the bottleneck path.

`scripts/kpm_rollup.py` reads the KPM tree from
`requirements/requirement-map.yml`, collects leaf measurements from each
KPM's Issue, and computes parent values automatically. If a child
overruns its target, the parent flips to failing *by construction* —
you see margin erosion before integration testing reveals it.

Five aggregation patterns cover most cases:

| Pattern | Math | Typical use |
|---|---|---|
| `sum` | parent = Σ children | mass, BOM cost, average power, total LOC |
| `max` | parent = max(children) | peak power, peak temp, peak RSS |
| `min` | parent = min(children) | min margin, weakest-link MTBF |
| `independent` | leaf — measured directly | most KPMs at the lowest level |
| (future) `critical_path` | bottleneck over a declared path | end-to-end latency, throughput |

Use `independent` as the escape hatch for emergent system behavior
that doesn't roll up from subsystems — overall accuracy, "feels fast,"
or any UX KPM where measurement only makes sense on the integrated
whole.

This pattern replaces the older notion of separate "budgets" — a
budget *is* a rolled-up KPM with `aggregation: sum`.

---

## The agent roster

Three universal agents plus a configurable set of discipline leads.

### Universal

- **`systemmaster`** (operator-only) — cross-cutting review, architecture
  audits, doc/process surgery. Use sparingly; produces review briefs to
  `dev-docs/SystemReviews/`.
- **`verification`** — runs the per-commit verification cycle for whatever
  discipline. Posts evidence comments on Issues. Mandates the
  `verification-before-completion` Superpowers skill.
- **`validation`** — runs per-milestone E2E validation. Posts evidence
  comments on UN and Milestone closure-trigger Issues.

### Discipline leads (declared in `config/disciplines.yml`)

Pick zero or more. A project might use only one (software-only) or all of
them (a battery-powered IoT device with a custom enclosure + regulatory):

- **`systems_lead`** — owns the requirements tree, interfaces, budgets,
  architecture decisions. Pairs with Superpowers `brainstorming` and
  `writing-plans`.
- **`software_lead`** — owns `src/` (or equivalent) and software tests.
  Pairs with `test-driven-development`, `subagent-driven-development`,
  `systematic-debugging`, `verification-before-completion`.
- **`firmware_lead`** — owns embedded code, RTOS configuration,
  hardware-software interfaces. Pairs with `test-driven-development`,
  `systematic-debugging`.
- **`electrical_lead`** — owns schematics, PCB layout, signal/power
  integrity. Pairs with `verification-before-completion`,
  `systematic-debugging`.
- **`mechanical_lead`** — owns CAD assemblies, FEA, manufacturing
  drawings. Pairs with `verification-before-completion`.
- **`manufacturing_lead`** — owns DFM/DFA reviews, supplier qualification,
  EVT/PVT planning.
- **`regulatory_lead`** — owns compliance evidence (FCC, CE, UL, ISO,
  applicable standards).

Each lead's `.claude/agents/<name>.md` is a system prompt + an operating
ruleset. Add or remove leads per project by editing `config/disciplines.yml`
and (de)activating the corresponding agent file.

---

## The V&V evidence kinds

The V&V matrix columns are universal. The *vocabulary* of what counts as
evidence is per-discipline, declared in `config/evidence-kinds.yml`:

| Kind | When to use | Example reference |
|---|---|---|
| `pytest` | Python unit/integration test | `pytest: tests/test_x.py::test_y` |
| `unittest` | other unit-test frameworks | `unittest: src/.../test_module.cpp` |
| `simulation` | numerical simulation result | `simulation: sim/thermal-rev-c.run.json` |
| `fea` | finite-element analysis | `fea: cad/mount-stress-analysis-rev3.fea` |
| `spice` | circuit simulation | `spice: pcb/regulator-tran.sp` |
| `bench` | bench-top measurement | `bench: 2026-05-20 oscilloscope capture, BNC-3` |
| `dvt` | Design Verification Test | `dvt: dvt-plan-rev1 §4.2` |
| `evt` | Engineering Verification Test | `evt: evt-build-3, unit #007` |
| `pvt` | Production Verification Test | `pvt: pvt-lot-2, AQL 1.0` |
| `dfm` | DFM/DFA review | `dfm: 2026-04-12 review with supplier ACME` |
| `kpm` | measurement against a KPM target | `kpm: KPM-1.2` |
| `e2e` | end-to-end demonstration | `e2e: stage-3 milestone demo recording` |
| `soak` | endurance / soak test | `soak: KPM-1.4 50-cycle log` |
| `manual` | manual verification step | `manual: operator confirms LED sequence` |
| `script` | scripted verification | `script: scripts/verify_thermal.py` |
| `inspection` | visual / document inspection | `inspection: PR diff shows no docs/ paths` |
| `review` | formal design review | `review: PDR 2026-06-10 minutes` |

Pick the subset that fits your project and add more if needed; the V&V
matrix renderer is kind-agnostic.

---

## The stage / milestone model

Stages are time-bound deliverables, not classifications. They're modeled
as **GitHub Milestones**. A typical software project has 5-8 stages; a
hardware project might have 10-15 spanning years.

The default `config/stages.yml` ships with two presets:

- **Software preset:** Scaffold → Core → Inference → Integration → V&V → Release.
- **Hardware preset:** Concept → PDR → CDR → Engineering Build → DVT → EVT → PVT → Production.

Plus a `custom` slot you fill in. Each stage maps 1:1 to a GitHub Milestone.
`pr_rollup.py` closes the Milestone when all its user-needs roll up to
verified.

---

## The render chain

GitHub Issues + `requirements/requirement-map.yml` are the canonical
source of truth. Three render targets consume them:

```
GitHub Issues + requirement-map.yml  <-- source of truth
              |
              +-> generate_docs.py    --> dev-docs/<AUTO sections>
              |                            (living-user-needs.md,
              |                             architecture.md, etc.)
              |
              +-> migrate_wiki.py     --> github.com/<repo>/wiki
              |                            (one-way; LOCAL-ONLY escape hatch)
              |
              +-> export_sysml.py     --> model/system.sysml
                                           (SysMLv2 textual notation
                                            for Syson, Cameo, etc.)
```

- Edit **Issues** to change status, body, or labels — all three render
  targets refresh on next run.
- Edit **dev-docs/** hand-authored files (architecture notes, briefs,
  research) directly — they ship to the wiki as-is.
- Edit **AUTO-sentineled regions** of living docs — *don't*; edit the
  Issue instead.
- Never edit `model/system.sysml` by hand — regenerate from the YAML
  via `python scripts/export_sysml.py`.

The KPM rollup runs in parallel with these render targets:
`scripts/kpm_rollup.py` reads child KPM measurements from Issue
comments, aggregates them per the `aggregation` field in
`requirement-map.yml`, and posts the computed parent values back as
Issue comments.

---

## The breadcrumb discipline

Three small habits that compound:

1. **Every agent Issue comment ends with `**Next action:**`** —
   the `github_comment.py` CLI requires it.
2. **Every engineer/architect brief ends with `## Open questions if
   you stop mid-step`** — the template ships with the section
   pre-stubbed; you fill it in *before* stopping.
3. **Every PR description names what changed and why, with links
   back to the FR/UN it touches.**

The cost is ~one minute per artifact. The benefit is being able to put
the project down for three days, come back, and resume in five minutes
instead of an hour.

---

## What this template intentionally doesn't do

- **It doesn't do formal SysML semantics.** Diagrams are Mermaid;
  relationships are inferred from filenames + decomposition tree, not
  from a formal model. Trade-off: zero tooling install, no round-trip
  to a modeling tool, no model-execution.
- **It doesn't enforce process.** The discipline comes from running the
  scripts, not from gates that prevent you from working. You can write
  code that has no FR. The V&V matrix will flag it as orphan; the
  template won't block your commit.
- **It doesn't host very large binary artifacts.** Multi-megabyte CAD
  assemblies, FEA blobs, full Gerber zips → use git-LFS, your own vault,
  or a shared drive, with a manifest in `artifacts/`. Small outputs
  (BOM CSVs, snapshot PNGs, single-part STEPs, atopile-generated KiCad
  PCBs) commit directly under `artifacts/<discipline>/` — see
  `dev-docs/architecture/artifact-manifest.md` for the size threshold
  rule of thumb.
- **It doesn't replace your domain tools.** Keep SolidWorks, KiCad,
  Altium, MATLAB, Fusion, Allegro, whatever you have — the template
  wraps around them. For an agent-driven workflow the template
  recommends a specific FOSS / code-first stack (Atopile + KiCad,
  Build123d + ezdxf, FreeCAD FEM, ngspice). See
  `dev-docs/architecture/external-tools.md` for the rationale and
  rough edges. Proprietary tools fit as Pattern 4 ("human-paired")
  escape hatches in that doc.

---

## Where the design came from

Every pattern here was field-tested on a real project before being
extracted. See the PHOTONForge System Review at
`https://github.com/Ajam1997/PHOTONFORGE_Photo-Workflow/tree/main/dev-docs/SystemReviews`
for the unedited narrative of how this set of rules emerged from a
solo-operator photo-pipeline project that turned into a systems-
engineering exercise.

If you're going to deviate from any of the five rules, do it deliberately
and write it down. The rules are load-bearing; they will fail individually
but the system survives. They fail collectively only if you forget which
ones you've already broken.
