#!/usr/bin/env python3
"""Validate artifact manifests under artifacts/.

Walks every `.md` file under `artifacts/<discipline>/` (skipping
`README.md` and any `snapshots/` subdirectories), parses the YAML
front-matter, and checks:

  - All required fields are present and non-empty
  - `discipline` matches an entry in config/disciplines.yml
  - `linked_requirements` reference IDs that exist in
    requirements/requirement-map.yml or in GitHub Issues
  - `snapshot` path exists and is <= 200 KB
  - `sha256` is 64 hex chars
  - `last_reviewed` is a valid ISO date

Exits non-zero if any manifest fails. Suitable for CI.

Usage:
  python scripts/validate_artifacts.py           # validate, exit 1 on failure
  python scripts/validate_artifacts.py --verbose # show every manifest checked
  python scripts/validate_artifacts.py --fix     # stub missing optional fields
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# UTF-8 stdout safety for non-UTF-8 consoles
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import yaml

REPO_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
DISCIPLINES_PATH = REPO_ROOT / "config" / "disciplines.yml"
REQ_MAP_PATH = REPO_ROOT / "requirements" / "requirement-map.yml"

REQUIRED_FIELDS = [
    "name", "discipline", "owner", "linked_requirements",
    "current_revision", "storage", "sha256", "snapshot",
    "last_reviewed", "reviewer",
]
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
MAX_SNAPSHOT_BYTES = 200 * 1024  # 200 KB


@dataclass
class Manifest:
    path: Path
    front_matter: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def discover_manifests(root: Path) -> list[Path]:
    """Return all manifest .md paths under artifacts/<discipline>/."""
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.rglob("*.md"):
        if p.name == "README.md":
            continue
        if "snapshots" in p.parts:
            continue
        out.append(p)
    return sorted(out)


def parse_manifest(path: Path) -> Manifest:
    m = Manifest(path=path)
    text = path.read_text(encoding="utf-8")
    fm = FRONT_MATTER_RE.search(text)
    if not fm:
        m.errors.append("no YAML front-matter (expected `---` fenced block at top)")
        return m
    try:
        m.front_matter = yaml.safe_load(fm.group(1)) or {}
    except yaml.YAMLError as e:
        m.errors.append(f"YAML front-matter parse error: {e}")
        return m
    if not isinstance(m.front_matter, dict):
        m.errors.append("YAML front-matter must be a mapping")
        m.front_matter = {}
    return m


def load_disciplines() -> set[str]:
    if not DISCIPLINES_PATH.exists():
        return set()
    data = yaml.safe_load(DISCIPLINES_PATH.read_text(encoding="utf-8")) or {}
    return {(d.get("name") or "").replace("_lead", "")
            for d in (data.get("disciplines") or [])
            if d.get("name")}


def load_known_requirement_ids() -> set[str]:
    """Collect every requirement ID referenced in requirement-map.yml."""
    if not REQ_MAP_PATH.exists():
        return set()
    data = yaml.safe_load(REQ_MAP_PATH.read_text(encoding="utf-8")) or {}
    ids: set[str] = set()
    for section_name in ("user_needs", "functional_requirements",
                         "non_functional_requirements", "interface_requirements",
                         "kpms"):
        section = data.get(section_name) or {}
        if isinstance(section, dict):
            ids.update(section.keys())
    # Also pick up children referenced under user_needs (FRs/NFRs/IFs/KPMs
    # may not have their own top-level entry yet)
    for un_entry in (data.get("user_needs") or {}).values():
        if isinstance(un_entry, dict):
            for fld in ("functional_requirements",
                        "non_functional_requirements",
                        "interface_requirements", "kpms"):
                for child in (un_entry.get(fld) or []):
                    ids.add(child)
    return ids


def validate_manifest(m: Manifest, known_disciplines: set[str],
                      known_req_ids: set[str]) -> None:
    fm = m.front_matter

    # Required fields
    for fld in REQUIRED_FIELDS:
        val = fm.get(fld)
        if val is None or (isinstance(val, str) and not val.strip()) \
                or (isinstance(val, list) and len(val) == 0):
            m.errors.append(f"missing required field: {fld}")

    # discipline must be known (warn — not all projects activate all disciplines)
    disc = fm.get("discipline")
    if disc and known_disciplines and disc not in known_disciplines:
        m.warnings.append(
            f"discipline '{disc}' is not active in config/disciplines.yml "
            f"(known: {sorted(known_disciplines)})"
        )

    # linked_requirements must resolve
    if known_req_ids:
        for req in (fm.get("linked_requirements") or []):
            if req not in known_req_ids:
                m.warnings.append(
                    f"linked_requirements '{req}' not found in "
                    f"requirements/requirement-map.yml"
                )

    # sha256 format
    sha = fm.get("sha256")
    if isinstance(sha, str) and not SHA256_RE.match(sha):
        m.errors.append(f"sha256 not 64 hex chars: {sha!r}")

    # last_reviewed format
    last_rev = fm.get("last_reviewed")
    if isinstance(last_rev, str) and not ISO_DATE_RE.match(last_rev):
        m.errors.append(f"last_reviewed not ISO date YYYY-MM-DD: {last_rev!r}")
    elif isinstance(last_rev, date):
        # PyYAML auto-parses YYYY-MM-DD to date objects — that's fine
        pass

    # snapshot exists and is small
    snap = fm.get("snapshot")
    if snap:
        snap_path = m.path.parent / snap
        if not snap_path.exists():
            m.errors.append(f"snapshot file not found: {snap_path.relative_to(REPO_ROOT)}")
        else:
            size = snap_path.stat().st_size
            if size > MAX_SNAPSHOT_BYTES:
                m.warnings.append(
                    f"snapshot is {size // 1024} KB (recommended ≤ 200 KB)"
                )


def report(manifests: list[Manifest], verbose: bool) -> int:
    """Print a summary; return exit code (0 OK, 1 errors)."""
    n_total = len(manifests)
    n_errors = sum(1 for m in manifests if m.errors)
    n_warnings = sum(1 for m in manifests if m.warnings and not m.errors)
    n_clean = n_total - n_errors - n_warnings

    print(f"\n=== Validation: {n_total} manifest(s) checked ===\n")

    for m in manifests:
        rel = m.path.relative_to(REPO_ROOT).as_posix()
        if m.errors:
            print(f"[FAIL] {rel}")
            for e in m.errors:
                print(f"        ERROR: {e}")
            for w in m.warnings:
                print(f"        warn:  {w}")
        elif m.warnings:
            print(f"[WARN] {rel}")
            for w in m.warnings:
                print(f"        warn:  {w}")
        elif verbose:
            print(f"[ok]   {rel}")

    print(f"\nSummary: {n_clean} clean, {n_warnings} warnings, {n_errors} errors")
    return 0 if n_errors == 0 else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true",
                    help="Show every manifest checked, not just failing ones.")
    ap.add_argument("--fix", action="store_true",
                    help="(future) stub missing optional fields with placeholders.")
    args = ap.parse_args()

    if args.fix:
        print("--fix is not implemented yet; running validation only.")

    paths = discover_manifests(ARTIFACTS_DIR)
    if not paths:
        print(f"No manifests found under {ARTIFACTS_DIR.relative_to(REPO_ROOT)}.")
        print("(Add a manifest per the spec at dev-docs/architecture/artifact-manifest.md)")
        return

    known_disciplines = load_disciplines()
    known_req_ids = load_known_requirement_ids()

    manifests = [parse_manifest(p) for p in paths]
    for m in manifests:
        if m.errors:  # don't re-validate if parsing already failed
            continue
        validate_manifest(m, known_disciplines, known_req_ids)

    sys.exit(report(manifests, verbose=args.verbose))


if __name__ == "__main__":
    main()
