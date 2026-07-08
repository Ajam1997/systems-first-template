# Development Plan: From systems-first-template to the SE Synthesis Harness

**Date:** 2026-07-08
**Status:** Proposed
**Inputs reviewed:** this repository (commit `a7af30a`), `systems_first_audit.md`,
`CLAUDE_CODE_BOOTSTRAP.md` (v1/v2/v3), `litreview_v2.md`, the SysML v2 tooling
research report ("compass" artifact), and the Capability Builders SE workshop
handout (Digby, Feb 2026, 398 slides).

---

## 1. Executive summary

The prior work is further along than "brainstorming" — it contains a completed
audit, a converged architecture (Bootstrap v3), a defensible research gap
statement with ~60 sources, a tooling decision for SysML v2 validation, and a
methodological grounding (the workshop handout) that the validation rules are
already traceable to.

**The recommendation of this plan is to stop iterating on the template and
build the Bootstrap v3 harness as a standalone repository**, treating this
template as the documented prototype it has become. The genuinely open work is
not architecture — v3 settles that — it is:

1. **The evaluation design.** The research claim ("a validation-refinement
   loop produces valid SE artifacts where a single-pass LLM call would not")
   has no experiment specified anywhere in the prior work. Section 6 defines one.
2. **Closing the loop on SysML output.** v3 generates SysML v2 text but never
   validates it; the compass report already picked the tool (`windtrader`).
3. **A second case study with ground truth.** The handout's grain-mill worked
   example provides instructor-authored requirements, architecture, trade
   study, and ICD artifacts to compare harness output against — a validation
   opportunity none of the prior documents noticed.
4. **Disposition of this repository** (freeze + harvest, small fix list).

---

## 2. What the prior work already decided — adopt, do not reopen

The five documents show a clear convergence across three bootstrap iterations.
These decisions are settled and the plan treats them as fixed:

| Decision | Where settled | Rationale |
|---|---|---|
| Abandon GitHub Issues as the requirements database | Audit §1, Bootstrap v3 "WHAT THIS IS NOT" | Coupling makes the capstone claim ("DB-agnostic") indefensible |
| Standalone CLI + library, not a Claude Code artifact | Audit §4, v3 | Testable headless; Claude Code builds it but does not appear in it |
| SQLite runtime store; YAML in/out; self-contained HTML reports | v3 "PERSISTENCE MODEL" | Zero infrastructure, offline, full SQL |
| Six-stage pipeline: Formalization → Quality → Logical arch → Physical arch → ICD → V&V render | v3 | Mirrors handout P01→P02 and stops before P03 (declared out of scope) |
| EARS + "Excellent Requirements" rules as the linguistic validation layer, severity *warning*; structural rules severity *error* | v2 (EARS regex spec), v3 rules 1–13 | Direct operationalization of handout W1.3/W1.4; warnings never block |
| OpenRouter as the model-agnostic LLM provider | v3 | One env var, one model string; enables the cross-model experiment |
| SysML v2 export as text emission only; no round-trip, no parametrics | Compass report GO/NO-GO | SysON can't round-trip byte-stably; parametric views don't exist yet |
| Spacecraft communications subsystem as the primary case study | v3 fixtures | Realistic, tractable, derived from coursework |
| Research gap: no published work combines DB-agnostic ingestion + LLM synthesis + formal validation gate + refinement loop | litreview_v2 gap statement | Verified against SysMBench, Timperley 2025, Rafique 2025, LLM4RE SLR |

**One prior-art caveat to carry into the paper:** the Internetware 2025 study
(litreview L7) found rule-based regeneration fixed most *syntactic* defects but
only modestly improved *semantic* hallucinations (31/72). The harness's
validation rules are largely syntactic/structural. The evaluation (§6) must
therefore measure semantic quality independently, or the capstone risks
demonstrating only what L7 already showed.

---

## 3. State of this repository (condensed)

The full survey is in the audit; a fresh pass at `a7af30a` confirms and updates it.

**Pilot-hardened and worth keeping (as harvest material):**
- `scripts/export_sysml.py` — YAML→SysML v2 emission, carrying real fixes from
  the feline pilot (`import ScalarValues::*`, `// verifies:` comments instead
  of invalid `verify` keyword). This is the seed of `export/sysml.py` in the harness.
- `scripts/kpm_rollup.py` — cycle detection, topo-sort, sum/max/min aggregation.
  The KPM validation logic maps directly to `validate_decomposition_acyclicity`
  and `validate_kpm_unit_consistency`.
- `requirements/requirement-map.yml` schema — the import format
  `YAMLRequirementsDB` must remain compatible with.
- `config/evidence-kinds.yml` vocabulary (18 kinds) — richer than v3's default list.
- METHODOLOGY.md's five rules and the breadcrumb/handoff discipline — these
  survive any refactor and belong in the harness docs.

**Known defects, if the template stays in use** (none block the harness):
- `scripts/github_comment.py` mojibake — em-dashes double-encoded in every
  comment f-string; it is also the one script missing the UTF-8 stdout guard.
- Living-doc naming is three-way inconsistent (`living-user-needs.md` vs
  `requirements-summary.md`) and most render targets don't exist, so
  `generate_docs.py` silently renders only `architecture.md`.
- `evidence-kinds.yml` `active`/`file_check` enforcement is documented but never
  implemented in `generate_docs.py`.
- Dead references: `scripts/seed_github.py`, `scripts/sync_milestones.py`,
  `dev-docs/architecture/template-roadmap.md`, `requirements/interfaces/IF-*.md`,
  `user-need.md` (actual file is `.yml`); `.claude/README.md` describes the
  Pass-1 world; external-tools.md points into the out-of-repo feline pilot.
- Stubs: `validate_artifacts.py --fix`, `critical_path` aggregation.

**Disposition (Phase 0 decision):** freeze the template. It has done its job:
it proved the methodology, surfaced the coupling problem, and hardened the
SysML exporter through a real pilot. Fix only the mojibake bug (it corrupts
any future pilot's Issue comments) and add a README pointer to the harness
repo. The rest of the defect list is recorded here and fixed only if a future
pilot actually runs on the template. Do not spend capstone weeks polishing a
repo the capstone no longer depends on.

---

## 4. What the handout adds (and where v3 is already aligned)

The workshop handout is the methodological anchor. Alignment check:

**Already aligned in v3:**
- P01/P02 process model → Stages 1–4; P03 explicitly out of scope (correct —
  the handout treats component-requirements specification as a distinct process).
- EARS five patterns + complex combinations → `validate_ears_syntax` (v2 regex spec).
- Priority tiers Essential/Desirable/Optional/Aspirational → `validate_has_priority`.
- "Write the verification method at the same time as the requirement" →
  `verification_method` is a field on `Requirement` from Stage 1, and the VCRM
  (v3's V&V matrix) is a linked view over the same store — exactly the
  handout's slide-163 prescription.
- Unique, permanent, information-free identifiers → UN-/FR-/IF-/KPM- neutral scheme.
- N² interface chart → `icd.html` embeds a Mermaid N² matrix.
- Logical-before-physical architecture, allocation completeness checks →
  Stages 3/4 and `validate_traceability`/`validate_interface_bidirectionality`.

**Gaps worth closing cheaply:**
- **Requirements Bingo defect taxonomy (15 categories)** — v3 implements 7 as
  regex rules + EARS and defers 3 (testable, no-design, well-defined). Build an
  explicit mapping table (category → rule → implemented/deferred/out-of-scope)
  into the harness docs. It is a one-hour artifact that gives the capstone paper
  a complete coverage argument for the linguistic layer.
- **Operational scenarios / states in P01** — the handout elicits states and
  modes during requirements definition; v3 defers states to Stage 3. Acceptable,
  but Stage 1's prompt should ask the LLM to *note* candidate states from
  stakeholder text so Stage 3 has raw material. Prompt change only, no schema change.
- **Trade studies, FMECA, baselines/BCRs, gateway reviews** — out of scope for
  the harness MVP; cite as future work. The regenerative model (re-synthesize
  downstream from a changed need, per the SDD sources) is the harness's answer
  to baseline change management and deserves a paragraph in the paper, not code.

**New opportunity — the grain mill as second case study:** the handout threads
a deployable grain mill worked example through all 398 slides, including an
instructor-authored requirements database structure (URD/SRD/VCRM sheets),
trade study, and ICD template. Feeding the mill's stakeholder needs into the
harness and comparing output against the instructor's artifacts gives the
evaluation a ground-truth case study *authored by an independent SE
practitioner* — much stronger than self-authored fixtures alone, and it
directly demonstrates alignment with the training the capstone audience
(practitioners) receives.

---

## 5. Plan of record — phases

Phasing follows the audit's three-phase capstone shape, updated for what v3
already specifies. Weeks are relative to start-of-build.

### Phase 0 — Disposition and setup (days, not weeks)
1. Create the `systems-first-harness` repository from Bootstrap v3's structure.
2. Freeze this template: fix `github_comment.py` mojibake (+ UTF-8 guard), add
   README pointer to the harness repo, link this plan. No other cleanup.
3. Port harvest material: `export_sysml.py` emission logic, KPM validation
   logic, `requirement-map.yml` schema (as the `YAMLRequirementsDB` import
   contract), evidence-kinds vocabulary.
4. Set up CI skeleton per the compass report: pytest + `windtrader` job
   (Temurin JDK + pinned windtrader/JAR versions) gating `.sysml` output.

### Phase 1 — Foundation: model, DB, validation (≈ weeks 1–4)
Bootstrap v3 START HERE steps 1–11, in order, with tests before synthesis:
dataclasses → `RequirementsDB` (SQLite, YAML, mock) → `ValidationReport` →
structural rules 1–5 → EARS (v2 regex spec verbatim) → linguistic rules 7–13 →
ICD + evidence validators → `ValidationPipeline` with per-stage rule sets.
**Add to v3:** the Requirements-Bingo mapping table (docs) and property-style
tests for the EARS regexes against the handout's own example requirements
(both conformant and "Bingo" defect examples — free test vectors).
*Exit criteria:* v3 success criteria 1–5 (install, ≥80% coverage on
`validation/` and `db/`, fixture-driven validate commands behave).

### Phase 2 — Synthesis loop, CLI, exports (≈ weeks 5–8)
v3 steps 12–20: `LLMProvider` (OpenRouter + mock) → five stage prompts →
`SynthesisEngine` (gen → parse → validate → refine, max 5 iterations) →
`InputParser` → SysML/YAML/HTML exports → orchestrator → CLI.
**Add to v3:**
- Validate emitted SysML with `windtrader` as part of `export --format sysml`
  and in CI; spot-render in SysON locally (import + Requirements Table +
  Interconnection View per the compass GO list). Do not build round-trip.
- Instrument the loop for the experiment: persist per-iteration
  `ValidationReport`s and raw outputs (v3 already stores these) plus token
  counts and wall time per stage. The experiment in §6 is only as good as
  this instrumentation.
- Stage 1 prompt notes candidate states/modes (handout alignment, §4).
*Exit criteria:* v3 success criteria 6–16 (full pipeline on spacecraft-comms
fixture; six HTML reports, zero external HTTP; SysML export non-empty **and
windtrader-clean**; model swap via `--model` flag only).

### Phase 3 — Evaluation and case studies (≈ weeks 9–12)
Run the experiment (§6) on two case studies:
1. **Spacecraft comms** (v3 fixtures) — primary, self-authored ground truth.
2. **Grain mill** (handout) — secondary, independent practitioner ground truth.
Write up: research gap (litreview §Gap), method, results, threats to validity
(led by the L7 semantic-hallucination caveat), Bingo coverage table, limitations
and future work (DOORS/OSLC/ReqIF adapters, deferred LLM-assisted validators,
P03, template re-integration).

### Phase 4 — Stretch (only if timeline allows)
Re-integrate with this template: `@systems_lead` invokes the harness CLI and
posts results back through `scripts/github_comment.py` (v3 open question 8).
This closes the loop with the original vision but is deliberately last — the
capstone stands without it.

---

## 6. Evaluation design (the missing piece)

The prior work states the research claim but never the experiment. Proposed design:

**Hypothesis.** Stage-gated semantic validation with structured error feedback
increases the rate of valid SE artifacts vs. single-pass generation, at
acceptable iteration cost, robustly across models.

**Conditions.** (a) Single-pass: `max_iterations = 1` (ablation baseline);
(b) Loop: `max_iterations = 5`. Same prompts, fixtures, and parser in both —
the loop is the only variable.

**Models.** Three via OpenRouter (e.g., an Anthropic frontier model, an OpenAI
frontier model, a fast/cheap model), pinned by exact model string. N ≥ 10 runs
per condition × model × case study (LLM output is stochastic; report
distributions, not single runs).

**Primary metrics (automatic, from instrumentation):**
- Validity rate: fraction of runs where each stage reaches zero errors
  (report per stage — Stage 3/4 structural validity is where the claim bites).
- Error profile: count per rule at iteration 1 vs. final (which rules the loop
  actually fixes; which errors models make unprompted).
- Convergence: iterations-to-valid; failure-to-converge rate at cap.
- Cost: tokens and wall time per condition (the loop must earn its overhead).

**Secondary metrics (semantic — addresses the L7 caveat):**
- Blinded human rubric on final artifacts using Ferrari et al.'s criteria
  (completeness, correctness, standards adherence, comprehensibility) plus
  traceability correctness (Timperley found function-level traceability the
  weak point — score it specifically).
- Ground-truth comparison: element-level precision/recall of generated
  logical blocks / interfaces / requirements against the fixture (spacecraft)
  and instructor artifacts (grain mill).

**Analysis.** Paired per-seed comparison of conditions; simple proportion tests
suffice at this N. The interesting result is the *shape*: if the loop lifts
structural validity to ~100% but semantic rubric scores stay flat, that is an
honest (and publishable) finding that positions the deferred LLM-assisted
validators as necessary future work.

---

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Loop games the regexes: model satisfies EARS/structural rules while semantics degrade (L7 finding) | Semantic rubric + ground-truth comparison in §6; report both; frame honestly |
| YAML parse fragility dominates iterations | v3 already treats parse failures as ValidationErrors; track `yaml_parse` error rate separately so it doesn't masquerade as a validation result |
| `windtrader` is v0.1.x, solo-maintainer, parse-only (no semantic resolution) | Pin versions; treat as syntax gate only; SysON manual import as the semantic spot check; fallback documented in compass report |
| OpenRouter cost/availability during the N×condition×model matrix | Budget with the cheap model first; cache raw outputs (already persisted) so scoring never re-runs generation |
| Scope creep back into the template / GitHub integration | Phase 4 is explicitly stretch; the capstone deliverable is the harness + experiment |
| Confidence metric (1.0/iterations) is crude | Keep it as a display heuristic only; the experiment reports the real distributions |
| Capstone timeline unknown (audit open question #1) | Phases 1–2 are strictly ordered with exit criteria; Phase 3 can shrink to one case study (spacecraft) and two models if needed — decide at week 8, not week 12 |

---

## 8. Immediate next actions

1. Approve this plan (or redline the disposition decision in §3 — it is the
   only genuinely reversible fork).
2. Phase 0: create `systems-first-harness` repo; paste Bootstrap v3 as the
   build brief; land the CI skeleton.
3. Fix `github_comment.py` mojibake in this repo; add the pointer README.
4. Begin Phase 1 step 1 (model dataclasses) — v3's START HERE order is the
   work queue from here on.
