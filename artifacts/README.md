# `artifacts/`

Non-text engineering artifacts — CAD, schematics, PCB layouts, firmware
binaries, large simulation results — don't diff well in git. This
directory holds **references**, not the artifacts themselves.

## Subdirectories

One per active discipline. Add or remove based on `config/disciplines.yml`:

- `mechanical/` — STEP, PRT, IGES, manufacturing drawings (PDF)
- `electrical/` — schematics, PCB layouts, BOMs, gerbers
- `firmware/` — embedded code, build artifacts, RTOS configs
- `software/` — heavy assets that don't fit in `src/` (model weights,
  large datasets, generated code)

## What goes here

For each artifact, a markdown manifest file with this shape:

```markdown
# motor-mount-rev-C.step

**Owner:** @mechanical-lead
**Linked requirements:** FR-2.3, NFR-3.1, IF-1.4
**Last reviewed:** 2026-06-12 by @systems-lead
**Storage:** vault://CAD/motor-mount/rev-C/
**SHA-256:** abc123...
**Snapshot:** ./snapshots/motor-mount-rev-C.png

## Change log
- rev-C (2026-06-12): widened bolt circle to 38mm for thermal expansion
- rev-B (2026-05-04): initial release
```

The actual STEP file lives in your CAD vault, git-LFS, or shared drive —
wherever it normally lives. The manifest gives the project a stable
reference that *can* be diffed, reviewed in PRs, and linked from
Issues. The PNG snapshot in `snapshots/` is a low-resolution preview
so reviewers can see what changed without installing the tool.

## Why this matters

- Snapshot images + manifest data let `@verification` and reviewers do
  meaningful work without the heavyweight tool.
- The SHA-256 lets you catch silent overwrites in the vault.
- The `Linked requirements:` field makes the «satisfy» relationship
  automatic — `generate_docs.py` builds a manifest-to-requirement
  matrix from these.

## Format spec + validator

Full schema and field reference: [`dev-docs/architecture/artifact-manifest.md`](../dev-docs/architecture/artifact-manifest.md).

Worked example: [`artifacts/mechanical/EXAMPLE-motor-mount.md`](mechanical/EXAMPLE-motor-mount.md).

Validate all manifests:
```bash
python scripts/validate_artifacts.py           # check, exit 1 on errors
python scripts/validate_artifacts.py --verbose # show clean files too
```

The validator runs in CI on every PR via a future workflow; for now,
run it locally before opening a PR that touches `artifacts/`.
