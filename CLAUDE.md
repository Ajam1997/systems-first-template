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
