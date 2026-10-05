# <Project Name> — Systems-First Project

> **Template placeholder.** When you instantiate this template, replace
> this file with your project's specifics. Keep the *structure* — the
> sections below are load-bearing for the Claude Code agent harness.

## Context

<1-paragraph description of the project, its hardware/software target,
and the operating environment.>

## Agent Roster

| Agent | Scope | Superpowers pairing |
|---|---|---|
| @systemmaster (operator-only) | deep cross-cutting reviews | n/a |
| @verification (inherit) | commit-level test enforcement | **mandate**: `verification-before-completion` |
| @validation (inherit) | milestone E2E validation | **mandate**: `verification-before-completion` |
| @systems_lead (opus) | requirements tree, interfaces, budgets, architecture | recommend: `brainstorming`, `writing-plans` |
| <add discipline leads from `config/disciplines.yml`> | | |

Start every session with `dev-docs/start-work-checklist.md` (~60s).

## Tool Stack

<If your project activates `electrical_lead` and/or `mechanical_lead`
(profile B or C), list the specific tools you use here so agent
sessions inherit the choice. Default recommendation:>

- **Electrical:** Atopile (schematic), KiCad pcbnew (layout), ngspice (sim), `kicad-cli` (CI verification)
- **Mechanical:** Build123d (parts/assemblies), ezdxf (drawings), CalculiX via FreeCAD FEM (analysis)
- **Glue:** STEP as cross-discipline interchange

See [dev-docs/architecture/external-tools.md](./dev-docs/architecture/external-tools.md)
for the full stack rationale, the four integration patterns, and the
rough edges. If your project picks differently (existing licenses,
supplier constraints), note the override here so future sessions see
the decision.

## Methodology

This project follows the five rules in [METHODOLOGY.md](./METHODOLOGY.md):

1. **Issues are canonical for status.** `sf-pr-rollup` is the sole label writer.
2. **Docs render from Issues.** Edit Issues, not AUTO sections.
3. **Wiki is one-way export.** Edit `dev-docs/`, not the wiki.
4. **Every requirement has a Verified By and Validated By.** Empty until populated; V&V matrix shows the gap.
5. **Every handoff leaves a breadcrumb.** `**Next action:**` on comments; `## Open questions if you stop mid-step` on briefs.

## Constraints

<Project-specific NFRs and budgets. Examples:>
- NFR-X.Y: <constraint>
- Mass budget: <kg or g>
- Power budget: <W>
- Cost target: <unit price>

## Project-specific FR Thresholds

<Pull thresholds out of the FR Issue bodies into here for quick reference,
or delete this section.>

## Build Sequence

See `config/stages.yml` for the milestone breakdown. Stages map 1:1 to
GitHub Milestones; `sf-pr-rollup` closes them when their UNs verify.

## Agent Write-back Protocol

**Canonical source of truth: GitHub Issues.** `dev-docs/` is a render target via
`sf-docs`; the wiki is a one-way export. Agents post evidence
as Issue comments. Agents do **not** edit `dev-docs/*` AUTO sections by hand,
and they do **not** move status labels — that is `sf-pr-rollup`'s job on PR merge.
See `dev-docs/architecture/doc-source-of-truth.md`.

Requirements are written to `dev-docs/architecture/requirement-format.md`
(user-voice UNs, EARS `shall` statements, one-number KPMs, directed
interface crossings). Read it before filing or editing any requirement.

Agents write results via `sf-comment`. **Never call the GitHub
API directly.** Every comment **must** end with a `**Next action:** ...` line.
Every agent comment carries a `via: @<agent>` footer.

```bash
# Verification example:
sf-comment verify-fr FR-X.Y \
  "<evidence summary>" \
  --next-action "<what next>"

# Validation example:
sf-comment validate-un UN-X \
  "<E2E summary>" \
  --next-action "<what next>"
```

## Remote Execution (optional)

<If your verification cycle runs on a remote target — Yoga, RPi, bench
fixture, hardware-in-loop rig — document the SSH pattern here. Delete
this section if everything runs locally.>

## Template Development Backlog (delete this section when you instantiate)

Notes for work on the template itself, kept here so they are not lost
between sessions. They were learned porting a 525-requirement project
(ReadShift, `Ajam1997/Notion-clone`) into this template in 2026-09/10.

### Requirement rules not yet in `requirement-format.md`

The format guide covers the first 14 rules. Decided since, and owed to
the guide:

- **Atomic requirements (R17).** Exactly one `shall` per FR, NFR and
  interface. A split keeps the original id on the first statement; new
  ids go at the end of the pillar; ids are never renumbered. Each child
  has its own status and evidence, so a half-built requirement becomes
  one shipped and one planned item. A list one `shall` covers stays one
  requirement.
- **Atomic user needs.** One first-person sentence ("I ..."), one goal.
  Independent goals split; example lists move down to child requirements.
- **Acceptance** is one to three checkable bullets.
- **Interface = pointer.** The interface Issue is one sentence naming
  both sides and the ICD file; the ICD holds the detail.
- **Interface links.** A requirement lists a crossing (`IF-x.y#k`) only
  when its statement is about the exchange itself: it names the other
  side or something on the wire (route, header, token, frame, response
  or error body). A requirement about what one side shows or stores has
  no link. Reverse lists (`Realised By` on the interface Issue,
  `Requirements:` under each ICD contract section) are generated, never
  hand-kept. A crossing with no realising requirement is a lint warning;
  it is how behaviour hiding in an ICD is found.
- **Test for "does this need an interface":** could the behaviour be
  shown with the other side switched off? If yes, no link. If a
  behaviour must survive a round trip, expect three requirements: the
  sender, the carrier and the keeper.

### Skills and tools to build

1. **Write-requirement skill.** Drafts or rewrites one UN, FR, NFR, IF
   or KPM to the format guide, including the split and link rules above.
   Source to adapt: ReadShift `prompts/rewrite-requirements.md`.
2. **Requirement lint tool.** Deterministic checks (one `shall`, EARS
   shape, known module names, acceptance count, UN sentence count,
   interface references, unrealised crossings, stage order). Source:
   the `lint` and `icd-links` subcommands of ReadShift
   `scripts/req_stage.py` and its tests.
3. **Requirement review skill.** The judgement pass a linter cannot do:
   status checked against the code, cited tests exercise the statement,
   duplicates merged, over- and under-splitting. Source: the per-pillar
   procedure in ReadShift `dev-docs/migration/README.md`.
4. **Before/after review page.** Renders a set of requirement changes as
   one HTML page for the owner to approve before Issues are edited.
   Source: ReadShift `scripts/req_diff_page.py`.
5. **Port-a-project skill.** How to bring an existing non-systems
   project into this template: extract candidate requirements from
   specs and code into staged fragments, merge and allocate ids, file
   Issues pillar by pillar, then run the correction pass. Source:
   ReadShift `dev-docs/migration/README.md`, `scripts/req_stage.py`
   (`merge`, `render`, `file`, `edit`) and the review record
   `dev-docs/SystemReviews/2026-10-01-requirements-review.md` (Part 5
   holds every rule with its reason).

Lessons the port skill must carry: decide the format before extracting
(the port filed 525 Issues, then rewrote them all); gate the first
pillar on a visual review by the owner; never hand-edit Issue bodies,
only through the staging script; keep fragments as the editable source
and the map as generated output.

The ReadShift sources live on branch `feat/port-corrections` until that
work merges.
