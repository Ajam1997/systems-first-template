#!/usr/bin/env python3
"""Sync repo labels to .github/labels.yml.

Reconciles the live GitHub repo labels to the canonical set declared in
.github/labels.yml. Plays the same role as Financial-Times/github-label-sync
but uses only `gh` + PyYAML — no Node dependency.

Operations:
  - Creates any label in labels.yml that doesn't exist on the repo
  - Updates color/description of labels whose attributes drift
  - Deletes labels on the repo that aren't in labels.yml
    (use --allow-extra to keep them)

Usage:
  python scripts/sync_labels.py --dry-run         # preview only
  python scripts/sync_labels.py                   # apply
  python scripts/sync_labels.py --allow-extra     # don't delete unmanaged labels

Repo identity:
  Resolved from REPO_OWNER + REPO_NAME env vars, or auto-detected from
  `git config remote.origin.url`. Same convention as the other scripts.

Auth:
  Uses `gh` CLI (must be authenticated via `gh auth login`). No tokens
  in this script's argv or env. Falls back to GH_TOKEN / GITHUB_TOKEN
  if `gh` is missing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
LABELS_PATH = REPO_ROOT / ".github" / "labels.yml"


def _resolve_repo() -> str:
    owner = os.environ.get("REPO_OWNER")
    repo = os.environ.get("REPO_NAME")
    if owner and repo:
        return f"{owner}/{repo}"
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
        if m:
            return f"{m.group(1)}/{m.group(2)}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    raise SystemExit(
        "Cannot resolve repo. Set REPO_OWNER + REPO_NAME or run from a "
        "git checkout with origin pointed at github.com."
    )


def _gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a `gh` subcommand. Caller passes args after `gh`."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.stderr.write(f"gh {' '.join(args)} failed:\n{result.stderr}\n")
        sys.exit(1)
    return result


def list_remote_labels(repo: str) -> list[dict]:
    """Return current repo labels via `gh api`."""
    labels: list[dict] = []
    page = 1
    while True:
        result = _gh([
            "api",
            f"repos/{repo}/labels",
            "-X", "GET",
            "-F", "per_page=100",
            "-F", f"page={page}",
        ])
        batch = json.loads(result.stdout)
        if not batch:
            break
        labels.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return labels


def load_desired_labels(path: Path) -> list[dict]:
    """Parse labels.yml. Accepts a top-level list or `{labels: [...]}` shape."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "labels" in data:
        data = data["labels"]
    if not isinstance(data, list):
        raise SystemExit(f"{path}: expected a list of label objects")
    out: list[dict] = []
    for item in data:
        if not isinstance(item, dict) or "name" not in item:
            raise SystemExit(f"{path}: label entry missing `name`: {item!r}")
        out.append({
            "name": item["name"],
            "color": str(item.get("color", "ededed")).lstrip("#"),
            "description": item.get("description", ""),
        })
    return out


def reconcile(desired: list[dict], existing: list[dict], allow_extra: bool):
    """Return (creates, updates, deletes) lists of label dicts."""
    existing_by_name = {l["name"]: l for l in existing}
    desired_by_name = {l["name"]: l for l in desired}

    creates = [d for d in desired if d["name"] not in existing_by_name]
    deletes = [] if allow_extra else [
        e for e in existing if e["name"] not in desired_by_name
    ]

    updates: list[tuple[dict, dict]] = []  # (desired, current)
    for d in desired:
        cur = existing_by_name.get(d["name"])
        if not cur:
            continue
        cur_color = (cur.get("color") or "").lstrip("#").lower()
        cur_desc = cur.get("description") or ""
        if cur_color != d["color"].lower() or cur_desc != d["description"]:
            updates.append((d, cur))

    return creates, updates, deletes


def print_plan(creates, updates, deletes):
    print("=== Label Sync Plan ===")
    if creates:
        print(f"\n+ Creating {len(creates)} label(s):")
        for c in creates:
            print(f"  + {c['name']:<28} (color: {c['color']})")
    if updates:
        print(f"\n~ Updating {len(updates)} label(s):")
        for d, cur in updates:
            cur_color = (cur.get('color') or '').lstrip('#').lower()
            cur_desc = cur.get('description') or ''
            changes = []
            if cur_color != d["color"].lower():
                changes.append(f"color {cur_color}->{d['color']}")
            if cur_desc != d["description"]:
                old = (cur_desc[:25] + "…") if len(cur_desc) > 25 else cur_desc
                new = (d['description'][:25] + "…") if len(d['description']) > 25 else d['description']
                changes.append(f"desc '{old}'->'{new}'")
            print(f"  ~ {d['name']:<28} ({'; '.join(changes)})")
    if deletes:
        print(f"\n- Deleting {len(deletes)} unmanaged label(s):")
        for e in deletes:
            print(f"  - {e['name']}")
    if not (creates or updates or deletes):
        print("\n(no changes needed)")
    print()


def apply_changes(repo: str, creates, updates, deletes):
    """Apply the plan via gh api."""
    import urllib.parse

    for c in creates:
        _gh([
            "api", "-X", "POST",
            f"repos/{repo}/labels",
            "-f", f"name={c['name']}",
            "-f", f"color={c['color']}",
            "-f", f"description={c['description']}",
        ])
        print(f"  + created  {c['name']}")
    for d, _ in updates:
        encoded = urllib.parse.quote(d["name"], safe="")
        _gh([
            "api", "-X", "PATCH",
            f"repos/{repo}/labels/{encoded}",
            "-f", f"new_name={d['name']}",
            "-f", f"color={d['color']}",
            "-f", f"description={d['description']}",
        ])
        print(f"  ~ updated  {d['name']}")
    for e in deletes:
        encoded = urllib.parse.quote(e["name"], safe="")
        _gh(["api", "-X", "DELETE", f"repos/{repo}/labels/{encoded}"])
        print(f"  - deleted  {e['name']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan and exit without making any changes.")
    ap.add_argument("--allow-extra", action="store_true",
                    help="Do not delete labels that aren't in labels.yml.")
    ap.add_argument("--labels", default=str(LABELS_PATH),
                    help=f"Path to labels.yml (default: {LABELS_PATH}).")
    args = ap.parse_args()

    repo = _resolve_repo()
    print(f"Repo: {repo}")
    print(f"Labels source: {args.labels}\n")

    desired = load_desired_labels(Path(args.labels))
    existing = list_remote_labels(repo)
    print(f"Desired: {len(desired)} label(s) in YAML")
    print(f"Existing: {len(existing)} label(s) on repo")

    creates, updates, deletes = reconcile(desired, existing, args.allow_extra)
    print_plan(creates, updates, deletes)

    if args.dry_run:
        print("(--dry-run — no changes applied)")
        return
    if not (creates or updates or deletes):
        return

    apply_changes(repo, creates, updates, deletes)
    print("\nDone.")


if __name__ == "__main__":
    main()
