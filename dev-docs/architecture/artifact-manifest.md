# Artifact Manifest Format

Non-text engineering artifacts — CAD assemblies, PCB layouts, firmware
binaries, large simulation results — don't diff in git and break the
template's "Issues canonical, docs render" pattern. The template's
answer: store the **manifest** in the repo, store the **artifact** in
your vault / LFS / shared drive.

The manifest is plain markdown with YAML front-matter. It carries:

- A reference to where the actual file lives
- A SHA-256 hash so silent vault overwrites get caught on PR review
- A snapshot PNG so reviewers don't need the CAD/EDA tool
- The requirements this artifact satisfies («satisfy» link)
- An append-only change log

This format works for any discipline (mechanical, electrical, firmware
binaries, large datasets). `scripts/validate_artifacts.py` validates
it independent of discipline.

## File location

```
artifacts/
  mechanical/
    motor-mount.md            ← the manifest (text, git-tracked)
    snapshots/
      motor-mount-rev-C.png   ← snapshot image, git-tracked, ≤ 200 KB
  electrical/
    main-board.md
    snapshots/
      main-board-rev-3.png
  firmware/
    bootloader.md
  software/
    florence2-int8.md         ← large model weights
```

One manifest per *named artifact* (a CAD assembly, a schematic, a
firmware binary). Revisions of the same artifact roll up under one
manifest with a change log.

## Schema

YAML front-matter at the top of the file, then free-form markdown
sections below the closing `---`.

```markdown
---
name: motor-mount
discipline: mechanical
owner: "@mechanical_lead"
linked_requirements:
  - FR-2.3
  - NFR-3.1
  - IF-1.4
current_revision: C
storage: "vault://CAD/motor-mount/rev-C/motor-mount.step"
sha256: "abc123def456..."
snapshot: "snapshots/motor-mount-rev-C.png"
last_reviewed: "2026-06-12"
reviewer: "@systems_lead"
---

# motor-mount

<Optional free-form description, design rationale, links to FEA
results, etc. — this section is not parsed.>

## Change log

- **rev-C** (2026-06-12): widened bolt circle to 38mm for thermal
  expansion; mass +2g; FEA verified at 75°C steady-state.
- **rev-B** (2026-05-04): initial release.
```

### Required fields

| Field | Type | Purpose |
|---|---|---|
| `name` | string | Stable identifier; matches the filename stem |
| `discipline` | string | Must match a key in `config/disciplines.yml` (`mechanical`, `electrical`, `firmware`, `software`, …) |
| `owner` | string | `@<github-handle>` — who's responsible |
| `linked_requirements` | list of strings | FR/NFR/IF/KPM IDs this artifact satisfies — drives the «satisfy» relationship |
| `current_revision` | string | Latest rev letter or version string |
| `storage` | string | URI pointing at the actual artifact (vault:// , https:// , lfs:// , file:// ) |
| `sha256` | string | Hex hash of the artifact at `current_revision` |
| `snapshot` | string | Relative path to a PNG render under `snapshots/` |
| `last_reviewed` | string (ISO date) | When the latest revision was last reviewed |
| `reviewer` | string | `@<github-handle>` who did the latest review |

### Optional fields

| Field | Type | Purpose |
|---|---|---|
| `aliases` | list of strings | Prior names for `git log --follow` analogs |
| `parent_artifact` | string | Name of a parent assembly this is part of |
| `vendor` | string | Supplier, if applicable |
| `cost_unit_usd` | float | Unit cost — feeds into BOM cost KPM rollup if used |
| `mass_g` | float | Mass in grams — feeds into mass KPM rollup |
| `notes` | string | Anything else |

`mass_g` and `cost_unit_usd` are the bridge to the KPM rollup engine.
If a child KPM is `aggregation: independent` but linked to an artifact
with `mass_g: 60`, `kpm_rollup.py` (future enhancement) can read the
manifest's mass directly instead of needing a per-component KPM
measurement.

## Snapshot conventions

- **PNG only.** JPEG compresses CAD wireframes poorly; SVG renders
  inconsistently across browsers.
- **≤ 200 KB.** PR review weight matters. Render at 1024×768 or so.
- **Render the same view across revisions** so diff is visible at a
  glance. If the part has multiple meaningful views, render each as a
  separate file (`motor-mount-rev-C-iso.png`, `motor-mount-rev-C-top.png`).
- **Commit the snapshot in the same PR as the manifest update.** Stale
  snapshots are worse than no snapshots.

## Change log conventions

- Append-only. Never delete a revision entry. If a revision was
  withdrawn, mark it `(WITHDRAWN)` in the entry.
- One bullet per revision, newest first.
- Format: `**rev-<letter>** (YYYY-MM-DD): <one-line summary>`.
- Free to add follow-up bullets under a revision for detail, but keep
  the headline scannable.

## Validation

`scripts/validate_artifacts.py` checks every manifest under
`artifacts/`:

- All required fields present
- `discipline` is in `config/disciplines.yml`
- `linked_requirements` reference real IDs (looks up against
  `requirements/requirement-map.yml`)
- `snapshot` path exists and is ≤ 200 KB
- `sha256` is 64 hex chars
- `last_reviewed` is a valid ISO date

Run it manually or in CI:
```bash
python scripts/validate_artifacts.py
python scripts/validate_artifacts.py --fix  # touch snapshots/, add stub fields
```

## When to use a manifest vs commit the artifact directly

The manifest pattern was designed for binaries too large to commit.
With the code-CAD / code-PCB stack we recommend ([external-tools.md](external-tools.md)),
many engineering outputs are now small enough to live directly in
git:

| Output | Typical size | Commit directly? |
|---|---|---|
| BOM CSV | <1 KB | yes |
| Snapshot PNG | <200 KB | yes |
| Build123d STEP (single part) | <100 KB | yes |
| Atopile-generated KiCad PCB (small board) | <50 KB | yes |
| ezdxf-generated drawing DXF | <50 KB | yes |
| Full multi-part CAD assembly STEP | several MB | manifest + vault |
| Full board Gerber zip with images | several MB | manifest + vault |
| FEA result blobs | tens of MB | manifest + vault |
| Firmware binaries with debug symbols | tens of MB | manifest + vault |

**Rule of thumb:** if the binary is under ~1 MB and produced by a
reproducible build (code-CAD `.py`, atopile `.ato`), commit it. The
small artifact IS its own manifest in that case — git's SHA-1 + diff
history is sufficient, and the source file regenerates it. Use the
manifest format below for the cases where the binary is too large or
its source isn't text.

## What this format does NOT do

- **It doesn't store the artifact.** Use git-LFS, your CAD vault, or
  a shared drive. The manifest is a pointer, not the payload.
- **It doesn't enforce vault sync.** If the SHA-256 in the manifest
  doesn't match what's at the storage URL, the validator complains;
  re-uploading is your job.
- **It doesn't render the artifact.** That's what the snapshot PNG is
  for, plus the user opening the file in their CAD tool when they need
  detail.
- **It doesn't replace the CAD tool's version control.** Use whatever
  PDM/PLM your CAD tool offers natively; the manifest tracks
  *project*-level state, not internal CAD revision history.

## Why this is text-only

Three reasons:

1. **PR review.** Reviewing a manifest diff in the GitHub PR UI is
   trivial. Reviewing a STEP file diff is impossible.
2. **Audit trail.** Every revision change is a commit. `git log
   artifacts/mechanical/motor-mount.md` shows the artifact's
   project-level history.
3. **Validation in CI.** Plain text + structured fields → cheap
   automated checks.

The artifact itself is binary. The metadata is not. Keep them
separate; track them together via the manifest.

## See also

- `scripts/validate_artifacts.py` — the validator
- `artifacts/mechanical/EXAMPLE-motor-mount.md` — worked example
- `dev-docs/architecture/doc-source-of-truth.md` — overall write authority
- `METHODOLOGY.md` "The artifact hierarchy" — where this fits
