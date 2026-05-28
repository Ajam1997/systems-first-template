# Bootstrap Prompt — Systems-First Template

> **What this is.** A self-contained prompt for Claude Code. Paste it into
> a fresh Claude Code session opened at the root of a repo cloned from
> `systems-first-template`. Claude will read the methodology, scope the
> project with you, activate the right discipline leads, file the first
> user needs as GitHub Issues, draft `requirements/requirement-map.yml`,
> and run the full render chain so the docs / SysML model / V&V matrix
> are coherent before you write a line of code.
>
> **Why a prompt and not a script.** Bootstrapping a systems project is
> a *conversation*: the right discipline mix, the right phase model, the
> right first 8–12 user needs all depend on what you're building. A
> script can't ask the right follow-ups. Claude can.
>
> **Prerequisites.**
> - `gh auth status` shows you logged in
> - `python --version` is ≥ 3.10
> - `pip install -r requirements.txt` has run (PyYAML)
> - The repo has a GitHub remote (`git remote -v` shows `origin`)

---

## Paste everything below this line into Claude Code

You are bootstrapping a new project from the **systems-first-template**.
Your job is to take a freshly-cloned template repo and bring it to a
state where:

1. `config/disciplines.yml`, `config/stages.yml`, and
   `config/evidence-kinds.yml` describe *this* project
2. The right discipline-lead agents are active in `.claude/agents/`
3. GitHub Milestones exist for every stage
4. Labels are synced
5. The first 8–12 user needs are filed as GitHub Issues with the
   `UN`, `status:defined`, and milestone fields set
6. `requirements/requirement-map.yml` reflects those UNs (with FR/NFR/
   IF/KPM stubs decomposed under each)
7. `dev-docs/`, `model/system.sysml`, and the V&V matrix have been
   regenerated and are internally consistent
8. The operator has a clear list of next actions

You will do this **conversationally** with the operator. Follow the
sequence below. Stop and ask whenever a step needs a decision; never
guess a project's scope, market, or discipline mix.

### Step 0 — Ground yourself in the methodology

Before you ask the operator anything, read these files in order. Do
not skip any:

1. `README.md`
2. `METHODOLOGY.md` — the five rules
3. `dev-docs/architecture/doc-source-of-truth.md` — who writes what
4. `dev-docs/start-work-checklist.md` — agent selection
5. `config/README.md` — what the three config files do

Then read these to understand what you'll be generating:

6. `requirements/requirement-map.yml` (the template version — observe
   the shape, not the content)
7. `dev-docs/architecture/artifact-manifest.md` — non-text artifact
   format (only relevant if the project has CAD / PCB / firmware)
8. `dev-docs/architecture/vv-matrix.md` — V&V evidence format

Briefly tell the operator: *"I've read the template methodology. Five
questions before I start."*

### Step 1 — Scope the project (5 questions)

Ask the operator these five questions. Use one `AskUserQuestion` call
with all five, or ask in plain text — your choice. Do not proceed
until you have all five answers.

1. **What is the project, in one sentence?** ("A handheld inventory
   scanner for warehouse staff", "An offline photo workflow", etc.)
2. **Which disciplines are in scope?** Multi-select from: systems,
   software, mechanical, electrical, firmware, manufacturing,
   regulatory. (Systems is always on.) Map their answer to a profile:
   - {systems, software} → profile **A**
   - {systems, mechanical, manufacturing} → profile **B**
   - {systems, software, mechanical, electrical, firmware,
     manufacturing, regulatory} → profile **C**
   - Anything else → custom (you'll write `disciplines.yml` by hand
     after running profile A or B as a starting point)
3. **Roughly how many top-level user needs do you expect?** (Aim for
   6–12 for the first pass; you can add more later.)
4. **What target markets / certification regimes apply?** ("Hobby /
   none", "FCC Part 15B", "CE-RED + UL", "Medical / IEC 62304", etc.)
   This drives whether `regulatory_lead` activates.
5. **What's the GitHub repo slug?** (`owner/name`) Confirm by running
   `gh repo view` and reading the result back.

### Step 2 — Activate a profile

Based on the answers, run:

```bash
python scripts/init_project.py --activate-profile <A|B|C> --dry-run
```

Show the operator the plan. If it looks right, run again without
`--dry-run` to apply. This will:

- Overwrite `config/disciplines.yml` and `config/stages.yml` from the
  preset
- Sync `.github/labels.yml` to the repo (creates / updates / deletes)
- Create one Milestone per stage in `config/stages.yml`
- Copy the active discipline-lead agent packs from
  `.claude/agent-packs/<name>/` → `.claude/agents/`
- Run `scripts/generate_docs.py` to fill AUTO sections

If the project is genuinely custom (Step 1 answer 2 didn't fit A/B/C),
start from the closest profile, then hand-edit `config/disciplines.yml`
to add or remove leads, and re-run `python scripts/init_project.py`
(without `--activate-profile`).

### Step 3 — Tune evidence kinds

Open `config/evidence-kinds.yml`. Read it with the operator. Confirm
which `kind:` entries are valid for *this* project's V&V evidence.
For pure software projects, you usually only need `pytest`, `manual`,
`review`. For hardware, add `bench`, `dvt`, `evt`, `pvt`, `fea`, `emc`,
`regulatory`. Trim the rest.

Edit the file in place. Commit on the way out of this step.

### Step 4 — Draft user needs conversationally

This is the heart of the bootstrap. Walk the operator through their
project's user needs **one at a time**. For each:

1. Ask: *"What does the user / operator / customer need this system to
   do?"* Capture in one sentence.
2. Convert to a `UN-XXX` Issue body following the template at
   `.github/ISSUE_TEMPLATE/user-need.md`. The body must include:
   - **What:** one-paragraph need statement
   - **Why:** motivation
   - **Acceptance criteria:** bulleted, testable
   - **Verified By:** (empty for now — leaf FRs/NFRs/KPMs will populate
     it as they verify)
   - **Validated By:** (empty for now — `pr_rollup.py` populates when
     the parent milestone closes)
   - **Milestone:** which stage this UN lands in
3. Show the operator the drafted Issue body. Iterate until they're
   happy.
4. File it via `gh issue create --title "UN-XXX: <short>" --body-file
   <tempfile> --label "UN,status:defined" --milestone "<stage>"`.
5. Record the Issue number; you'll need it for `requirement-map.yml`.

Aim for 6–12 UNs on the first pass. If the operator wants more later,
they can run a smaller version of this loop in a follow-up session.

### Step 5 — Decompose UNs into FR / NFR / IF / KPM

For each UN filed in Step 4, ask the operator: *"How do we know we've
met this need?"* The answer is a small bundle of:

- **FRs** — functional requirements ("the system shall …")
- **NFRs** — non-functional ("response time < 100 ms", "RSS < 1.5 GB")
- **IFs** — interfaces it crosses (USB-C, Bluetooth LE, REST API)
- **KPMs** — measurable target values

File each as a GitHub Issue with the matching label
(`FR`/`NFR`/`IF`/`KPM`) and write the decomposition into
`requirements/requirement-map.yml`. The schema is:

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

# ... and so on for non_functional_requirements,
#     interface_requirements, kpms
```

Multi-parent FRs are first-class: an FR can support more than one UN.
Always write `fr_to_uns` as a list, even with one parent.

KPMs need extra fields when they aggregate (V-model rollup):

```yaml
kpms:
  KPM-1.1:
    title: "End-to-end latency"
    issue: 42
    unit: ms
    target_value: 100
    target_op: "<="
    aggregation: max          # one of: independent, sum, max, min
    aggregates_from: [KPM-2.1, KPM-2.2, KPM-2.3]
    margin_target: 0.20       # 20% margin below target
```

Leaf KPMs (no `aggregates_from`) get their measurements from either a
`KPM Rollup` comment on the Issue or a value in an artifact manifest.

### Step 6 — Run the render chain

With Issues filed and `requirement-map.yml` complete:

```bash
python scripts/generate_docs.py        # fills AUTO sections in dev-docs/
python scripts/kpm_rollup.py           # computes parent KPMs from leaves
python scripts/export_sysml.py         # writes model/system.sysml
python scripts/validate_artifacts.py   # CI gate — should be no-op pre-design
```

Diff each output. Show the operator. Commit:

```bash
git add config/ requirements/ dev-docs/ model/
git commit -m "feat: bootstrap UN tree, render chain green"
```

### Step 7 — Report state and next actions

End with a tight report: how many UNs filed, which Milestones exist,
which discipline leads are active, where the SysML model writes to,
and what the operator should do next. A good shape:

```
Bootstrap complete.

UNs filed:        UN-001 … UN-008  (8 issues, all status:defined)
Milestones:       Stage-1 … Stage-5
Active leads:     systems_lead, software_lead, mechanical_lead,
                  electrical_lead, firmware_lead, manufacturing_lead,
                  regulatory_lead
Render chain:     [ok] generate_docs  [ok] kpm_rollup  [ok] export_sysml
                  [ok] validate_artifacts (no artifacts yet)
Open questions:   (any genuine ambiguity surfaced during scoping)

Next action: open dev-docs/architecture/<feature>-engineer-brief.md
for the first FR and hand it to @<discipline>_lead.
```

---

## Notes on operator-driven steps you should NOT automate

- **`gh repo create`.** The operator creates the repo before pasting
  this prompt. You can verify it with `gh repo view` but you do not
  create it.
- **PAT generation.** If the wiki workflow needs to push, the operator
  generates a classic PAT with `repo` scope and adds it as the
  `WIKI_PUSH_TOKEN` secret. Do not paste tokens, do not write them to
  files, do not echo them.
- **Status label moves.** `pr_rollup.py` owns `verified` / `validated`
  transitions on PR merge. You never edit those labels.
- **Hand edits to AUTO sections.** Anything inside an `<!-- AUTO:key
  -->` sentinel is regenerated. If you find yourself wanting to edit
  the rendered table, edit the Issue or `requirement-map.yml` instead.

## When to stop and ask the operator

- The discipline mix doesn't fit a profile cleanly
- A UN's acceptance criteria aren't testable
- A KPM's aggregation strategy isn't obvious (sum vs max vs min)
- An interface crosses a discipline boundary you don't have a lead for
- The render chain fails — diagnose root cause, don't paper over
