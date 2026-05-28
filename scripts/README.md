# `scripts/`

The four scripts that enforce the five rules from `METHODOLOGY.md`.

| Script | Role | When it runs |
|---|---|---|
| `generate_docs.py` | Re-renders AUTO sections of living docs from Issue state. Reads `config/*.yml` for the active vocabulary. | On every PR merge (`.github/workflows/regen-docs.yml`) and manually |
| `pr_rollup.py` | Sole writer of `status: verified` and `status: validated`. Closes Milestones when their UNs roll up. | On every PR merge (`.github/workflows/pr-close-issues.yml`) |
| `migrate_wiki.py` | One-way render of `dev-docs/` to the GitHub Wiki. Diff-mode preview, LOCAL-ONLY escape hatch. | On push to main (`.github/workflows/wiki-publish.yml`) and manually with `--diff` / `--push` |
| `github_comment.py` | Agent-safe CLI for posting Issue comments. Required `--next-action` flag enforces the breadcrumb rule. | Invoked by `verification` and `validation` agents |

Plus shared infrastructure:

- `github_client.py` — thin REST + GraphQL wrapper. The token-holder.
- `sync_labels.py` — pure-Python label syncer (uses `gh`); reconciles
  the repo's labels to `.github/labels.yml`.

## Configuration-driven

The scripts read `config/disciplines.yml`, `config/evidence-kinds.yml`,
`config/stages.yml`, and `config/budgets.yml`, plus the requirement tree
at `requirements/requirement-map.yml`. Edit the config, not the scripts,
to adapt to your domain.

## Repo identity

Every script resolves the GitHub owner/repo from:
1. Explicit `--owner` / `--repo` (or `owner=` / `repo=` kwargs)
2. `REPO_OWNER` and `REPO_NAME` env vars
3. `git config --get remote.origin.url`

CI workflows set the env vars explicitly; local runs auto-detect.
