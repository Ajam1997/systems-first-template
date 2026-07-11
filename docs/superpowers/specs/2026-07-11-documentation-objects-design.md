# Documentation Objects — Design Spec (Phase 2)

**Date:** 2026-07-11
**Status:** Approved (brainstormed with Alex; records the validated design)
**Builds on:** PHOTONFORGE marketplace phase 1
(`2026-07-10-systems-first-marketplace-design.md`) — systems-first-core
v0.1.2 at `Ajam1997/PHOTONFORGE`.
**Scope:** The documentation object hierarchy from the 2026-07-10 doc-system
brain dump: House Style, templates, conventions, glossary, and the
document-class/medium model — delivered across **two releases** (v0.2.0
markdown-side, v0.3.0 HTML machinery) from **this one spec**.
**Out of scope** (separate small specs later): teaching `sf-init` the plugin
world, porting `sf-gates` from kicad-pcba, absorbing photo-workflow's
doc-integrity scripts into the package.

## 1. Problem

Every systems-first project accumulates documentation rules — banner
formats, ID syntax, "PR touching X must update doc Y", term definitions —
but they live as scattered prose (photo-workflow:
`doc-maintenance-protocol.md`, `pr-conventions.md`, `ci-policy.md`,
`doc-source-of-truth.md`). Prose conventions decay into suggestions; new
document types get invented ad hoc; review decisions live in chat
transcripts instead of a durable archive. kicad-pcba independently proved
the remedies (templates/ directory, profile.json conventions-as-data,
self-contained HTML review docs, machine-checked gates with recorded
sign-offs) but only for PCB work. Phase 2 generalizes them.

## 2. Design principles (locked)

- **Plugin = engine, repo = policy.** systems-first-core ships the skills,
  CLIs, and a seed; each project owns its actual House Style instance as
  repo files under `dev-docs/house-style/`.
- **Document class determines medium:**

  | Class | The output is | Medium |
  |---|---|---|
  | **review-critical** | a human decision | interactive single-file HTML: input affordances, then publish-and-lock |
  | **working** | shared understanding, edited by agents + humans | markdown (the current system) |
  | **report** | a rendering of data; nobody hand-edits | code-driven graphical single-file HTML |

- **Conventions are data with a per-rule ratchet.** Each convention carries
  `enforce: blocking | advisory`. New rules start advisory; a project flips
  them to blocking once clean. Checked in CI, not just documented.
- **Cited, never duplicated.** Templates cite conventions by id; the
  glossary is the single home for definitions; `house-style.md` is an index,
  not a copy.
- **Self-contained HTML always.** Every generated HTML document is one file
  with zero CDN/network dependencies — viewable offline from `file://`
  indefinitely. That property is what makes the decision archive durable.
- **Single-operator decisions (explicit assumption).** Sign-off quorum is
  one human (Alex). The decisions index schema carries `decided_by` so a
  multi-reviewer model later is additive, not rework.

## 3. The object model (per-project policy instance)

```
dev-docs/house-style/
  house-style.md        # top-level object: voice/tone rules, doc lifecycle,
                        #   INDEX of templates, conventions, and doc classes
  doc-classes.yml       # doc type → class (review-critical|working|report),
                        #   medium, lifecycle states
  glossary.yml          # system bible: term → definition (+ aliases, scope)
  conventions/*.yml     # one convention per file (schema below)
  templates/*.md        # one document template per doc type
```

### 3.1 Convention file schema

```yaml
id: supersession-banner                # kebab-case, unique in the repo
title: Superseded docs carry a banner and move to Archive/
enforce: blocking                      # or advisory — the ratchet
applies_to: ["dev-docs/**/*.md"]       # glob scope
prose: |
  A superseded doc gets a top-of-file banner and moves to
  dev-docs/Archive/ at the same relative path. History is preserved,
  never load-bearing. (The why + how, for agents and humans.)
checks:                                # zero or more machine checks
  - type: regex_required_if
    when_contains: "SUPERSEDED"
    pattern: '^> \*\*SUPERSEDED \(\d{4}-\d{2}-\d{2}, PR #\d+\):\*\*'
```

**Check-type vocabulary (fixed, implemented in the package rules engine):**

| type | Checks |
|---|---|
| `regex_required` | every file matching `applies_to` matches `pattern` |
| `regex_required_if` | files containing `when_contains` must match `pattern` |
| `regex_forbidden` | no file matching `applies_to` matches `pattern` |
| `frontmatter_required` | required keys present in YAML frontmatter |
| `paired_paths` | PR-mode only: change touching glob A must also touch glob B (the docs-impact matrix, data-fied) |
| `locked_files` | PR-mode only: no change may touch paths listed in the decisions index (§6) |
| `id_format` | tokens matching `token_pattern` (e.g. `(FR\|NFR\|IF\|KPM)-\d`) must match full `pattern` (requirement-ID syntax) |

A convention with zero `checks` is legitimate — judgment-only rules still
live in the same system, they just aren't machine-enforced.

### 3.2 doc-classes.yml

```yaml
classes:
  review-critical:
    medium: interactive-html
    lifecycle: [draft, in-review, decided, superseded]
  working:
    medium: markdown
    lifecycle: [living, superseded]
  report:
    medium: generated-html
    lifecycle: [current]        # regenerated, never edited
doc_types:
  design-spec:      {class: review-critical, template: design-spec}
  design-review:    {class: review-critical, template: design-review}
  system-review:    {class: review-critical, template: system-review}
  trade-study:      {class: review-critical, template: trade-study}
  adr:              {class: working, template: adr}
  interface-spec:   {class: working, template: interface-spec}
  engineer-brief:   {class: working, template: engineer-brief}
  impl-plan:        {class: working, template: impl-plan}
  kpm-dashboard:    {class: report, generator: sf-report}
  verification-run: {class: report, generator: sf-report}
```

(Projects reclassify freely — this is policy data. Note: markdown drafts of
review-critical docs are normal; the class governs the **review and archive**
medium, not the drafting medium.)

### 3.3 Templates

Markdown files with frontmatter:

```yaml
---
name: adr
doc_type: adr
output_path: "dev-docs/architecture/adr/NNNN-<slug>.md"
conventions: [supersession-banner, requirement-id-format]   # cited by id
---
# <Title>
...skeleton with guidance comments...
```

### 3.4 Glossary

`glossary.yml` (`term`, `definition`, optional `aliases`, `scope`) rendered
into `dev-docs/glossary.md` by `sf-docs` via a new `AUTO:glossary` section —
the existing AUTO machinery, no new render pipeline. Agents load the YAML
directly when they need definitions.

## 4. Engine — v0.2.0 (markdown side)

### 4.1 `house-style` skill (systems-first-core) — the router

- Reads only `house-style.md`'s index, then loads the ONE template + its
  cited conventions needed for the doc at hand (progressive disclosure).
- If `dev-docs/house-style/` is absent: offers to instantiate the plugin's
  seed (§7).
- Trigger: any time an agent is about to author or substantially revise a
  dev-doc.

### 4.2 `template-writer` skill (systems-first-core) — the meta-skill

Mints a new template when a doc type has none: follows the template-format
convention, cites existing conventions rather than restating, registers the
new type in `house-style.md`'s index and `doc-classes.yml`. Never generates
code; templates are markdown + frontmatter only.

### 4.3 `sf-style` CLI (systems-first package) — the enforcement

```
sf-style                      # full-repo check, all conventions
sf-style --pr-mode <base>     # diff-aware: paired_paths/locked_files vs base
sf-style --rule <id>          # single rule (debugging a ratchet flip)
```

- Reads `dev-docs/house-style/conventions/*.yml` + the decisions index.
- Exit nonzero **only** on blocking violations; advisory violations print a
  report table. Summary always lists rule id, enforce level, violation count.
- Missing `house-style/` → green no-op with a notice (the wiki-publish
  opt-in pattern).
- CI: one added step in the docs-integrity workflow
  (`sf-style --pr-mode "origin/$BASE"`), inherited by instantiated projects
  via the template repo.

### 4.4 `sf-docs` addition

`AUTO:glossary` renderer sourced from `glossary.yml` → `dev-docs/glossary.md`.
Follows every existing AUTO-section rule (hand edits lose).

## 5. Engine — v0.3.0 (HTML machinery)

### 5.1 `sf-review` CLI — interactive review docs + decision capture

```
sf-review render <doc.md> -o <doc.html>   # markdown draft → interactive single-file HTML
sf-review serve <doc.html>                # local decision server (127.0.0.1)
sf-review lock <doc> --decision <id>      # freeze + hash + index (also invoked by serve)
```

- **render:** wraps the draft in the review chrome: metadata header, section
  anchors, per-section comment affordances, and a decision panel
  (Approve / Request changes / notes). Single file, inline CSS/JS, no
  network. Template chrome ships in the package.
- **serve:** kicad-pcba `dashboard.py` pattern — tiny stdlib HTTP server;
  the human opens the doc, interacts; the decision panel POSTs a structured
  decision (verdict, notes, per-section comments, `decided_by`, timestamp)
  which the server writes to the decisions index and prints to stdout so a
  waiting agent can proceed. Request-changes returns the comments as the
  work list.
- **lock (publish):** on Approve — re-render the doc with the decision,
  decider, and timestamp baked into the chrome; write to
  `dev-docs/decisions/YYYY-MM-DD-<slug>.html`; record
  `{path, sha256, decision, decided_by, date, source_doc}` in
  `dev-docs/decisions/index.yml`; the `locked_files` convention (blocking)
  then makes any later modification a CI failure. Tamper-evident via hash
  (artifact-manifest pattern), enforced via sf-style.

### 5.2 `sf-report` CLI — code-driven graphical reports

```
sf-report build [kpm|verification|all]    # durable single-file HTML → dev-docs/reports/
```

v1 reports: **KPM dashboard** (targets/current/margins, trend from Issue
history) and **verification/gate status** (V&V coverage). Reads the same
sources `sf-docs` and `sf-kpm-rollup` already read. Inline-SVG charts —
self-contained, no JS chart libraries fetched. CI regenerates on the same
triggers as regen-docs; commits under `dev-docs/reports/`.

### 5.3 Wiki interplay

The wiki remains markdown-only. HTML decisions and reports stay in the repo
(the durable archive); the glossary, decision **index** (rendered stub table
linking to the HTML artifacts), and report stubs publish to the wiki like
any other dev-doc.

## 6. Decision lifecycle (end-to-end)

1. Agent drafts a review-critical doc in markdown from its template
   (`house-style` skill).
2. `sf-review render` + `serve`; the human reviews in the browser.
3. **Request changes** → structured comments back to the agent → revise →
   re-render (stays `in-review`).
4. **Approve** → `lock`: frozen HTML + hash + index entry; state `decided`.
   The markdown source gets a supersession-style pointer banner to the
   locked artifact.
5. A later reversal never edits the locked doc: a new review supersedes it
   (index entry gains `superseded_by`), preserving the archive.

## 7. Seed (ships in systems-first-core, instantiated by the house-style skill)

- `house-style.md` — generic voice/lifecycle rules + index of everything below.
- `doc-classes.yml` — the §3.2 table.
- Templates (the proven photo-workflow set): working class — `adr`,
  `interface-spec`, `engineer-brief`, `impl-plan`; review-critical class —
  `design-spec`, `design-review`, `system-review`, `trade-study`.
- Starter conventions (extracted from photo-workflow's prose, generalized):
  `supersession-banner`, `auto-sections-never-hand-edited`
  (regex_forbidden on sentinel edits outside sf-docs commits — advisory),
  `requirement-id-format`, `docs-impact-matrix` (paired_paths — **seeded
  empty**; each project fills its own matrix), `locked-decisions`
  (locked_files, blocking), `template-format` (frontmatter_required).
- `glossary.yml` — seeded with the systems-first method terms (UN, FR, NFR,
  IF, KPM, ICD, ADR, V&V, HB-x, SOP-B, stage gate…); projects add their own.

## 8. Pilot (photo-workflow, same playbook as phase 1)

Extract, don't invent: photo-workflow's scattered conventions move into
`dev-docs/house-style/` — the docs-impact matrix becomes `paired_paths`
data; banner/ID/AUTO rules become convention files; the glossary seeds from
CLAUDE.md's floating terms. The prose docs shrink to pointers. v0.3 pilot:
one real design review (first candidate: any phase-3 change-management
design) goes through render → serve → decide → lock.

## 9. Acceptance criteria

**v0.2.0**
1. Package rules engine: unit tests per check type; marketplace CI dogfoods
   `sf-style` against the plugin's own seed (seed templates must satisfy
   seed conventions).
2. photo-workflow pilot: extracted conventions run green via
   `sf-style --pr-mode` in docs-integrity CI; at least one rule flipped to
   blocking demonstrably fails a test PR containing a seeded violation.
3. `sf-docs` renders `AUTO:glossary`; wiki publishes it.
4. house-style + template-writer skills invocable; router loads only the
   needed template + conventions (spot-check context size).

**v0.3.0**
5. A real review-critical doc completes the full lifecycle (§6) on
   photo-workflow: interactive review in browser, decision captured by the
   local server, locked artifact + hash in `decisions/index.yml`.
6. A PR touching a locked file fails CI via the `locked-decisions` rule.
7. `sf-report build kpm` produces a self-contained HTML dashboard with
   correct values (cross-checked against `sf-kpm-rollup` output); renders
   from `file://` with network disabled.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Check-type vocabulary too weak for a real convention | Vocabulary is versioned with the package; add types in minor releases. Judgment-only conventions (zero checks) are first-class, so nothing is forced into regex |
| Decision server is a new interactive surface (port conflicts, orphaned processes) | stdlib-only, localhost-only, single-doc lifetime, `--port` override; kicad-pcba's dashboard already proved the pattern on this machine |
| Locked-file guard blocks legitimate mechanical changes (e.g. repo-wide moves) | Supersession flow (§6.5) is the sanctioned path; emergencies use the ratchet (flip to advisory in the same PR, visibly) |
| AUTO-section hand-edit check can't see commit authorship in pr-mode | Ship it advisory; it's a nudge, sf-docs regen remains the real defense |
| Seed conventions drift from photo-workflow's evolved practice | Pilot (§8) IS the extraction; the seed generalizes from what the pilot proves |
