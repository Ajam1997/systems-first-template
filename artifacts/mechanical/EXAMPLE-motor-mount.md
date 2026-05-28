---
name: EXAMPLE-motor-mount
discipline: mechanical
owner: "@mechanical_lead"
linked_requirements:
  - FR-2.3
  - NFR-3.1
  - IF-1.4
current_revision: C
storage: "vault://CAD/EXAMPLE-motor-mount/rev-C/EXAMPLE-motor-mount.step"
sha256: "0000000000000000000000000000000000000000000000000000000000000000"
snapshot: "snapshots/EXAMPLE-motor-mount-rev-C.png"
last_reviewed: "2026-06-12"
reviewer: "@systems_lead"
mass_g: 58.2
cost_unit_usd: 4.20
vendor: "Acme Machining"
---

# EXAMPLE: motor-mount

This is a worked-example manifest illustrating the
[artifact manifest format](../../dev-docs/architecture/artifact-manifest.md).
Delete this file (and `snapshots/EXAMPLE-motor-mount-rev-C.png` if you
create one) before shipping. It exists so the validator has something to
parse and so future-you remembers what a real manifest looks like.

## Design rationale

The motor mount holds the BLDC motor against the chassis with a 4-bolt
pattern on a 38mm diameter circle. The C revision widened the bolt
circle from 32mm (rev-A/B) to accommodate thermal expansion at the
75°C steady-state operating point measured in FEA.

Material: 6061-T6 aluminum. Mass per unit: 58.2 g (measured, not
estimated). The KPM allocation for this part is 60 g — we have 1.8 g
of margin.

## Linked verification

- FEA stress analysis: `verification/simulation/EXAMPLE-motor-mount-stress.md`
  (rev-C passes at 5x design load with 2.1 safety factor)
- Bench measurement (mass): noted in this manifest's `mass_g` field;
  also posted as a measurement comment on KPM-mass-pcb-mount
- DVT plan: `verification/dvt/EXAMPLE-thermal-soak.md` (verifies
  thermal expansion accommodation under 4-hour 75°C ambient)

## Change log

- **rev-C** (2026-06-12): widened bolt circle from 32mm → 38mm to
  accommodate thermal expansion observed in FEA at 75°C. Mass increased
  from 57.0 g (rev-B) to 58.2 g; still within 60 g allocation. FEA
  re-run; passes. DVT thermal-soak plan updated.
- **rev-B** (2026-05-04): bolt circle correction from 30mm (rev-A
  was wrong — bolt spec was M4, needed M5 spacing). Mass unchanged.
- **rev-A** (2026-04-20): initial release. Withdrawn after bolt-circle
  geometry error.

## Notes

- Vendor `Acme Machining` quoted $4.20/unit at 100-unit quantity.
  Source the BOM cost from this field, not from a separate quote
  document — keep it where the artifact lives.
- The `0000…` placeholder SHA-256 is intentional — this is an example,
  not a real artifact. For a real manifest, compute the hash with
  `sha256sum motor-mount.step` (Linux/Mac) or
  `Get-FileHash motor-mount.step -Algorithm SHA256` (PowerShell).
