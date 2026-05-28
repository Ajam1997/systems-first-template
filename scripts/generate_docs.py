#!/usr/bin/env python3
"""Regenerate auto-managed sections of dev-docs/ from GitHub Issues.

Rule 2 of METHODOLOGY.md: docs render from Issues. This script is the
renderer. Reads:

  config/disciplines.yml      — active disciplines (for future filtering)
  config/evidence-kinds.yml   — valid V&V evidence vocabulary
  requirements/requirement-map.yml — UN → FR/NFR/IF/KPM decomposition

Writes into the AUTO sentinels of:

  dev-docs/living-user-needs.md      — UN list with status and decomp
  dev-docs/photonforge-architecture.md (or generic: dev-docs/architecture-doc.md)
                                       — FR / NFR / IF / KPM tables +
                                         V&V matrix
  dev-docs/roadmap.md                — milestone-driven stage table
  dev-docs/kpm-dashboard.md          — KPM-only table

Edits outside AUTO sentinels survive. Edits inside lose on next run.

Usage:
  python -m scripts.generate_docs

Env:
  GITHUB_TOKEN   — required
  REPO_OWNER     — optional; auto-detected from git remote
  REPO_NAME      — optional; auto-detected from git remote
"""
import re
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.github_client import GitHubClient

REPO_ROOT = Path(__file__).parent.parent
DOCS = REPO_ROOT / "dev-docs"
CONFIG = REPO_ROOT / "config"
REQUIREMENTS = REPO_ROOT / "requirements"

# Backward-compat for callers that previously expected `SCRIPTS` constant.
SCRIPTS = REPO_ROOT / "scripts"


def _extract_id(title: str) -> str:
    """Extract ID from title like '[UN-001] Title' -> 'UN-001'"""
    m = re.match(r"\[([A-Z]+-[\d.]+)\]", title)
    return m.group(1) if m else title


def _get_label(issue: dict, prefix: str) -> str:
    """Get label value by prefix, e.g. 'status: ' -> 'defined'"""
    for label in issue.get("labels", []):
        if label["name"].startswith(prefix):
            return label["name"].removeprefix(prefix)
    return ""


def _body_field(body: str, field: str) -> str:
    """Extract field value from issue body like '**Field:** value' -> 'value'"""
    m = re.search(rf"\*\*{re.escape(field)}:\*\*\s*(.+?)(?=\n\n|\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def _body_list_field(body: str, field: str) -> list[str]:
    """Extract a bullet-list field. Example:

        **Verified By:**
        - pytest: tests/test_sharpness.py::test_x
        - pytest: tests/test_sharpness.py::test_y

    Returns ["pytest: tests/test_sharpness.py::test_x", "pytest: tests/test_sharpness.py::test_y"].
    Blank line or next `**Field:**` heading ends the section.
    """
    pattern = rf"\*\*{re.escape(field)}:\*\*\s*\n((?:[ \t]*-\s*.+\n?)+)"
    m = re.search(pattern, body)
    if not m:
        return []
    items: list[str] = []
    for line in m.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


def render_user_needs_section(
    issues: list[dict],
    fr_issues: list[dict],
    nfr_issues: list[dict],
    req_map: dict,
) -> str:
    """Render UN-XXX list with acceptance, KPM, stage, status, and FR/NFR decomposition."""
    fr_index = {_extract_id(i["title"]): i for i in fr_issues}
    nfr_index = {_extract_id(i["title"]): i for i in nfr_issues}
    un_decomp = req_map.get("user_needs", {})

    lines = []
    for issue in sorted(issues, key=lambda i: _extract_id(i["title"])):
        un_id = _extract_id(issue["title"])
        title = issue["title"].split("] ", 1)[1] if "] " in issue["title"] else issue["title"]
        status = _get_label(issue, "status: ").upper() or "DEFINED"
        stage = _get_label(issue, "stage: ") or "?"
        acceptance = _body_field(issue["body"], "Acceptance")
        kpm = _body_field(issue["body"], "KPM") or "NONE"
        url = issue["html_url"]
        lines.append(f"[{un_id}]({url}): {title}")
        lines.append(f"Acceptance: {acceptance}")
        lines.append(f"KPM: {kpm}")
        lines.append(f"Stage: {stage}")
        lines.append(f"Status: {status}")

        decomp = un_decomp.get(un_id, {})
        parts = []
        for fr_id in decomp.get("functional_requirements", []):
            fr = fr_index.get(fr_id)
            if fr:
                parts.append(f"[{fr_id}]({fr['html_url']})")
        for nfr_id in decomp.get("non_functional_requirements", []):
            nfr = nfr_index.get(nfr_id)
            if nfr:
                parts.append(f"[{nfr_id}]({nfr['html_url']})")
        if parts:
            lines.append(f"Decomposes to: {', '.join(parts)}")

        lines.append("")
    return "\n".join(lines)


def render_fr_table(issues: list[dict]) -> str:
    """Render FR table with ID, description, implementation, status."""
    rows = ["| ID | Description | Implementation | Status |",
            "|:---|:---|:---|:---|"]
    for issue in sorted(issues, key=lambda i: _extract_id(i["title"])):
        fr_id = _extract_id(issue["title"])
        desc = issue["title"].split("] ", 1)[1] if "] " in issue["title"] else issue["title"]
        impl = _body_field(issue["body"], "Implementation")
        status = _get_label(issue, "status: ").upper() or "DEFINED"
        url = issue["html_url"]
        rows.append(f"| [{fr_id}]({url}) | {desc} | {impl} | {status} |")
    return "\n".join(rows)


def render_nfr_table(issues: list[dict]) -> str:
    """Render NFR table with ID, description, specification, status."""
    rows = ["| ID | Description | Specification | Status |",
            "|:---|:---|:---|:---|"]
    for issue in sorted(issues, key=lambda i: _extract_id(i["title"])):
        nfr_id = _extract_id(issue["title"])
        desc = issue["title"].split("] ", 1)[1] if "] " in issue["title"] else issue["title"]
        spec = _body_field(issue["body"], "Specification")
        status = _get_label(issue, "status: ").upper() or "DEFINED"
        url = issue["html_url"]
        rows.append(f"| [{nfr_id}]({url}) | {desc} | {spec} | {status} |")
    return "\n".join(rows)


def render_if_table(issues: list[dict]) -> str:
    """Render Interface Requirement table: ID, sides, what crosses, status."""
    rows = ["| ID | Side A | Side B | What crosses | Status |",
            "|:---|:---|:---|:---|:---|"]
    for issue in sorted(issues, key=lambda i: _extract_id(i["title"])):
        if_id = _extract_id(issue["title"])
        body = issue.get("body") or ""
        side_a = _body_field(body, "Side A") or "—"
        side_b = _body_field(body, "Side B") or "—"
        crosses = _body_field(body, "What Crosses") or "—"
        status = _get_label(issue, "status: ").upper() or "DEFINED"
        url = issue["html_url"]
        rows.append(f"| [{if_id}]({url}) | {side_a} | {side_b} | {crosses} | {status} |")
    return "\n".join(rows)


def render_kpm_table(issues: list[dict]) -> str:
    """Render KPM table with metric, target, owner, verified by, last measured, status."""
    rows = ["| KPM | Metric | Target | Owner | Verified By | Last Measured | Status |",
            "|:---|:---|:---|:---|:---|:---|:---|"]
    for issue in sorted(issues, key=lambda i: _extract_id(i["title"])):
        kpm_id = _extract_id(issue["title"])
        metric = issue["title"].split("] ", 1)[1] if "] " in issue["title"] else issue["title"]
        target = _body_field(issue["body"], "Target")
        owner = _body_field(issue["body"], "Owner")
        verified_by = _body_field(issue["body"], "Verified By")
        last = _body_field(issue["body"], "Last Measured") or "untested"
        status = _body_field(issue["body"], "Status") or "untested"
        url = issue["html_url"]
        rows.append(f"| [{kpm_id}]({url}) | {metric} | {target} | {owner} | {verified_by} | {last} | {status} |")
    return "\n".join(rows)


def render_vv_matrix(
    un_issues: list[dict],
    fr_issues: list[dict],
    nfr_issues: list[dict],
    if_issues: list[dict],
    kpm_issues: list[dict],
) -> str:
    """Render the V&V matrix table.

    Columns: ID · Type · Verified By · Validated By · Coverage
    Coverage flags: ✓ verified+validated, ⚠ partial, ✗ neither (unverified).
    """
    rows = [
        "| ID | Type | Verified By | Validated By | Coverage |",
        "|:---|:---|:---|:---|:---:|",
    ]

    def coverage(verified: list[str], validated: list[str], req_type: str) -> str:
        # UNs derive verification from children — no direct check here.
        # KPMs are self-validating.
        if req_type == "user-need":
            return "✓" if validated else "⚠"
        if req_type == "kpm":
            return "✓" if verified else "✗"
        if verified and validated:
            return "✓"
        if verified or validated:
            return "⚠"
        return "✗"

    def row_for(issue: dict, req_type_label: str, req_type_key: str) -> str:
        req_id = _extract_id(issue["title"])
        body = issue.get("body", "") or ""
        verified = _body_list_field(body, "Verified By")
        validated = _body_list_field(body, "Validated By")
        cov = coverage(verified, validated, req_type_key)
        v_cell = "<br>".join(f"`{x}`" for x in verified) if verified else "—"
        va_cell = "<br>".join(f"`{x}`" for x in validated) if validated else "—"
        url = issue["html_url"]
        return f"| [{req_id}]({url}) | {req_type_label} | {v_cell} | {va_cell} | {cov} |"

    grouped = (
        [(i, "UN", "user-need") for i in sorted(un_issues, key=lambda i: _extract_id(i["title"]))]
        + [(i, "FR", "fr") for i in sorted(fr_issues, key=lambda i: _extract_id(i["title"]))]
        + [(i, "NFR", "nfr") for i in sorted(nfr_issues, key=lambda i: _extract_id(i["title"]))]
        + [(i, "IF", "if") for i in sorted(if_issues, key=lambda i: _extract_id(i["title"]))]
        + [(i, "KPM", "kpm") for i in sorted(kpm_issues, key=lambda i: _extract_id(i["title"]))]
    )
    for issue, label, key in grouped:
        rows.append(row_for(issue, label, key))

    # Footer: coverage summary
    total = len(grouped)
    full = sum(
        1 for issue, _, key in grouped
        if coverage(_body_list_field(issue.get("body") or "", "Verified By"),
                    _body_list_field(issue.get("body") or "", "Validated By"),
                    key) == "✓"
    )
    rows.append("")
    rows.append(f"_Coverage: **{full} / {total}** requirements fully verified+validated. "
                f"Format spec: `dev-docs/architecture/vv-matrix.md`. "
                f"Evidence vocabulary: `config/evidence-kinds.yml`._")
    return "\n".join(rows)


_STAGE_TITLE_RE = re.compile(r"^Stage\s+(\d+)\b")


def render_roadmap_section(milestones: list[dict]) -> str:
    """Render roadmap table from GitHub Milestones (post Increment 3 migration).

    Each milestone titled like "Stage N — Title" becomes one row.
    Status is derived from milestone state + open/closed counts:
      - "Done"        — milestone state == "closed"
      - "In Progress" — milestone state == "open", any issues closed
      - "Not Started" — milestone state == "open", zero issues closed
    """
    lines = ["| Stage | Title | Status | Progress |", "|:---|:---|:---|:---|"]
    stage_entries: list[tuple[int, str]] = []
    for ms in milestones:
        m = _STAGE_TITLE_RE.match(ms.get("title", ""))
        if not m:
            continue
        stage_num = int(m.group(1))
        title = ms["title"]
        url = ms["html_url"]
        open_count = ms.get("open_issues", 0)
        closed_count = ms.get("closed_issues", 0)
        total = open_count + closed_count
        if ms.get("state") == "closed":
            status = "Done"
        elif closed_count > 0:
            status = "In Progress"
        else:
            status = "Not Started"
        progress = f"{closed_count}/{total}" if total else "—"
        stage_entries.append(
            (stage_num, f"| {stage_num} | [{title}]({url}) | {status} | {progress} |")
        )
    for _, row in sorted(stage_entries):
        lines.append(row)
    return "\n".join(lines)


def inject_auto_section(text: str, key: str, content: str) -> str:
    """Replace content between AUTO markers with new content."""
    pattern = rf"(<!-- AUTO:{re.escape(key)} -->)(.*?)(<!-- /AUTO:{re.escape(key)} -->)"
    if not re.search(pattern, text, re.DOTALL):
        raise ValueError(f"Markers AUTO:{key} not found in document")
    return re.sub(pattern, rf"\1\n{content}\n\3", text, flags=re.DOTALL)


def _maybe_inject(text: str, key: str, content: str) -> str:
    """Inject if the AUTO sentinel exists; silently skip if not.

    Lets a template installation render whatever sentinels the project
    has opted in to, without requiring every doc to carry every section.
    """
    pattern = rf"<!-- AUTO:{re.escape(key)} -->"
    if not re.search(pattern, text):
        return text
    return inject_auto_section(text, key, content)


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def main() -> None:
    """Fetch issues from GitHub and regenerate living docs."""
    client = GitHubClient()

    # Requirement map: prefer requirements/requirement-map.yml (canonical
    # location in this template); fall back to scripts/requirement_map.yml
    # (PHOTONForge legacy location) for projects that haven't migrated.
    req_map_paths = [
        REQUIREMENTS / "requirement-map.yml",
        SCRIPTS / "requirement_map.yml",
    ]
    req_map = next(
        (_read_yaml(p) for p in req_map_paths if p.exists()),
        {"stages": {}, "user_needs": {}},
    )

    print("Fetching Issues from GitHub...")
    un_issues = client.list_issues(labels="type: user-need", state="all")
    fr_issues = client.list_issues(labels="type: fr", state="all")
    nfr_issues = client.list_issues(labels="type: nfr", state="all")
    if_issues = client.list_issues(labels="type: if", state="all")
    kpm_issues = client.list_issues(labels="type: kpm", state="all")
    milestones = client.list_milestones(state="all")
    print(f"  UN={len(un_issues)} FR={len(fr_issues)} NFR={len(nfr_issues)} "
          f"IF={len(if_issues)} KPM={len(kpm_issues)} milestones={len(milestones)}")

    # Regenerate living-user-needs.md
    un_path = DOCS / "living-user-needs.md"
    if un_path.exists():
        text = un_path.read_text(encoding="utf-8")
        text = _maybe_inject(
            text, "user_needs",
            render_user_needs_section(un_issues, fr_issues, nfr_issues, req_map),
        )
        un_path.write_text(text, encoding="utf-8")
        print(f"Updated {un_path}")

    # Regenerate architecture doc — try generic name first, then project-specific.
    arch_candidates = [DOCS / "architecture-doc.md", DOCS / "photonforge-architecture.md"]
    arch_path = next((p for p in arch_candidates if p.exists()), None)
    if arch_path:
        text = arch_path.read_text(encoding="utf-8")
        text = _maybe_inject(text, "fr_table", render_fr_table(fr_issues))
        text = _maybe_inject(text, "nfr_table", render_nfr_table(nfr_issues))
        text = _maybe_inject(text, "if_table", render_if_table(if_issues))
        text = _maybe_inject(text, "kpm_table", render_kpm_table(kpm_issues))
        text = _maybe_inject(
            text, "vv_matrix",
            render_vv_matrix(un_issues, fr_issues, nfr_issues, if_issues, kpm_issues),
        )
        arch_path.write_text(text, encoding="utf-8")
        print(f"Updated {arch_path}")

    # Regenerate roadmap page
    roadmap_path = DOCS / "roadmap.md"
    if roadmap_path.exists():
        text = roadmap_path.read_text(encoding="utf-8")
        text = inject_auto_section(text, "roadmap", render_roadmap_section(milestones))
        roadmap_path.write_text(text, encoding="utf-8")
        print(f"Updated {roadmap_path}")

    # Regenerate KPM dashboard page
    kpm_page_path = DOCS / "kpm-dashboard.md"
    if kpm_page_path.exists():
        text = kpm_page_path.read_text(encoding="utf-8")
        text = inject_auto_section(text, "kpm_table", render_kpm_table(kpm_issues))
        kpm_page_path.write_text(text, encoding="utf-8")
        print(f"Updated {kpm_page_path}")

    print("Done.")


if __name__ == "__main__":
    main()
