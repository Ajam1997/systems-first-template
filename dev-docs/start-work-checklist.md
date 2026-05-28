# Start-Work Checklist

Run this at the top of every session. ~60 seconds. Picks the right
agent and the right tool **before** the first invocation.

---

## 1. What kind of work is this session?

| Situation | Skill / agent to start with |
|---|---|
| (a) New idea, no design yet | `superpowers:brainstorming` → @systems_lead to file the UN |
| (b) UN exists, need a plan | @systems_lead → engineer brief |
| (c) Brief exists, ready to implement | The discipline lead named in the brief's `Owner:` line |
| (d) Resuming mid-flight work | SOP-B below |
| (e) Debugging a specific failure | `superpowers:systematic-debugging` → the relevant discipline lead |
| (f) About to claim "done" / merge | `superpowers:verification-before-completion` + @verification → PR |
| (g) Cross-cutting question / system review | @systemmaster |

## 2. Does this work deserve workspace isolation?

Multiple files, risk of half-done state, parallel to other work in the tree
→ `superpowers:using-git-worktrees`.

## 3. Are there 2+ independent investigations to do?

→ `superpowers:dispatching-parallel-agents`.

## 4. Which @agent will I hand this to?

Open `CLAUDE.md` and check the Agent Roster + Superpowers pairing table.
If you can't decide, default:

- **Design / interfaces / budgets / architecture** → @systems_lead
- **src/ implementation, software tests** → @software_lead
- **Embedded code, RTOS, peripheral drivers, HAL** → @firmware_lead
- **Schematics, PCB layout, SPICE, EMC pre-compliance** → @electrical_lead
- **CAD, FEA, drawings, tolerance analysis** → @mechanical_lead
- **DFM/DFA reviews, EVT/PVT plans, supplier qualification, AVL** → @manufacturing_lead
- **FCC/CE/UL roadmap, DoC, test-house engagement, BOM compliance** → @regulatory_lead
- **Per-commit verification** → @verification (or skip — `pr_rollup.py` handles labels)
- **Per-milestone E2E pass** → @validation
- **Cross-cutting / architecture review** → @systemmaster (operator-invoked only)

Which leads are active on *your* project depends on `config/disciplines.yml`.
Run `init_project.py --activate-profile A|B|C` to seed a starter set.

## 5. Will the next person resuming this session find a breadcrumb?

Per METHODOLOGY.md §5:

- Every `github_comment.py` call already requires `--next-action "..."` —
  the CLI fails fast if you forget.
- Every brief authored by @systems_lead must end with
  `## Open questions if you stop mid-step`, even if empty.
- PR descriptions reference the FR/UN they close and what changed.

If you're about to stop mid-step, fill the brief's "Open questions"
section *before* closing the session. Future-you will thank present-you.

---

## SOP-B — Resuming Mid-Flight Work

When picking up after a gap:

1. `git status` and `git log --oneline -10` — identify the in-flight feature
   and current branch.
2. Open `dev-docs/architecture/<feature>-engineer-brief.md` if one exists;
   otherwise the FR Issue body. Recover *intent*.
3. Read the FR Issue's most recent comments — especially the
   `**Next action:**` lines from @verification / @validation.
   Recover *state*.
4. Open the relevant test file or test plan. Recover the
   *implementation surface*. If returning to a failing test, invoke
   `superpowers:systematic-debugging`.
5. If still unclear: invoke @systemmaster with `"resume context for FR-X.Y"` —
   review brief lands at `dev-docs/SystemReviews/<date>-resume-FR-X.Y.md`.

You should *not* need to read `src/` (or `firmware/`, or `cad/`) to
figure out where you were. If you do, the brief / Issue comments are
missing a breadcrumb — fix the artifact before continuing.

---

## See Also

- [CLAUDE.md](../CLAUDE.md) → Agent Roster (skill pairings per agent)
- [doc-source-of-truth.md](architecture/doc-source-of-truth.md)
- [vv-matrix.md](architecture/vv-matrix.md)
- [METHODOLOGY.md](../METHODOLOGY.md)
