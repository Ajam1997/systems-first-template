# Architecture Contracts — Format Spec

The **system-level architecture contracts doc** defines the top-level
module decomposition of a system: what major chunks exist, what each
is responsible for, who owns it, and what flows between them.

It is the **vocabulary establishment** document — every ICD, every
engineer brief, every agent prompt references modules **by name**, and
those names need to live somewhere canonical before they're used
anywhere else.

> **Mental model:** if ICDs nail down *individual boundaries*
> (one signal, one API), the architecture contracts doc nails down
> the **module map itself**. Without it, three agents invent three
> different names for the same module and your system reads like
> three different projects.

---

## When you need one

You need an architecture contracts doc **before any ICD lands** and
**before any discipline lead authors a schematic, CAD assembly, or
firmware skeleton**. It is the foundation; everything else hangs off
it.

Trigger to author it: as soon as Stage 1 (System Architecture) UNs
are filed and the system has more than one discipline. For pure
software projects (Profile A), the architecture contract is usually
implicit in `src/` package structure and a `contracts.md` per feature
suffices.

For Profile B or C, the system-level contracts doc is mandatory
output of Stage 1.

---

## Where it lives

| File | Purpose |
|---|---|
| `dev-docs/architecture/system-architecture-contracts.md` | The top-level module map. One per system. Hand-authored by @systems_lead. |
| `dev-docs/architecture/<feature>-contracts.md` | Per-feature contract docs (lower level). Author when a feature's internal module decomposition matters and the system-level doc gets too coarse. |

Both are **design docs**, not status docs. They live in dev-docs/,
they're rendered to the wiki, and they're free-form prose (not under
AUTO sentinels). Edit freely.

---

## Required structure

### 1. Header

```markdown
# <System> — Architecture Contracts

**Owner:** @systems_lead
**Status:** living | frozen-at-PDR | frozen-at-CDR
**Last updated:** YYYY-MM-DD
**Companion ICDs:** see `requirements/interfaces/IF-*.md`
```

### 2. System overview (one paragraph)

A single paragraph: what the system is, what it does, what its
top-level success criterion is. Pulled from the README + UN-001
statement.

### 3. Module table (the load-bearing section)

A table, one row per top-level module. Required columns:

| Column | Purpose |
|---|---|
| **Module** | Canonical name. Used by every IF Issue, every brief. Title-case, short, no abbreviations that won't be obvious in 3 months. |
| **Responsibilities** | What this module owns, in plain English. 1–2 sentences. Should be possible to write the module's mission statement from this. |
| **Inputs** | What flows in. Each input links to its IF Issue (`[IF-X.Y](#)`). If the input is from outside the system (sensor, network, human), say so. |
| **Outputs** | What flows out. Same linking rule. |
| **Owner** | Single owning discipline (`firmware`, `electrical`, `mechanical`, `software`, `manufacturing`, `regulatory`). When a module spans disciplines, pick the *implementation* owner and note shared-design in a row below. |
| **Performance envelope** | NFRs / KPMs this module is on the hook for. Links to the relevant Issues. |

### 4. Cross-cutting concerns (optional but usually needed)

Some modules don't fit cleanly in the table:

- **Power supply** — every module is a "consumer"; document the rail map separately
- **Safety/interlock** — typically hardware-priority paths that bypass software
- **Compliance boundaries** — RF, ground reference, isolation
- **Real-time vs best-effort** — which modules have hard timing constraints

Each gets a sub-section after the table.

### 5. Cross-discipline boundaries (the ICD seed list)

For every pair of modules whose owners are in different disciplines,
enumerate the IF requirements that cross that boundary. This is the
list `@systems_lead` uses to know which ICDs to author next.

Example:

```markdown
| From → To | IFs | Notes |
|---|---|---|
| Main controller → Laser gimbal | IF-3.2 | Firmware → Mechanical (servo PWM) |
| Safety monitor → Laser driver | IF-2.2 | Electrical → Electrical (hardware AND gate) |
| Camera → Main controller | IF-2.1 | Electrical → Firmware (image data) |
```

### 6. Open questions

End with `## Open Questions if Frozen Mid-Authoring` — same convention
as engineer briefs. Future agents resuming need to see what's
deliberately undecided.

---

## When to split a module vs combine

Split when:

- The two halves have different **owning disciplines** (firmware vs electrical)
- The two halves have **independent failure modes** that affect different requirements
- One half is hardware-priority (cannot be bypassed by software) and the other is software-mediated
- The two halves can be **integrated separately** during DVT/EVT

Combine when:

- The two halves are always implemented together (one PCB, one firmware binary)
- They share state that's hard to expose across a boundary
- The boundary would be more confusing than the merger
- The split would create more ICDs than the boundary's value justifies

> **Heuristic:** if the split creates a new ICD that adds genuine
> contract clarity (signal direction, fail-safe behavior, timing
> budget), do the split. If the new ICD would just say "Module A
> reads Module B's state," combine.

---

## How modules relate to IF Issues

Every IF Issue references *two* modules from this doc — the source
and the destination. The IF Issue body should start with:

```markdown
**From:** <Module A> (owner: @<discipline>_lead)
**To:** <Module B> (owner: @<discipline>_lead)
**Spec:** requirements/interfaces/IF-X.Y.md
```

If you write an IF Issue and can't find the modules in the
architecture contracts doc, **add the modules first**. Don't invent
ad-hoc names in the IF Issue.

---

## Living doc vs frozen

The architecture contracts doc is **living until PDR**, then **frozen
at PDR** with changes thereafter requiring a documented change
request (a new doc at `dev-docs/SystemReviews/<date>-arch-change-<topic>.md`
that captures the rationale, affected ICDs, and discipline-lead
sign-offs).

States:

- `living` (Stage 1–2) — edit freely, the system is still being scoped
- `frozen-at-PDR` (Stage 3+) — changes require a system review
- `frozen-at-CDR` (Stage 4+) — changes require V&V replan + impact analysis

Update the `**Status:**` line in the header when the gate is passed.

---

## Authority and ownership

- **Authored by** @systems_lead.
- **Reviewed by** every active discipline lead before frozen-at-PDR.
- **Referenced by** every ICD (IF Issues), every engineer brief, every
  agent prompt that names a module.
- **Changed by** @systems_lead with discipline-lead concurrence after
  PDR.

The doc is not under AUTO regen — `generate_docs.py` does not touch
it. Hand-edits are the only way it changes.

---

## Anti-patterns

- **Reinventing module names per ICD.** Use the canonical name from
  this doc. If the name is bad, fix this doc and propagate.
- **One row per file rather than one row per module.** A module
  is a *conceptual unit of design*, not a code file. Many code
  files can belong to one module.
- **No outputs.** A module with no outputs is either a black hole
  (something is wrong) or the system boundary (and should be
  labeled as such).
- **Inputs/outputs that don't map to IF Issues.** Every flow either
  links to an IF or is internal to the module. Cross-module flow
  without an IF is an interface gap waiting to bite.
- **Mixing owners.** "Owned by firmware AND electrical" is two
  modules pretending to be one. Split or pick the lead-implementation
  owner.
- **Writing it after the first schematic.** The whole point is to
  precede design. If schematics already exist, the contracts doc
  should reflect them and you've accepted some integration risk.

---

## Worked example

See [`EXAMPLE-3d-printer-architecture-contracts.md`](EXAMPLE-3d-printer-architecture-contracts.md)
for a fully-filled example based on a hypothetical desktop FDM 3D
printer. The example covers all required sections + cross-cutting
concerns (thermal runaway protection, power rail map) + cross-discipline
boundaries.

---

## See also

- [doc-source-of-truth.md](doc-source-of-truth.md) — where every doc lives
- [vv-matrix.md](vv-matrix.md) — how IFs verify
- [external-tools.md](external-tools.md) — the tool stack each module's owner uses
- `requirements/interfaces/IF-*.md` — the per-boundary ICDs that reference modules from this doc
