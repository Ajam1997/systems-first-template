# Doc Source-of-Truth — Where Things Live

The precedence rule for the project's documentation surface. **Read once
at project start; refer back whenever a writer collision feels possible.**

---

## Precedence Rule (resolves conflicts in one line)

> When a fact appears in more than one place, **Issues win**.
> Docs reflect Issues. The wiki reflects docs. Nothing reflects back upstream.

---

## Where Does X Live?

| Thing | Canonical location | Rendered into | Notes |
|---|---|---|---|
| FR / UN / NFR / IF / KPM **status** (`defined`, `in-progress`, `verified`, `validated`) | GitHub Issue labels | `dev-docs/living-user-needs.md`, `dev-docs/architecture.md`, `dev-docs/roadmap.md`, `dev-docs/kpm-dashboard.md` AUTO sections | Only `scripts/pr_rollup.py` writes `verified` / `validated`. Agents post comments via `github_comment.py` but never move labels. |
| FR / UN / NFR acceptance criteria, KPM target | GitHub Issue body | Architecture doc tables | Edit the Issue body, then run `python -m scripts.generate_docs`. |
| Decomposition (UN → FR/NFR/IF/KPM) | `requirements/requirement-map.yml` | Living-user-needs.md AUTO section | Hand-edited; not regenerated from Issues. |
| Interface details (ICDs, pinouts, protocols, drawings) | `requirements/interfaces/IF-X.Y.md` | n/a (hand-authored) | Free-form markdown for cross-discipline boundaries. |
| Stage / Milestone definition | GitHub Milestones | `dev-docs/roadmap.md` AUTO section | Created from `config/stages.yml` on project setup. `pr_rollup.py` closes milestones when their UNs verify. |
| Budget allocations | KPMs in `requirements/requirement-map.yml` with `aggregation: sum`; allocations are child KPMs | Architecture doc KPM table + rollup comments on parent KPM Issues | A budget is just an aggregated KPM. `scripts/kpm_rollup.py` posts computed values. |
| Architecture contracts (module interfaces) | `dev-docs/architecture/<feature>-contracts.md` | n/a (hand-authored) | Design docs, not status docs. Edit freely. |
| Engineer briefs (per-feature plans) | `dev-docs/architecture/<feature>-engineer-brief.md` | n/a | Authored by @systems_lead, consumed by the assigned discipline lead. Must include "Open questions if you stop mid-step". |
| Research / scratch notes | `dev-docs/research/*.md` | n/a | Free-form. Not in AUTO regen. |
| Verification / validation evidence | GitHub Issue comments via `scripts/github_comment.py` | n/a | Reports as Issue comments, not as `docs/VerificationReports/*.md` files. |
| Test plans (DVT/EVT/PVT, bench, simulation) | `verification/<phase>/<plan>.md` | Referenced from V&V matrix | Hand-authored procedures + result links. |
| Non-text engineering artifacts (CAD/PCB/firmware-binaries) | external vault / git-LFS, with manifest in `artifacts/<discipline>/` | n/a | Manifest carries link, SHA-256, reviewer, snapshot PNG. The actual file lives elsewhere. |
| System reviews | `dev-docs/SystemReviews/<date>-<topic>.md` | n/a | Operator-invoked deep reviews (@systemmaster). |
| Operator's offline memory aid | GitHub Wiki | one-way exported from `dev-docs/` via `scripts/migrate_wiki.py` | Wiki is downstream of dev-docs. Direct edits to the wiki survive only if front-matter-tagged `WIKI:LOCAL-ONLY`. |

---

## AUTO Sentinels — How Hand Edits Survive Regen

`scripts/generate_docs.py` only replaces content between sentinels:

```
<!-- AUTO:key_name -->
...generated content...
<!-- /AUTO:key_name -->
```

Anything **outside** these markers is preserved. If you need to add
context to a living doc, write it outside the sentinels.

If a needed edit doesn't fit outside the sentinel, the *Issue* is the
wrong source — fix the Issue, not the doc.

Recognized AUTO keys in this template:

| Key | Doc |
|---|---|
| `user_needs` | living-user-needs.md |
| `fr_table` | architecture doc |
| `nfr_table` | architecture doc |
| `if_table` | architecture doc |
| `kpm_table` | architecture doc + kpm-dashboard.md |
| `vv_matrix` | architecture doc |
| `roadmap` | roadmap.md |

Each is opt-in: the renderer silently skips a key whose sentinel isn't
in the document. Add sentinels to your project's docs only for the
sections you want auto-managed.

---

## What Agents May Write

| Actor | May write | May not write |
|---|---|---|
| @verification | Issue comments (with `Next action:` and `via:` footers) via `github_comment.py` | `dev-docs/*` AUTO sections; status labels |
| @validation | Issue comments via `github_comment.py`; `verification/*` test plans + result links | `dev-docs/*` AUTO sections; status labels; `src/`; `tests/test_*` |
| @systems_lead | `requirements/*`, `requirements/interfaces/*`, `dev-docs/architecture/*`, `CLAUDE.md` | Status labels; AUTO sections of living docs |
| @software_lead | `src/`, `tests/`, PR descriptions | Status labels; AUTO sections; non-software discipline artifacts |
| @firmware_lead | `firmware/`, `tests/firmware/`, `artifacts/firmware/*.md` manifests, `verification/hil/*` test plans | Status labels; other disciplines' content |
| @electrical_lead | `artifacts/electrical/*.md` manifests + snapshots, `verification/bench/*` and `verification/simulation/*` (SPICE) test plans, BOM CSVs | Status labels; other disciplines' content |
| @mechanical_lead | `artifacts/mechanical/*.md` manifests + snapshots, `verification/simulation/*` (FEA) and `verification/bench/*` test plans, BOM CSVs | Status labels; other disciplines' content |
| @manufacturing_lead | `artifacts/manufacturing/*` (AVL, supplier audits, fixture manifests), `verification/dfm/*`, `verification/evt/*`, `verification/pvt/*` | Designs themselves; status labels |
| @regulatory_lead | `artifacts/regulatory/*` (cert roadmap, DoCs, technical file, per-standard plans), `verification/inspection/bom-compliance-*` | Designs themselves; status labels |
| `pr_rollup.py` (workflow) | `verified` / `validated` labels on PR merge; closes milestones | Anything else |
| `generate_docs.py` (workflow) | AUTO sections of the four living docs | Anything outside AUTO sentinels |
| `kpm_rollup.py` (workflow) | KPM rollup comments on parent KPM Issues | Status labels; AUTO sections; non-KPM Issues |
| `export_sysml.py` (workflow) | `model/system.sysml` | Anything else |
| `validate_artifacts.py` (CI) | nothing (read-only) | n/a |

If you find an agent writing outside this table, that's the bug — fix
the agent, not the doc.

---

## See Also

- [METHODOLOGY.md](../../METHODOLOGY.md) — the five rules + design philosophy
- [vv-matrix.md](vv-matrix.md) — V&V evidence format spec
- [start-work-checklist.md](../start-work-checklist.md) — ~60s pre-session checklist
