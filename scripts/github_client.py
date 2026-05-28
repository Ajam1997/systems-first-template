"""GitHub REST + GraphQL client for systems-first-template scripts.

Repository identity is resolved at construction time in this order:

    1. Explicit `owner=` / `repo=` arguments
    2. REPO_OWNER and REPO_NAME env vars
    3. `git config --get remote.origin.url` parse

This keeps the template portable: clone-and-go projects don't have to
edit any script to point at their own repo. CI sets the env vars
explicitly; local runs auto-detect from the git remote.
"""
import os
import re
import subprocess
import requests
from typing import Any


def _detect_owner_repo() -> tuple[str | None, str | None]:
    """Parse `origin` remote URL for owner/repo. Returns (None, None) on failure."""
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
    if not m:
        return None, None
    return m.group(1), m.group(2)


class GitHubClient:
    REST_BASE = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self, token: str | None = None, owner: str | None = None, repo: str | None = None):
        self.token = token or os.environ["GITHUB_TOKEN"]
        if owner is None:
            owner = os.environ.get("REPO_OWNER")
        if repo is None:
            repo = os.environ.get("REPO_NAME")
        if owner is None or repo is None:
            det_owner, det_repo = _detect_owner_repo()
            owner = owner or det_owner
            repo = repo or det_repo
        if owner is None or repo is None:
            raise RuntimeError(
                "Could not resolve GitHub repo identity. Set REPO_OWNER + REPO_NAME "
                "env vars, pass owner=/repo= explicitly, or run from a git checkout "
                "with an `origin` remote pointed at github.com."
            )
        self.owner = owner
        self.repo = repo
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    # --- Labels ---

    def create_label(self, name: str, color: str, description: str) -> dict:
        """Create a label; return existing label if it already exists."""
        r = self._session.post(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/labels",
            json={"name": name, "color": color, "description": description},
        )
        if r.status_code == 422:
            # Already exists — fetch it
            r2 = self._session.get(
                f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/labels/{requests.utils.quote(name, safe='')}",
            )
            r2.raise_for_status()
            return r2.json()
        r.raise_for_status()
        return r.json()

    # --- Issues ---

    def find_issue_by_title(self, search_term: str) -> dict | None:
        """Return first open Issue whose title contains search_term, or None."""
        r = self._session.get(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues",
            params={"state": "open", "per_page": 100},
        )
        r.raise_for_status()
        for issue in r.json():
            if search_term in issue.get("title", ""):
                return issue
        return None

    def create_issue(self, title: str, body: str, labels: list[str]) -> dict:
        """Create an Issue and return the response dict (includes number and node_id)."""
        r = self._session.post(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues",
            json={"title": title, "body": body, "labels": labels},
        )
        r.raise_for_status()
        return r.json()

    def get_or_create_issue(self, search_term: str, title: str, body: str, labels: list[str]) -> dict:
        """Return existing Issue matching search_term, or create it."""
        existing = self.find_issue_by_title(search_term)
        if existing:
            return existing
        return self.create_issue(title, body, labels)

    def add_sub_issue(self, parent_number: int, child_issue_id: int) -> None:
        """Add child_issue_id as a sub-issue of parent_number.
        Skips gracefully if the sub-issues API is unavailable (404) — requires GitHub Team/Enterprise.
        """
        r = self._session.post(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues/{parent_number}/sub_issues",
            json={"sub_issue_id": child_issue_id},
        )
        if r.status_code == 404:
            return  # Sub-issues API not available on this plan — hierarchy captured via labels/body
        r.raise_for_status()

    def post_comment(self, issue_number: int, body: str) -> dict:
        r = self._session.post(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments",
            json={"body": body},
        )
        r.raise_for_status()
        return r.json()

    def get_issue(self, issue_number: int) -> dict:
        r = self._session.get(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues/{issue_number}",
        )
        r.raise_for_status()
        return r.json()

    def set_labels(self, issue_number: int, labels: list[str]) -> None:
        r = self._session.post(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues/{issue_number}/labels",
            json={"labels": labels},
        )
        r.raise_for_status()

    def replace_status_label(self, issue_number: int, new_status: str) -> None:
        """Replace any existing status:* label with new_status, preserving all other labels."""
        issue = self.get_issue(issue_number)
        current = [l["name"] for l in issue.get("labels", [])]
        updated = [l for l in current if not l.startswith("status:")] + [new_status]
        r = self._session.put(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues/{issue_number}/labels",
            json={"labels": updated},
        )
        r.raise_for_status()

    def close_issue(self, issue_number: int) -> None:
        r = self._session.patch(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues/{issue_number}",
            json={"state": "closed"},
        )
        r.raise_for_status()

    def list_milestones(self, state: str = "open") -> list[dict]:
        """Return all milestones for the repo. state: open | closed | all."""
        milestones: list[dict] = []
        page = 1
        while True:
            r = self._session.get(
                f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/milestones",
                params={"state": state, "per_page": 100, "page": page},
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            milestones.extend(batch)
            page += 1
        return milestones

    def close_milestone(self, milestone_number: int) -> None:
        r = self._session.patch(
            f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/milestones/{milestone_number}",
            json={"state": "closed"},
        )
        r.raise_for_status()

    def list_issues(self, labels: str | None = None, state: str = "open") -> list[dict]:
        params: dict[str, Any] = {"state": state, "per_page": 100}
        if labels:
            params["labels"] = labels
        issues = []
        page = 1
        while True:
            params["page"] = page
            r = self._session.get(
                f"{self.REST_BASE}/repos/{self.owner}/{self.repo}/issues",
                params=params,
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            issues.extend(batch)
            page += 1
        return issues

    # --- GraphQL (Projects v2) ---

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        r = self._session.post(
            self.GRAPHQL_URL,
            json={"query": query, "variables": variables or {}},
        )
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL error: {data['errors']}")
        return data["data"]

    def get_owner_node_id(self) -> str:
        data = self.graphql(
            "query($login: String!) { user(login: $login) { id } }",
            {"login": self.owner},
        )
        return data["user"]["id"]

    def find_project_by_title(self, title: str) -> dict | None:
        """Return existing Projects v2 board with matching title, or None."""
        data = self.graphql(
            "query($login: String!) { user(login: $login) { projectsV2(first: 20) { nodes { id number title } } } }",
            {"login": self.owner},
        )
        for node in data["user"]["projectsV2"]["nodes"]:
            if node["title"] == title:
                return {"id": node["id"], "number": node["number"]}
        return None

    def get_or_create_project(self, owner_id: str, title: str) -> dict:
        """Return existing project with title, or create it."""
        existing = self.find_project_by_title(title)
        if existing:
            print(f"    (found existing board: {title})")
            return existing
        return self.create_project(owner_id, title)

    def create_project(self, owner_id: str, title: str) -> dict:
        """Create a Projects v2 board. Returns {"id": ..., "number": ...}."""
        data = self.graphql(
            """
            mutation($ownerId: ID!, $title: String!) {
              createProjectV2(input: {ownerId: $ownerId, title: $title}) {
                projectV2 { id number }
              }
            }
            """,
            {"ownerId": owner_id, "title": title},
        )
        return data["createProjectV2"]["projectV2"]

    def add_project_item(self, project_id: str, issue_node_id: str) -> str:
        """Add an Issue to a Projects v2 board. Returns the item node ID."""
        data = self.graphql(
            """
            mutation($projectId: ID!, $contentId: ID!) {
              addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
                item { id }
              }
            }
            """,
            {"projectId": project_id, "contentId": issue_node_id},
        )
        return data["addProjectV2ItemById"]["item"]["id"]

    def _find_project_field_id(self, project_id: str, name: str) -> str | None:
        """Return the node ID of an existing field on a project, or None."""
        data = self.graphql(
            """
            query($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  fields(first: 30) {
                    nodes {
                      ... on ProjectV2Field { id name }
                      ... on ProjectV2SingleSelectField { id name }
                    }
                  }
                }
              }
            }
            """,
            {"projectId": project_id},
        )
        for node in data["node"]["fields"]["nodes"]:
            if node.get("name") == name:
                return node["id"]
        return None

    def create_project_field(self, project_id: str, name: str, data_type: str, options: list[str] | None = None) -> str:
        """Create a custom field on a Projects v2 board. Returns field node ID.
        Idempotent: returns existing field ID if a field with the same name exists.
        data_type: TEXT | SINGLE_SELECT | NUMBER | DATE
        options: required when data_type is SINGLE_SELECT
        """
        existing_id = self._find_project_field_id(project_id, name)
        if existing_id:
            return existing_id

        if data_type == "SINGLE_SELECT":
            opts = [{"name": o, "color": "GRAY", "description": ""} for o in (options or [])]
            data = self.graphql(
                """
                mutation($projectId: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
                  createProjectV2Field(input: {projectId: $projectId, name: $name, dataType: SINGLE_SELECT, singleSelectOptions: $options}) {
                    projectV2Field { ... on ProjectV2SingleSelectField { id } }
                  }
                }
                """,
                {"projectId": project_id, "name": name, "options": opts},
            )
            return data["createProjectV2Field"]["projectV2Field"]["id"]
        else:
            data = self.graphql(
                f"""
                mutation($projectId: ID!, $name: String!) {{
                  createProjectV2Field(input: {{projectId: $projectId, name: $name, dataType: {data_type}}}) {{
                    projectV2Field {{ ... on ProjectV2Field {{ id }} }}
                  }}
                }}
                """,
                {"projectId": project_id, "name": name},
            )
            return data["createProjectV2Field"]["projectV2Field"]["id"]

    def update_project_text_field(self, project_id: str, item_id: str, field_id: str, value: str) -> None:
        self.graphql(
            """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
              updateProjectV2ItemFieldValue(input: {
                projectId: $projectId, itemId: $itemId, fieldId: $fieldId,
                value: {text: $value}
              }) { projectV2Item { id } }
            }
            """,
            {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "value": value},
        )

    def update_project_select_field(self, project_id: str, item_id: str, field_id: str, option_id: str) -> None:
        self.graphql(
            """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
              updateProjectV2ItemFieldValue(input: {
                projectId: $projectId, itemId: $itemId, fieldId: $fieldId,
                value: {singleSelectOptionId: $optionId}
              }) { projectV2Item { id } }
            }
            """,
            {"projectId": project_id, "itemId": item_id, "fieldId": field_id, "optionId": option_id},
        )

    def find_project_item_by_issue_number(self, project_id: str, issue_number: int) -> str | None:
        """Return the Projects v2 item node ID for the given issue number, or None."""
        after = None
        while True:
            data = self.graphql(
                """
                query($projectId: ID!, $after: String) {
                  node(id: $projectId) {
                    ... on ProjectV2 {
                      items(first: 100, after: $after) {
                        nodes {
                          id
                          content { ... on Issue { number } }
                        }
                        pageInfo { hasNextPage endCursor }
                      }
                    }
                  }
                }
                """,
                {"projectId": project_id, "after": after},
            )
            items = data["node"]["items"]
            for node in items["nodes"]:
                content = node.get("content") or {}
                if content.get("number") == issue_number:
                    return node["id"]
            if not items["pageInfo"]["hasNextPage"]:
                return None
            after = items["pageInfo"]["endCursor"]

    def get_project_select_option_id(self, project_id: str, field_id: str, option_name: str) -> str | None:
        """Return the option node ID for a single-select field value by name."""
        data = self.graphql(
            """
            query($projectId: ID!) {
              node(id: $projectId) {
                ... on ProjectV2 {
                  fields(first: 30) {
                    nodes {
                      ... on ProjectV2SingleSelectField {
                        id
                        options { id name }
                      }
                    }
                  }
                }
              }
            }
            """,
            {"projectId": project_id},
        )
        for field in data["node"]["fields"]["nodes"]:
            if field.get("id") == field_id:
                for opt in field.get("options", []):
                    if opt["name"].lower() == option_name.lower():
                        return opt["id"]
        return None
