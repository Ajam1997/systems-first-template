#!/usr/bin/env python3
"""Export the requirement tree to SysMLv2 textual notation.

Reads `requirements/requirement-map.yml` (+ live GitHub Issue state for
titles and bodies, optional) and emits a single `.sysml` file describing
the project's requirements, interfaces, KPM constraints, and milestone
verification cases.

This is a **render target**, not a source of truth. Authoring stays in
GitHub Issues + YAML. The generated `.sysml` is for opening in Eclipse
Syson, Cameo, or any other SysMLv2-conformant tool when you want formal
validation, simulation, or vendor portability.

Mapping (see dev-docs/architecture/sysml-export.md for the full spec):

  YAML                          SysMLv2 element
  -----------------             ---------------------------------
  user_needs (UN-X)             requirement def UN_X
  functional_requirements       requirement def FR_X (:> parent UN)
  non_functional_requirements   requirement def NFR_X
  interface_requirements        interface def IF_X
  kpms                          constraint def KPM_X (with attributes)
    aggregation: sum/max/min      -> expression in constraint body
  stages                        verification case def Stage_N

Usage:
  python scripts/export_sysml.py                  # write model/system.sysml
  python scripts/export_sysml.py --stdout         # print to stdout
  python scripts/export_sysml.py --offline        # YAML only, skip Issue fetch
  python scripts/export_sysml.py --output PATH    # custom output path

Env:
  GITHUB_TOKEN — optional; required for live Issue body fetching
  REPO_OWNER, REPO_NAME — optional; auto-detected from git remote

Caveat: SysMLv2 textual notation is still evolving. Validate the output
against your target tool (Syson, Cameo, etc.) and tune the renderer
functions below if anything's rejected. The mapping is the stable part;
the syntax is the part most likely to need tuning.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Force UTF-8 stdout so the generated header arrows render on cp1252 consoles.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

import yaml

REPO_ROOT = Path(__file__).parent.parent
REQ_MAP_PATH = REPO_ROOT / "requirements" / "requirement-map.yml"
DEFAULT_OUTPUT = REPO_ROOT / "model" / "system.sysml"


# --- ID normalization ----------------------------------------------
# SysMLv2 identifiers can't contain hyphens or dots. Convert to underscores.

def sysml_id(req_id: str) -> str:
    return re.sub(r"[-.]+", "_", req_id)


# --- Issue body fetch (optional) -----------------------------------

@dataclass
class IssueInfo:
    title: str = ""
    body: str = ""


def fetch_issue_bodies(ids: list[str]) -> dict[str, IssueInfo]:
    """For each requirement ID, fetch the Issue title + body via gh CLI.

    Returns id -> IssueInfo. Missing Issues map to empty IssueInfo.
    Best-effort: failures are silent so --offline-style fallback works.
    """
    result: dict[str, IssueInfo] = {i: IssueInfo() for i in ids}
    for req_id in ids:
        try:
            r = subprocess.run(
                ["gh", "issue", "list", "--search", f"[{req_id}] in:title",
                 "--state", "all", "--json", "title,body", "--limit", "5"],
                capture_output=True, text=True, check=True,
            )
            import json as _json
            for issue in _json.loads(r.stdout):
                if f"[{req_id}]" in issue["title"]:
                    title = issue["title"].split("] ", 1)[-1].strip()
                    result[req_id] = IssueInfo(title=title, body=issue.get("body") or "")
                    break
        except Exception:
            continue
    return result


def _body_field(body: str, field_name: str) -> str:
    """Extract `**Field:** value` from an Issue body (same shape as generate_docs.py)."""
    m = re.search(rf"\*\*{re.escape(field_name)}:\*\*\s*(.+?)(?=\n\n|\Z)",
                  body, re.DOTALL)
    return m.group(1).strip() if m else ""


# --- Project metadata ----------------------------------------------

def resolve_project_name() -> str:
    """Best-effort name for the top-level package. Tries env, git remote, repo dir."""
    import os
    name = os.environ.get("REPO_NAME")
    if name:
        return _to_pascal(name)
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        m = re.search(r"github\.com[:/][^/]+/([^/.]+?)(?:\.git)?$", url)
        if m:
            return _to_pascal(m.group(1))
    except Exception:
        pass
    return _to_pascal(REPO_ROOT.name)


def _to_pascal(s: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[-_\s]+", s) if w)


# --- Renderers -----------------------------------------------------
# Each renderer produces a block of SysMLv2 text. Tune syntax here if the
# target tool rejects something — the mapping (what becomes what) is stable.

def render_header(project_name: str, source_path: Path) -> str:
    return (
        f"// AUTO-GENERATED by scripts/export_sysml.py — DO NOT HAND-EDIT.\n"
        f"// Source of truth: {source_path.relative_to(REPO_ROOT).as_posix()}\n"
        f"// Edit the YAML and re-run; this file regenerates from it.\n"
        f"// Mapping spec: dev-docs/architecture/sysml-export.md\n"
        f"\n"
        f"package {project_name} {{\n"
        f"\n"
        f"    // Bring SysMLv2 primitive scalar types (Real, String, Integer,\n"
        f"    // Boolean, etc.) into scope so attribute types resolve in Syson /\n"
        f"    // Cameo / any conformant parser.\n"
        f"    import ScalarValues::*;\n"
    )


def render_footer() -> str:
    return "}\n"


def render_doc(text: str, indent: str = "        ") -> str:
    """Render a `doc /* ... */` block, escaping comment terminators.

    Default indent is 8 spaces — one level inside the package block, which
    is itself indented 4. Callers can override for different nesting.
    """
    if not text:
        return ""
    safe = text.replace("*/", "* /").strip()
    return f"{indent}doc /* {safe} */\n"


def render_user_need(un_id: str, info: IssueInfo) -> str:
    sid = sysml_id(un_id)
    desc = info.title or un_id
    acceptance = _body_field(info.body, "Acceptance")
    body = acceptance or desc
    return (
        f"\n    // -- User Need: {un_id} --\n"
        f"    requirement def {sid} {{\n"
        f"{render_doc(body)}"
        f"    }}\n"
    )


def render_functional(fr_id: str, info: IssueInfo, parent_uns: list[str]) -> str:
    sid = sysml_id(fr_id)
    impl = _body_field(info.body, "Implementation")
    desc = info.title or fr_id
    body_text = f"{desc}. Implementation: {impl}" if impl else desc
    # «derive» = SysMLv2 specializes-from (`:>`)
    parents = ", ".join(sysml_id(u) for u in parent_uns)
    derives = f" :> {parents}" if parents else ""
    return (
        f"\n    // -- Functional Requirement: {fr_id} (derives from {', '.join(parent_uns) or '—'}) --\n"
        f"    requirement def {sid}{derives} {{\n"
        f"{render_doc(body_text)}"
        f"    }}\n"
    )


def render_non_functional(nfr_id: str, info: IssueInfo, parent_uns: list[str]) -> str:
    sid = sysml_id(nfr_id)
    spec = _body_field(info.body, "Specification")
    desc = info.title or nfr_id
    body_text = f"{desc}. Specification: {spec}" if spec else desc
    parents = ", ".join(sysml_id(u) for u in parent_uns)
    derives = f" :> {parents}" if parents else ""
    return (
        f"\n    // -- Non-Functional Requirement: {nfr_id} --\n"
        f"    requirement def {sid}{derives} {{\n"
        f"{render_doc(body_text)}"
        f"    }}\n"
    )


def render_interface(if_id: str, info: IssueInfo, parent_uns: list[str]) -> str:
    sid = sysml_id(if_id)
    side_a = _body_field(info.body, "Side A") or "side_a"
    side_b = _body_field(info.body, "Side B") or "side_b"
    crosses = _body_field(info.body, "What Crosses")
    contract = _body_field(info.body, "Contract")
    body_text = (
        f"{info.title or if_id}. "
        f"Side A: {side_a}. Side B: {side_b}."
        + (f" Crosses: {crosses}." if crosses else "")
        + (f" Contract: {contract}." if contract else "")
    )
    # SysMLv2: interfaces are typed via `interface def`. End types simplified.
    return (
        f"\n    // -- Interface Requirement: {if_id} --\n"
        f"    interface def {sid} {{\n"
        f"{render_doc(body_text)}"
        f"        end {sysml_id(side_a) or 'side_a'};\n"
        f"        end {sysml_id(side_b) or 'side_b'};\n"
        f"    }}\n"
    )


def render_kpm(kpm_id: str, kpm_entry: dict) -> str:
    """Render a KPM as a SysMLv2 constraint def with attribute attributes."""
    sid = sysml_id(kpm_id)
    target_value = kpm_entry.get("target_value")
    target_op = kpm_entry.get("target_op", "<=")
    unit = kpm_entry.get("unit") or ""
    aggregation = kpm_entry.get("aggregation", "independent")
    children = kpm_entry.get("aggregates_from") or []

    lines = [
        f"\n    // -- KPM: {kpm_id} (aggregation: {aggregation}) --",
        f"    constraint def {sid} {{",
    ]
    if target_value is not None:
        lines.append(f'        attribute target_value : Real = {target_value};')
        lines.append(f'        attribute target_op   : String = "{target_op}";')
    if unit:
        lines.append(f'        attribute unit        : String = "{unit}";')
    lines.append(f'        attribute aggregation : String = "{aggregation}";')
    if children:
        # Express the rollup as a comment for now — full SysMLv2 calc syntax
        # varies by tool; the script's authoritative form is requirement-map.yml.
        child_refs = ", ".join(sysml_id(c) for c in children)
        op_word = {"sum": "+", "max": "max", "min": "min"}.get(aggregation, aggregation)
        lines.append(f"        // rollup: this = {op_word}({child_refs})")
        for c in children:
            lines.append(f"        // child: {sysml_id(c)}")
    lines.append("    }")
    return "\n".join(lines) + "\n"


def render_verification_case(stage_num: int, stage_data: dict) -> str:
    """Render a stage milestone as a SysMLv2 verification case.

    Inside the case body, the requirements this case verifies are recorded
    as `// verifies:` comments rather than `verify <id>;` statements. The
    bare `verify` keyword inside a `verification case def` body is rejected
    by Syson (it's a verb used in a different syntactic position in
    SysMLv2). The comment form is unambiguous and round-trips through any
    tool. Authoritative verifies-relationship lives in
    requirements/requirement-map.yml + the GitHub Milestone link.
    """
    title = stage_data.get("title", f"Stage {stage_num}")
    safe = re.sub(r"[^A-Za-z0-9_]", "_", title)
    return (
        f"\n    // -- Verification Case: {title} --\n"
        f"    verification case def {safe} {{\n"
        f"{render_doc(title)}"
        + "".join(
            f"        // verifies: {sysml_id(un)}\n"
            for un in stage_data.get("user_needs", []) or []
        )
        + "    }\n"
    )


# --- Reverse-map helpers -------------------------------------------

def build_child_to_parents(req_map: dict) -> dict[str, list[str]]:
    """Map FR/NFR/IF/KPM ID -> list of parent UN IDs (preserving order)."""
    result: dict[str, list[str]] = {}
    for un_id, un_entry in (req_map.get("user_needs") or {}).items():
        if not isinstance(un_entry, dict):
            continue
        for field_name in ("functional_requirements",
                           "non_functional_requirements",
                           "interface_requirements",
                           "kpms"):
            for child_id in (un_entry.get(field_name) or []):
                result.setdefault(child_id, []).append(un_id)
    return result


# --- Main pipeline -------------------------------------------------

def export(req_map: dict, offline: bool) -> str:
    """Build the full SysMLv2 text and return it."""
    project_name = resolve_project_name()

    # Collect all requirement IDs we may want Issue bodies for
    un_ids = sorted((req_map.get("user_needs") or {}).keys())
    fr_ids = sorted((req_map.get("functional_requirements") or {}).keys())
    nfr_ids = sorted((req_map.get("non_functional_requirements") or {}).keys())
    if_ids = sorted((req_map.get("interface_requirements") or {}).keys())
    kpm_ids = sorted((req_map.get("kpms") or {}).keys())

    # Inferred FR/NFR/IFs from user_needs decomp that aren't in their own top-level dict
    child_parents = build_child_to_parents(req_map)
    for cid in child_parents:
        if cid.startswith("FR-") and cid not in fr_ids:
            fr_ids.append(cid)
        elif cid.startswith("NFR-") and cid not in nfr_ids:
            nfr_ids.append(cid)
        elif cid.startswith("IF-") and cid not in if_ids:
            if_ids.append(cid)
        elif cid.startswith("KPM-") and cid not in kpm_ids:
            kpm_ids.append(cid)
    fr_ids = sorted(set(fr_ids))
    nfr_ids = sorted(set(nfr_ids))
    if_ids = sorted(set(if_ids))
    kpm_ids = sorted(set(kpm_ids))

    all_ids = un_ids + fr_ids + nfr_ids + if_ids
    if offline:
        issue_bodies: dict[str, IssueInfo] = {i: IssueInfo() for i in all_ids}
    else:
        print(f"Fetching Issue bodies for {len(all_ids)} requirement(s)...", file=sys.stderr)
        issue_bodies = fetch_issue_bodies(all_ids)

    parts: list[str] = [render_header(project_name, REQ_MAP_PATH)]

    if un_ids:
        parts.append("\n    // ======= User Needs =======\n")
        for uid in un_ids:
            parts.append(render_user_need(uid, issue_bodies.get(uid, IssueInfo())))

    if fr_ids:
        parts.append("\n    // ======= Functional Requirements =======\n")
        for fid in fr_ids:
            parts.append(render_functional(fid, issue_bodies.get(fid, IssueInfo()),
                                           child_parents.get(fid, [])))

    if nfr_ids:
        parts.append("\n    // ======= Non-Functional Requirements =======\n")
        for nid in nfr_ids:
            parts.append(render_non_functional(nid, issue_bodies.get(nid, IssueInfo()),
                                               child_parents.get(nid, [])))

    if if_ids:
        parts.append("\n    // ======= Interface Requirements =======\n")
        for iid in if_ids:
            parts.append(render_interface(iid, issue_bodies.get(iid, IssueInfo()),
                                          child_parents.get(iid, [])))

    if kpm_ids:
        parts.append("\n    // ======= KPMs (constraint blocks) =======\n")
        kpms_dict = req_map.get("kpms") or {}
        for kid in kpm_ids:
            parts.append(render_kpm(kid, kpms_dict.get(kid, {})))

    stages = req_map.get("stages") or {}
    if stages:
        parts.append("\n    // ======= Verification Cases (Stages) =======\n")
        for stage_num in sorted(stages):
            parts.append(render_verification_case(stage_num, stages[stage_num] or {}))

    parts.append(render_footer())
    return "".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                    help=f"Output file path (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})")
    ap.add_argument("--stdout", action="store_true",
                    help="Print to stdout instead of writing to disk.")
    ap.add_argument("--offline", action="store_true",
                    help="Skip GitHub Issue body fetch; use YAML only.")
    args = ap.parse_args()

    if not REQ_MAP_PATH.exists():
        sys.exit(f"Missing {REQ_MAP_PATH}")
    req_map = yaml.safe_load(REQ_MAP_PATH.read_text(encoding="utf-8")) or {}

    text = export(req_map, offline=args.offline)

    if args.stdout:
        print(text)
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"Wrote {args.output.relative_to(REPO_ROOT)} "
          f"({len(text.splitlines())} lines, {len(text)} bytes)")


if __name__ == "__main__":
    main()
