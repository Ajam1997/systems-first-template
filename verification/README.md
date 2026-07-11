# `verification/`

Test plans and result links, organized by evidence kind. The structured
home for the `<kind>: <reference>` lines that the V&V matrix renders.

## Subdirectories

| Folder | Holds | Cadence |
|---|---|---|
| `unit/` | Unit-test plans (markdown) and links to test results | per-commit |
| `simulation/` | Simulation specs + result links (FEA, SPICE, thermal, control) | per-design-change |
| `bench/` | Bench-test procedures + raw data references | per-build |
| `dvt/` | Design Verification Test plans | per-stage |
| `evt/` | Engineering Verification Test plans (often per-build-lot) | per-stage |
| `pvt/` | Production Verification Test plans (sampling, AQL) | pre-production |

## What goes in each folder

A test-plan markdown file per requirement-or-interface being verified.
Example shape (`verification/dvt/DVT-thermal-soak.md`):

```markdown
# DVT-thermal-soak — Thermal soak verification

**Verifies:** NFR-2.4 (thermal envelope), KPM-3.2 (steady-state temp)
**Procedure:**
1. Mount DUT in chamber at 50°C ambient.
2. Run pipeline for 4 hours continuous.
3. Log internal temperature every 60s.
**Pass criteria:** Internal temp ≤ 75°C throughout.
**Last run:** 2026-06-12, DVT-build-3, unit #007. **PASS.**
**Result link:** vault://test-results/dvt-thermal-soak/2026-06-12/
```

The Issue body for the requirement then carries:

```
**Verified By:**
- dvt: verification/dvt/DVT-thermal-soak.md (PASS 2026-06-12)
```

`sf-docs` validates that referenced verification files
exist and surfaces orphans.

## Why test plans live here, not on Issues

Test *plans* benefit from version control with diffs. Test *results*
typically live wherever the test was run (scope traces, sim output,
chamber logs). The plan is the durable artifact; the result is a
reference.

## Pass 1 status

Pass 1 ships only `unit/`. Pass 2 (mechanical) adds `simulation/` and
`bench/`. Pass 3 adds the full DVT/EVT/PVT chain.
