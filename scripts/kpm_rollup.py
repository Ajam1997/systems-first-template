#!/usr/bin/env python3
"""Aggregate child KPM measurements into parent KPM values.

This is the V-model rollup engine. Reads the KPM tree declared in
`requirements/requirement-map.yml`, collects the latest measurements
for each leaf KPM from its GitHub Issue, applies the aggregation
function for each non-leaf, and posts the computed value back to the
parent's Issue.

Aggregation patterns supported:
  independent  — leaf; measured directly, never computed
  sum          — parent = Σ children's measured values
  max          — parent = max of children
  min          — parent = min of children

After running, every non-independent KPM Issue carries a fresh
comment with the rolled-up value, pass/fail vs target, and links to
the contributing children.

Usage:
  python scripts/kpm_rollup.py --dry-run   # print plan, no posts
  python scripts/kpm_rollup.py             # apply

Env:
  GITHUB_TOKEN — required
  REPO_OWNER, REPO_NAME — optional; auto-detected from git remote
"""
from __future__ import annotations

import argparse
import operator
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 stdout/stderr so rollup status glyphs render on cp1252 consoles.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.github_client import GitHubClient

REPO_ROOT = Path(__file__).parent.parent
REQ_MAP_PATH = REPO_ROOT / "requirements" / "requirement-map.yml"

OPS = {"<=": operator.le, ">=": operator.ge, "==": operator.eq,
       "<": operator.lt, ">": operator.gt}


@dataclass
class KPM:
    id: str
    target_value: float | None
    target_op: str
    unit: str
    aggregation: str  # independent | sum | max | min
    aggregates_from: list[str] = field(default_factory=list)
    margin_target: float = 0.0
    # Resolved at runtime:
    measured_value: float | None = None
    issue_number: int | None = None


def load_kpm_tree(path: Path = REQ_MAP_PATH) -> dict[str, KPM]:
    """Load KPMs from requirement-map.yml. Returns id -> KPM."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("kpms") or {}
    if not isinstance(raw, dict):
        raise SystemExit(f"{path}: expected `kpms:` to be a dict; got {type(raw).__name__}")
    tree: dict[str, KPM] = {}
    for kid, fields in raw.items():
        if not isinstance(fields, dict):
            raise SystemExit(f"{path}: kpms.{kid} must be a mapping")
        tree[kid] = KPM(
            id=kid,
            target_value=fields.get("target_value"),
            target_op=fields.get("target_op", "<="),
            unit=fields.get("unit", ""),
            aggregation=fields.get("aggregation", "independent"),
            aggregates_from=list(fields.get("aggregates_from") or []),
            margin_target=float(fields.get("margin_target") or 0.0),
        )
    return tree


def validate_tree(tree: dict[str, KPM]) -> list[str]:
    """Return a list of error messages; empty means valid."""
    errors: list[str] = []
    valid_ops = {"independent", "sum", "max", "min"}
    for kid, kpm in tree.items():
        if kpm.aggregation not in valid_ops:
            errors.append(f"{kid}: unknown aggregation '{kpm.aggregation}'")
        if kpm.aggregation == "independent":
            if kpm.aggregates_from:
                errors.append(f"{kid}: independent KPMs must not have aggregates_from")
        else:
            if not kpm.aggregates_from:
                errors.append(f"{kid}: aggregation '{kpm.aggregation}' requires aggregates_from")
            for child in kpm.aggregates_from:
                if child not in tree:
                    errors.append(f"{kid}: aggregates_from references unknown KPM {child}")
    # Cycle detection
    visited: dict[str, int] = {}  # 0=unvisited, 1=in progress, 2=done
    def visit(kid: str, stack: list[str]) -> None:
        st = visited.get(kid, 0)
        if st == 2:
            return
        if st == 1:
            errors.append(f"cycle detected: {' -> '.join(stack + [kid])}")
            return
        visited[kid] = 1
        for child in tree.get(kid, KPM(kid, None, "<=", "", "independent")).aggregates_from:
            if child in tree:
                visit(child, stack + [kid])
        visited[kid] = 2
    for kid in tree:
        visit(kid, [])
    return errors


def topo_sort(tree: dict[str, KPM]) -> list[str]:
    """Return KPM IDs in dependency order: leaves first, roots last."""
    order: list[str] = []
    visited: set[str] = set()
    def visit(kid: str):
        if kid in visited or kid not in tree:
            return
        visited.add(kid)
        for child in tree[kid].aggregates_from:
            visit(child)
        order.append(kid)
    for kid in sorted(tree):
        visit(kid)
    return order


_NUM_RE = re.compile(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?")


def parse_measurement(text: str) -> float | None:
    """Extract the first numeric value from a measurement string.

    `1.83 GB on i7-7500U — 2026-05-23` -> 1.83
    `47.2 W peak`                       -> 47.2
    Returns None if no number found.
    """
    if not text:
        return None
    m = _NUM_RE.search(text)
    return float(m.group()) if m else None


def fetch_latest_measurement(client: GitHubClient, issue_number: int) -> str | None:
    """Find the most recent `## KPM Update` comment on the Issue and
    extract the measurement string between backticks.

    Comments are posted by scripts/github_comment.py update-kpm; their
    body contains a line like:
      **KPM-1.2** - `1.83 GB on i7-7500U` - **passing**
    """
    # Issues comments endpoint; sort newest first for cheap recency
    r = client._session.get(
        f"{client.REST_BASE}/repos/{client.owner}/{client.repo}/issues/{issue_number}/comments",
        params={"per_page": 100, "sort": "created", "direction": "desc"},
    )
    r.raise_for_status()
    for comment in r.json():
        body = comment.get("body") or ""
        if "KPM Update" not in body:
            continue
        m = re.search(r"`([^`]+)`", body)
        if m:
            return m.group(1)
    return None


def resolve_issue_numbers(client: GitHubClient, tree: dict[str, KPM]) -> None:
    """Populate `issue_number` on each KPM via title search."""
    for kid, kpm in tree.items():
        found = client.find_issue_by_title(f"[{kid}]")
        if found:
            kpm.issue_number = found["number"]


def collect_leaf_measurements(client: GitHubClient, tree: dict[str, KPM]) -> None:
    """Fetch the latest measurement for every leaf KPM."""
    for kpm in tree.values():
        if kpm.aggregation != "independent":
            continue
        if kpm.issue_number is None:
            continue
        raw = fetch_latest_measurement(client, kpm.issue_number)
        kpm.measured_value = parse_measurement(raw) if raw else None


def aggregate(tree: dict[str, KPM]) -> dict[str, tuple[float | None, list[str]]]:
    """Compute measured_value for every non-independent KPM.

    Returns dict of kpm_id -> (computed_value, list_of_missing_children).
    Missing children -> computed_value=None, names listed.
    """
    results: dict[str, tuple[float | None, list[str]]] = {}
    for kid in topo_sort(tree):
        kpm = tree[kid]
        if kpm.aggregation == "independent":
            results[kid] = (kpm.measured_value, [])
            continue
        child_values: list[float] = []
        missing: list[str] = []
        for child_id in kpm.aggregates_from:
            child = tree.get(child_id)
            if child is None or child.measured_value is None:
                missing.append(child_id)
            else:
                child_values.append(child.measured_value)
        if missing:
            results[kid] = (None, missing)
            continue
        if kpm.aggregation == "sum":
            value = sum(child_values)
        elif kpm.aggregation == "max":
            value = max(child_values)
        elif kpm.aggregation == "min":
            value = min(child_values)
        else:
            results[kid] = (None, [f"unknown aggregation '{kpm.aggregation}'"])
            continue
        kpm.measured_value = value
        results[kid] = (value, [])
    return results


def evaluate_pass_fail(kpm: KPM) -> str | None:
    """Return 'passing' | 'failing' | 'margin-warning' | None (unmeasured)."""
    if kpm.measured_value is None or kpm.target_value is None:
        return None
    op = OPS.get(kpm.target_op)
    if op is None:
        return None
    passes = op(kpm.measured_value, kpm.target_value)
    if not passes:
        return "failing"
    # Margin check (only meaningful for <= or >= targets)
    if kpm.margin_target > 0 and kpm.target_op in ("<=", ">="):
        if kpm.target_op == "<=":
            # warning if measured > target * (1 - margin)
            threshold = kpm.target_value * (1.0 - kpm.margin_target)
            if kpm.measured_value > threshold:
                return "margin-warning"
        else:  # >=
            threshold = kpm.target_value * (1.0 + kpm.margin_target)
            if kpm.measured_value < threshold:
                return "margin-warning"
    return "passing"


def format_rollup_comment(kpm: KPM, tree: dict[str, KPM], missing: list[str]) -> str:
    """Build the comment body to post on a non-independent KPM."""
    status = evaluate_pass_fail(kpm) or "unmeasured"
    icon = {"passing": "[ok]", "failing": "[FAIL]",
            "margin-warning": "[WARN]", "unmeasured": "-"}[status]
    value_str = (f"{kpm.measured_value:g} {kpm.unit}" if kpm.measured_value is not None
                 else "—")
    target_str = (f"{kpm.target_op} {kpm.target_value:g} {kpm.unit}"
                  if kpm.target_value is not None else "—")
    lines = [
        f"## KPM Rollup ({kpm.aggregation}) — {icon} {status}",
        "",
        f"**{kpm.id}**  -  computed: `{value_str}`  -  target: `{target_str}`",
        "",
        "**Contributing children:**",
    ]
    for child_id in kpm.aggregates_from:
        child = tree.get(child_id)
        if child is None:
            lines.append(f"  - `{child_id}` *(not in tree)*")
            continue
        v = (f"{child.measured_value:g} {child.unit}"
             if child.measured_value is not None else "no measurement")
        lines.append(f"  - `{child_id}`: {v}")
    if missing:
        lines.append("")
        lines.append(f"**Missing measurements:** {', '.join(missing)}")
    lines.append("")
    lines.append("*via: @kpm_rollup*")
    return "\n".join(lines)


def post_rollup(client: GitHubClient, kpm: KPM, body: str, dry_run: bool) -> None:
    if kpm.issue_number is None:
        print(f"  {kpm.id}: Issue not found; skipping post")
        return
    if dry_run:
        print(f"  [dry-run] would post on {kpm.id} (#{kpm.issue_number})")
        return
    client.post_comment(kpm.issue_number, body)
    print(f"  posted rollup on {kpm.id} (#{kpm.issue_number})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan and exit without posting comments.")
    args = ap.parse_args()

    tree = load_kpm_tree()
    if not tree:
        print("No KPMs in requirement-map.yml. Nothing to roll up.")
        return

    errors = validate_tree(tree)
    if errors:
        sys.stderr.write("KPM tree validation errors:\n")
        for e in errors:
            sys.stderr.write(f"  - {e}\n")
        sys.exit(1)
    print(f"KPM tree: {len(tree)} KPM(s), no validation errors.")

    client = GitHubClient()
    resolve_issue_numbers(client, tree)
    unresolved = [k for k, v in tree.items() if v.issue_number is None]
    if unresolved:
        print(f"note: {len(unresolved)} KPM(s) have no matching Issue: {', '.join(unresolved)}")

    collect_leaf_measurements(client, tree)
    print("\nLeaf measurements:")
    for kid in sorted(tree):
        k = tree[kid]
        if k.aggregation != "independent":
            continue
        m = f"{k.measured_value:g} {k.unit}" if k.measured_value is not None else "—"
        print(f"  {kid:30s} {m}")

    aggregated = aggregate(tree)

    print("\nAggregated KPMs:")
    posts = 0
    for kid in topo_sort(tree):
        k = tree[kid]
        if k.aggregation == "independent":
            continue
        value, missing = aggregated[kid]
        status = evaluate_pass_fail(k) if value is not None else "unmeasured"
        v = f"{value:g} {k.unit}" if value is not None else "—"
        t = f"{k.target_op} {k.target_value:g} {k.unit}" if k.target_value is not None else "—"
        print(f"  {kid:30s} computed={v}  target={t}  status={status}")
        body = format_rollup_comment(k, tree, missing)
        post_rollup(client, k, body, args.dry_run)
        posts += 1

    print(f"\n{posts} rollup comment(s) {'planned' if args.dry_run else 'posted'}.")


if __name__ == "__main__":
    main()
