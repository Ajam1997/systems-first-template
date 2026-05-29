# Bootstrap Prompt — Systems-First Template

> **What this is.** A copy-and-fill scoping worksheet *and* a self-contained
> prompt for Claude Code, in one file. The operator fills Section A
> (project scoping) by hand, commits the filled copy as the project's
> permanent inception record, then pastes the whole file into a fresh
> Claude Code session. Claude reads Section A as input and executes
> Section B end-to-end.
>
> **Why a worksheet first.** The operator's answers to the five scoping
> questions are the *origin story* of the project. They deserve a
> dated, named artifact in the repo — "this is how it started" — not
> a chat scrollback that gets lost when the session ends. Filling the
> form by hand also front-loads the operator's thinking before any
> agent gets involved.
>
> **Stuck on a question?** See [bootstrap-faq.md](bootstrap-faq.md) —
> reference answers for every field in Section A and every decision
> point in Section B.
>
> **New to the template?** See
> [`dev-docs/getting-started.md`](../dev-docs/getting-started.md) for
> the zero-to-first-bootstrap walkthrough including VS Code, Claude
> Code, gh CLI, classic-PAT generation, and wiki setup.

---

## How to use this file

1. **Copy** `prompts/bootstrap.md` to `prompts/bootstrap_<your-name>.md`
   (e.g. `prompts/bootstrap_alex.md`). One filled copy per operator
   who runs a bootstrap; if a second operator re-bootstraps later,
   they make their own copy.
2. **Fill** Section A below. Replace every `<<fill in: ...>>` sentinel
   with a real answer. Don't delete the headers.
3. **Commit** the filled copy:
   ```bash
   git add prompts/bootstrap_<your-name>.md
   git commit -m "chore(inception): scoping worksheet by <your-name>"
   git push
   ```
   This is the project's inception record. It does not get deleted
   after the bootstrap runs.
4. **Paste** the entire filled file into a new Claude Code session
   opened at the repo root. Claude reads Section A, refuses if any
   `<<fill in: ...>>` sentinel remains, and executes Section B.

---

## SECTION A — Project scoping worksheet  *(operator fills this)*

### A1. Project, in one sentence

Name **who** uses it, **what** it does, and **why** (or a defining
constraint). Skip implementation. See FAQ Q1 for examples.

> **Project:** `<<fill in: one sentence>>`

### A2. Disciplines in scope → profile

Tick the disciplines that apply. Systems is always on.

- [ ] systems  *(always on)*
- [ ] software
- [ ] mechanical
- [ ] electrical
- [ ] firmware
- [ ] manufacturing
- [ ] regulatory

Then declare the matching profile:

> **Profile:** `<<fill in: A | B | C | custom>>`

Mapping (see FAQ Q2 for the full table):
- `{systems, software}` → **A** (software-only)
- `{systems, mechanical, manufacturing}` → **B** (mechanical / hardware-led)
- All seven → **C** (mixed-discipline IoT)
- Anything else → **custom** (Claude will start from the closest profile and hand-edit `disciplines.yml`)

> **If custom, name the closest base profile:** `<<fill in: A or B, or write 'n/a'>>`

### A3. Top-level user-need count target

Aim for 6–12 on this first pass. You can add more later.

> **Target UN count:** `<<fill in: integer between 6 and 12>>`

### A4. Target markets / certification regimes

Which markets do you intend to sell into, and what compliance regimes
apply? See FAQ Q4 for the standards table.

> **Markets / regimes:** `<<fill in: e.g. "hobby / personal use only" OR "FCC Part 15B + CE-RED" OR "UL + IEC 60825 Class 2 laser">>`

### A5. GitHub repo slug

`owner/name`. Verify with `gh repo view <slug>` before pasting.

> **Repo slug:** `<<fill in: owner/name>>`

### A6. Operator + date  *(inception provenance)*

> **Operator:** `<<fill in: your GitHub handle>>`
> **Date filled:** `<<fill in: YYYY-MM-DD>>`

---

## SECTION B — Execution instructions  *(Claude runs this)*

> Claude, you are bootstrapping a new project from the systems-first
> template. The operator has filled Section A above with this
> project's scoping answers. **Read Section A as input.** Do not
> re-ask the operator the questions in Section A — they already
> answered them.

### B.0 — Validate Section A

Before doing anything else:

1. Re-read Section A from the prompt you were pasted.
2. If any field still contains a `<<fill in: ...>>` sentinel, **stop**
   and tell the operator which fields are missing. Do not proceed.
3. If A5 (repo slug) is filled, run `gh repo view <slug>` and read
   the result back to confirm the repo exists and you're in its
   clone.
4. Briefly acknowledge: *"I have your scoping answers from Section A
   of bootstrap_<operator>.md. Starting bootstrap for `<project>` as
   profile `<profile>`."*

### B.1 — Ground yourself in the methodology

Read these files in order. Do not skip any:

1. `README.md`
2. `METHODOLOGY.md` — the five rules
3. `dev-docs/architecture/doc-source-of-truth.md` — who writes what
4. `dev-docs/start-work-checklist.md` — agent selection
5. `config/README.md` — what the three config files do
6. `requirements/requirement-map.yml` (template version — observe shape)
7. `dev-docs/architecture/artifact-manifest.md` *(skip if profile A)*
8. `dev-docs/architecture/vv-matrix.md` — V&V evidence format

### B.2 — Activate the profile

Using Section A's profile answer, run:

```bash
python scripts/init_project.py --activate-profile <A|B|C> --dry-run
```

Show the operator the plan. If it looks right, run again without
`--dry-run`. This will:

- Overwrite `config/disciplines.yml` and `config/stages.yml` from the preset
- Sync `.github/labels.yml` to the repo
- Create one Milestone per stage
- Copy active discipline-lead agent packs from `.claude/agent-packs/<name>/` → `.claude/agents/`
- Run `scripts/generate_docs.py` to fill AUTO sections

For **profile = custom**, start from the closest base profile (A6
field "closest base profile"), then hand-edit `config/disciplines.yml`
to add/remove leads, then re-run `init_project.py` without
`--activate-profile`.

For **profile sensitive to A4 markets**: if A4 names any
certification regime (FCC, CE, UL, IEC 60825, IEC 62368, etc.) and
the profile doesn't already include `regulatory_lead`, flag it to
the operator and offer to activate it.

### B.3 — Tune evidence kinds

Open `config/evidence-kinds.yml`. Trim to what this project will
actually produce (see FAQ Step 3). Commit on the way out.

### B.4 — Draft user needs conversationally

Walk the operator through A3 user needs **one at a time**. For each:

1. Ask: *"What does the user / operator / customer need this system
   to do?"*
2. Convert to a `UN-XXX` Issue body following
   `.github/ISSUE_TEMPLATE/user-need.md`. The body must include
   **What**, **Why**, **Acceptance criteria** (bulleted, testable),
   **Verified By:** (empty), **Validated By:** (empty), **Milestone:**.
3. Show the operator the drafted body. Iterate until they're happy.
4. File via `gh issue create --title "UN-XXX: <short>" --body-file
   <tempfile> --label "UN,status:defined" --milestone "<stage>"`.
5. Record the Issue number for the requirement map.

Stop at A3's target count. If the operator wants more later they'll
run a smaller bootstrap variant in a follow-up session.

### B.5 — Decompose UNs into FR / NFR / IF / KPM

For each UN, ask: *"How do we know we've met this need?"* File each
FR / NFR / IF / KPM as a labeled Issue and write the decomposition
into `requirements/requirement-map.yml`. Schema:

```yaml
user_needs:
  UN-001:
    title: "..."
    issue: 12
    functional_requirements: [FR-1.1, FR-1.2]
    non_functional_requirements: [NFR-1.1]
    interface_requirements: [IF-1.1]
    kpms: [KPM-1.1]

functional_requirements:
  FR-1.1:
    title: "..."
    issue: 13
    fr_to_uns: [UN-001]      # supports multi-parent — always a list
    kpms: [KPM-1.1]

kpms:
  KPM-1.1:
    title: "End-to-end latency"
    issue: 42
    unit: ms
    target_value: 100
    target_op: "<="
    aggregation: max          # independent | sum | max | min
    aggregates_from: [KPM-2.1, KPM-2.2]
    margin_target: 0.20
```

See FAQ Step 5 for aggregation strategy and margin guidance.

### B.5.5 — Rewrite CLAUDE.md for this project

The template ships a `CLAUDE.md` written for the upstream PHOTONForge
project. Once UNs, FRs, NFRs, and KPMs exist, rewrite it for *this*
project so future Claude Code sessions inherit the correct context.

Use Section A's answers plus the live requirement tree:

- **Context paragraph** — one paragraph from A1 (project sentence)
  and A4 (markets/regimes). Name the host hardware if relevant.
- **Agent Roster** — table of the active leads from
  `config/disciplines.yml` (post-Step B.2 state). One row per lead,
  with the same Superpowers pairing column the template uses.
- **Architecture Decisions** — 2–4 bullets capturing decisions the
  operator made implicitly during Section B.4/B.5 (e.g. "monolithic
  vs microservice," "RTOS choice deferred to firmware lead," "no GPU
  paths"). Leave blank if none yet — `@systems_lead` will fill it as
  briefs land.
- **Constraints** — every NFR with a hard threshold goes here as a
  one-liner (e.g. `NFR-2.1: 100% offline at runtime`).
- **FR Thresholds** — every FR that names a specific measurable
  threshold in its acceptance criteria (e.g.
  `FR-1.3: dHash Hamming distance <= 2`).
- **KPMs** — bullet list of every KPM with its target and owner
  discipline.
- **Conventions** — language version, linter, test framework, naming
  conventions. Reasonable defaults if the operator hasn't specified.
- **Project Layout** — `src/`, `tests/`, `scripts/`, `deploy/`,
  `firmware/`, etc. — whichever apply given the active disciplines.
- **Build Sequence** — one bullet per stage from
  `config/stages.yml`, with the active discipline lead in parens.
- **Agent Write-back Protocol** — copy from the template's
  CLAUDE.md unchanged. This is universal.

Show the operator a diff before writing. Commit alongside the
requirement-map.yml in B.6.

If the operator wants to defer CLAUDE.md rewriting until after they
see the bootstrap in action, that's fine — file an Issue
("rewrite CLAUDE.md for this project") with the `chore` label and
move on. The template's CLAUDE.md is non-blocking; it just produces
inherited-from-template context until rewritten.

### B.6 — Run the render chain

```bash
python scripts/generate_docs.py
python scripts/kpm_rollup.py
python scripts/export_sysml.py
python scripts/validate_artifacts.py
```

Diff each output. Show the operator. Commit:

```bash
git add config/ requirements/ dev-docs/ model/
git commit -m "feat: bootstrap UN tree, render chain green (per bootstrap_<operator>.md)"
```

Note the commit message references the filled bootstrap file —
preserves the inception trail.

### B.7 — Report state and next actions

Format:

```
Bootstrap complete (per prompts/bootstrap_<operator>.md, dated <A6 date>).

Project:          <A1 sentence>
Profile applied:  <A2 profile>
UNs filed:        UN-001 … UN-<N>  (<count> issues, all status:defined)
Milestones:       Stage-1 … Stage-<N>
Active leads:     <list>
Render chain:     [ok] generate_docs  [ok] kpm_rollup  [ok] export_sysml
                  [ok] validate_artifacts
Open questions:   <any genuine ambiguity surfaced during scoping>

Next action:      open dev-docs/architecture/<feature>-engineer-brief.md
                  for the first FR and hand it to @<discipline>_lead.
```

---

## Operator-owned steps Claude does NOT do

- **`gh repo create`** — operator creates the repo before copying this file.
- **PAT generation** — operator handles classic-PAT generation for the wiki workflow. Claude does not write tokens to files or echo them.
- **Status label moves** — `pr_rollup.py` owns `verified` / `validated`. Claude does not touch them.
- **Hand edits inside AUTO sentinels** — regenerated by `generate_docs.py`. Edit the Issue, not the rendered table.

## When Claude should stop and ask

- A UN's acceptance criteria aren't testable
- A KPM's aggregation strategy isn't obvious (sum / max / min)
- An interface crosses a discipline boundary with no active lead
- The render chain fails — diagnose root cause, don't paper over
- Section A's profile (A2) and market answer (A4) imply different discipline mixes (e.g. profile A but A4 names FCC)
