#!/usr/bin/env python3
"""Agent-safe CLI for writing GitHub Issue comments.

Agents (verification, validation, discipline leads) use this script
to post results. Never call the GitHub API directly — this script
holds the token.

This script posts **comments only**. It never moves status labels.
- `status: verified` on FR/NFR/UN/IF is owned by `scripts/pr_rollup.py` on PR merge.
- `status: validated` follows from the milestone rollup in `pr_rollup.py`.
- A regression posts an evidence comment; it does NOT downgrade the label.

Every ID-based command requires --next-action — the next reader uses that
line to resume work (the breadcrumb rule from METHODOLOGY.md §5). Every
comment carries a `via: @<agent>` footer so writer origin is legible.

Repo identity is auto-resolved (see scripts/github_client.py): explicit
flags → REPO_OWNER/REPO_NAME env vars → `git config remote.origin.url`.

ID-based commands:

  verify-fr <FR-ID> <summary> --next-action "<text>" [--via verification]
      Post a verification evidence comment on the FR Issue.

  regress-fr <FR-ID> <reason> --next-action "<text>" [--via verification]
      Post a regression evidence comment on the FR Issue. Does NOT move labels.

  update-kpm <KPM-ID> <last_measured> <passing|failing|untested>
             --next-action "<text>" [--via verification]
      Post measurement; update Last Measured + Status on the KPM Dashboard project board.

  validate-un <UN-ID> <summary> --next-action "<text>" [--via validation]
      Post an E2E evidence comment on the UN Issue.

  validation-failure <UN-ID> <reason> --next-action "<text>" [--via validation]
      Post comment on UN Issue and open a new type: validation-failure Issue
      assigned to @architect.

Low-level commands (Issue number directly; --next-action still required):

  comment <issue_number> <body> --next-action "<text>" [--via <name>]
  set-labels <issue_number> <label1> [<label2> ...]    (no footer / no next-action)
  close <issue_number>                                  (no footer / no next-action)

ID resolution: tries `dev-docs/github-issue-map.json` if present, then
falls back to `client.find_issue_by_title("[<ID>]")`, then to a live
`gh issue list --search`. A stale map never blocks a handoff.
The map is optional — projects that don't run `seed_github.py` work
fine without it.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.github_client import GitHubClient

MAP_PATH = Path(os.environ.get("ISSUE_MAP_PATH", "dev-docs/github-issue-map.json"))


def load_map() -> dict:
    if MAP_PATH.exists():
        return json.loads(MAP_PATH.read_text())
    return {}


def lookup_req(client: GitHubClient, issue_map: dict, req_id: str) -> int:
    """Return Issue number for a FR, NFR, IF, KPM, or UN ID.

    Tries the local map first; falls back to a live GitHub search so a stale
    map never blocks an agent.
    """
    prefix = req_id.split("-")[0].lower()
    section_map = {
        "fr": "functional_requirements",
        "nfr": "non_functional_requirements",
        "if": "interface_requirements",
        "kpm": "kpms",
        "un": "user_needs",
    }
    section = section_map.get(prefix)
    if section and req_id in issue_map.get(section, {}):
        return issue_map[section][req_id]["number"]

    # Fallback: live search by title prefix `[<REQ-ID>]`
    print(f"note: {req_id} not in local issue map — searching live", file=sys.stderr)
    found = client.find_issue_by_title(f"[{req_id}]")
    if found:
        return found["number"]

    # Final fallback: gh CLI search (works even if GitHubClient search misses)
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--search", f"{req_id} in:title",
             "--state", "all", "--json", "number,title", "--limit", "5"],
            capture_output=True, text=True, check=True,
        )
        issues = json.loads(result.stdout)
        for issue in issues:
            if f"[{req_id}]" in issue["title"]:
                return issue["number"]
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        pass

    raise KeyError(
        f"{req_id} not found in github-issue-map.json or via live search. "
        f"Re-run scripts/seed_github.py if this is a new requirement."
    )


def kpm_project_meta(issue_map: dict) -> tuple[str | None, str | None, str | None]:
    """Return (project_id, last_measured_field_id, status_field_id) or all None."""
    projects = issue_map.get("projects", {})
    kpm = projects.get("kpm_dashboard", {})
    return (
        kpm.get("id"),
        kpm.get("fields", {}).get("last_measured_id"),
        kpm.get("fields", {}).get("status_id"),
    )


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def render_footer(via: str, next_action: str) -> str:
    return f"\n\n---\n**Next action:** {next_action}\n\n*via: @{via}*"


# --- command implementations ---

def cmd_verify_fr(client: GitHubClient, issue_map: dict, args: argparse.Namespace) -> None:
    num = lookup_req(client, issue_map, args.id)
    body = (
        f"## Verification â€” {today_str()}\n\n"
        f"**{args.id}** Â· {args.summary}"
        f"{render_footer(args.via, args.next_action)}"
    )
    client.post_comment(num, body)
    print(f"posted verification comment on {args.id} (#{num})")
    print("note: status label NOT moved â€” pr_rollup.py owns that on PR merge.")


def cmd_regress_fr(client: GitHubClient, issue_map: dict, args: argparse.Namespace) -> None:
    num = lookup_req(client, issue_map, args.id)
    body = (
        f"## Regression â€” {today_str()}\n\n"
        f"**{args.id}** Â· {args.reason}"
        f"{render_footer(args.via, args.next_action)}"
    )
    client.post_comment(num, body)
    print(f"posted regression comment on {args.id} (#{num})")
    print("note: status label NOT downgraded â€” this is evidence only. "
          "Open an issue or revert the PR if the regression is real.")


def cmd_update_kpm(client: GitHubClient, issue_map: dict, args: argparse.Namespace) -> None:
    if args.kpm_status not in ("passing", "failing", "untested"):
        print(f"Error: status must be passing|failing|untested, got '{args.kpm_status}'")
        sys.exit(2)

    num = lookup_req(client, issue_map, args.id)
    body = (
        f"## KPM Update â€” {today_str()}\n\n"
        f"**{args.id}** Â· `{args.last_measured}` Â· **{args.kpm_status}**"
        f"{render_footer(args.via, args.next_action)}"
    )
    client.post_comment(num, body)
    print(f"posted KPM comment on {args.id} (#{num})")

    project_id, last_measured_field_id, status_field_id = kpm_project_meta(issue_map)
    if not project_id or not last_measured_field_id or not status_field_id:
        print("note: KPM Dashboard board fields not in issue map â€” skipping board update")
        return

    item_id = client.find_project_item_by_issue_number(project_id, num)
    if not item_id:
        print(f"note: {args.id} (#{num}) not found on KPM Dashboard board â€” skipping board update")
        return

    client.update_project_text_field(project_id, item_id, last_measured_field_id, args.last_measured)
    option_id = client.get_project_select_option_id(project_id, status_field_id, args.kpm_status)
    if option_id:
        client.update_project_select_field(project_id, item_id, status_field_id, option_id)
        print(f"updated KPM board: last_measured='{args.last_measured}', status='{args.kpm_status}'")
    else:
        print(f"note: could not find option '{args.kpm_status}' on KPM Status field â€” text field updated only")


def cmd_validate_un(client: GitHubClient, issue_map: dict, args: argparse.Namespace) -> None:
    num = lookup_req(client, issue_map, args.id)
    body = (
        f"## Validation â€” {today_str()}\n\n"
        f"**{args.id}** Â· {args.summary}"
        f"{render_footer(args.via, args.next_action)}"
    )
    client.post_comment(num, body)
    print(f"posted validation comment on {args.id} (#{num})")
    print("note: status label NOT moved â€” pr_rollup.py + Epic merge own that transition.")


def cmd_validation_failure(client: GitHubClient, issue_map: dict, args: argparse.Namespace) -> None:
    num = lookup_req(client, issue_map, args.id)
    body = (
        f"## Validation Failure â€” {today_str()}\n\n"
        f"**{args.id}** Â· {args.reason}\n\n"
        f"Escalating to @architect for requirement reassessment."
        f"{render_footer(args.via, args.next_action)}"
    )
    client.post_comment(num, body)

    failure_body = (
        f"## Validation Failure â€” {args.id}\n\n"
        f"**Date:** {today_str()}\n"
        f"**User Need:** {args.id}\n"
        f"**Reason:** {args.reason}\n\n"
        f"Opened automatically by @validation. Assigned to @architect for requirement reassessment.\n\n"
        f"**Next action:** {args.next_action}\n\n*via: @{args.via}*"
    )
    new_issue = client.create_issue(
        f"[validation-failure] {args.id} â€” {today_str()}",
        failure_body,
        ["type: validation-failure"],
    )
    print(f"posted failure comment on {args.id} (#{num})")
    print(f"opened validation-failure Issue #{new_issue['number']}")


def cmd_comment(client: GitHubClient, args: argparse.Namespace) -> None:
    body = args.body + render_footer(args.via, args.next_action)
    result = client.post_comment(args.issue_number, body)
    print(f"Posted comment {result['id']} on issue #{args.issue_number}")


def cmd_set_labels(client: GitHubClient, args: argparse.Namespace) -> None:
    client.set_labels(args.issue_number, args.labels)
    print(f"Set labels {args.labels} on issue #{args.issue_number}")


def cmd_close(client: GitHubClient, args: argparse.Namespace) -> None:
    client.close_issue(args.issue_number)
    print(f"Closed issue #{args.issue_number}")


# --- argparse wiring ---

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="github_comment",
        description="Agent-safe CLI for writing GitHub Issue comments. Comments only â€” never moves status labels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_next_action(sp: argparse.ArgumentParser, default_via: str) -> None:
        sp.add_argument("--next-action", required=True,
                        help="One-line next-step breadcrumb (HB-8 â€” required).")
        sp.add_argument("--via", default=default_via,
                        help=f"Agent footer name (default: {default_via}).")

    # verify-fr
    sp = sub.add_parser("verify-fr", help="Post FR verification evidence comment")
    sp.add_argument("id"); sp.add_argument("summary")
    add_next_action(sp, "verification")
    sp.set_defaults(func=cmd_verify_fr, needs_map=True)

    # regress-fr
    sp = sub.add_parser("regress-fr", help="Post FR regression evidence comment")
    sp.add_argument("id"); sp.add_argument("reason")
    add_next_action(sp, "verification")
    sp.set_defaults(func=cmd_regress_fr, needs_map=True)

    # update-kpm
    sp = sub.add_parser("update-kpm", help="Post KPM measurement + update Dashboard board")
    sp.add_argument("id"); sp.add_argument("last_measured")
    sp.add_argument("kpm_status", choices=["passing", "failing", "untested"])
    add_next_action(sp, "verification")
    sp.set_defaults(func=cmd_update_kpm, needs_map=True)

    # validate-un
    sp = sub.add_parser("validate-un", help="Post UN validation evidence comment")
    sp.add_argument("id"); sp.add_argument("summary")
    add_next_action(sp, "validation")
    sp.set_defaults(func=cmd_validate_un, needs_map=True)

    # validation-failure
    sp = sub.add_parser("validation-failure", help="Post UN failure comment + open escalation Issue")
    sp.add_argument("id"); sp.add_argument("reason")
    add_next_action(sp, "validation")
    sp.set_defaults(func=cmd_validation_failure, needs_map=True)

    # low-level: comment (still requires breadcrumb)
    sp = sub.add_parser("comment", help="Post raw comment on an Issue number")
    sp.add_argument("issue_number", type=int); sp.add_argument("body")
    add_next_action(sp, "operator")
    sp.set_defaults(func=cmd_comment, needs_map=False)

    # low-level: set-labels (no breadcrumb â€” operational maintenance, not handoff)
    sp = sub.add_parser("set-labels", help="Set labels on Issue (no breadcrumb required)")
    sp.add_argument("issue_number", type=int); sp.add_argument("labels", nargs="+")
    sp.set_defaults(func=cmd_set_labels, needs_map=False)

    # low-level: close (no breadcrumb)
    sp = sub.add_parser("close", help="Close an Issue (no breadcrumb required)")
    sp.add_argument("issue_number", type=int)
    sp.set_defaults(func=cmd_close, needs_map=False)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    client = GitHubClient()

    if getattr(args, "needs_map", False):
        issue_map = load_map()
        # ID-based commands take (client, issue_map, args)
        args.func(client, issue_map, args)
    else:
        # Low-level commands take (client, args)
        args.func(client, args)


if __name__ == "__main__":
    main()
