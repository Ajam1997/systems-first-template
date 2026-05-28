# V&V Matrix — Format Spec

Every FR / NFR / UN / IF / KPM Issue body carries explicit verification
and validation evidence in two structured sections. The renderer in
`scripts/generate_docs.py` parses these and produces a coverage table
in the architecture doc.

This is the SysML «verify» relationship in tabular form.

## Definitions

- **Verified By:** the *proof* that the requirement is correctly
  implemented. Usually a test, simulation, or measurement.
  Answers: *"how do we know the implementation does what the
  requirement says?"*
- **Validated By:** the *demonstration* that the requirement actually
  satisfies its parent user need (or, for KPMs, that the measurement
  was performed in the integrated system). Usually an E2E test,
  KPM measurement, or hardware soak.
  Answers: *"how do we know the requirement was the right one?"*

## Issue body format

Add these two sections to the Issue body. Each line is a single
evidence source. The grammar is:

```
**Verified By:**
- <kind>: <reference>
- <kind>: <reference>

**Validated By:**
- <kind>: <reference>
```

`<kind>` must come from `config/evidence-kinds.yml`. The active set is
project-specific.

### Common kinds (the full vocabulary is in `config/evidence-kinds.yml`)

| Kind | Reference shape | Example |
|---|---|---|
| `pytest` | `tests/<file>::<func>` | `pytest: tests/test_sharpness.py::test_score_is_normalized` |
| `unittest` | `<path>` (any framework) | `unittest: firmware/test/sensor_init.cpp::test_default_state` |
| `simulation` | `sim/<run>.json` | `simulation: sim/thermal-rev-c.run.json` |
| `fea` | `cad/<assembly>-<analysis>-rev<N>.fea` | `fea: cad/mount-stress-rev3.fea` |
| `spice` | `pcb/<schematic>-<analysis>.sp` | `spice: pcb/regulator-tran.sp` |
| `bench` | `<date> <instrument>, <conditions>` | `bench: 2026-06-12 oscilloscope BNC-3, 50°C ambient` |
| `dvt`/`evt`/`pvt` | `verification/<phase>/<plan>.md` | `dvt: verification/dvt/thermal-soak.md (PASS 2026-06-12)` |
| `dfm` | `<date> review with supplier <name>` | `dfm: 2026-04-12 review with supplier ACME` |
| `kpm` | `KPM-X.Y` | `kpm: KPM-1.3` |
| `e2e` | `Stage N milestone` or test path | `e2e: Stage 2 milestone — observable in library.db` |
| `script` | `scripts/<file>.py` | `script: scripts/check_drift.py` |
| `inspection` | what was inspected | `inspection: PR diff shows no docs/ paths left` |
| `review` | `<review-type> <date>` | `review: PDR 2026-06-10 minutes` |
| `regulatory` | `<standard> <cert-no> <date>` | `regulatory: FCC Part 15 Subpart B 2026-08-01` |

Blank line ends the section. Another `**Field:**` heading ends the
section. Order: `Verified By` always before `Validated By`.

## Per-requirement-type conventions

| Requirement type | Verified By | Validated By |
|---|---|---|
| **UN** (user need) | rolls up from its FR/NFR/IF children (no direct entry) | one E2E or observable check that proves the need is met for a real user |
| **FR** (functional) | one or more `pytest` / `unittest` / `simulation` / `bench` lines | the KPM or E2E that touches this code path |
| **NFR** (non-functional) | usually a `script`, `inspection`, `review`, or `pytest` line | the KPM (most NFRs constrain a measurable) |
| **IF** (interface) | two sets — one per side, in `Verified By (Side A)` and `Verified By (Side B)` | an integrated E2E that proves both sides work together |
| **KPM** | the benchmark script + its assertion | (KPMs are self-validating — leave Validated By empty or `N/A`) |

## Rendering

`scripts/generate_docs.py` walks all Issues with `type: fr`,
`type: nfr`, `type: if`, `type: kpm`, `type: user-need`, parses these
two sections, and renders a V&V matrix into the architecture doc between
the `<!-- AUTO:vv_matrix -->` sentinels.

A requirement with empty `Verified By` is flagged `⚠` or `✗` in the
rendered matrix — useful for finding the next test to write.

## Coverage flag legend

| Flag | Meaning |
|---|---|
| ✓ | Verified-by AND Validated-by both populated (or rolls up cleanly for UN/KPM) |
| ⚠ | One of the two populated |
| ✗ | Neither populated — this is your worklist |

## Migration tips when adopting

If you're adopting this on an existing project where requirements
already exist:

1. Start with the Issues for landed work (where the tests already
   exist) — the `Verified By` lines write themselves from the existing
   test inventory. ~10 minutes per stage of landed code.
2. Then file in `Validated By` lines for any UN that's been
   demonstrated end-to-end.
3. The remaining ✗ rows are the work that genuinely lacks evidence —
   triage them.
