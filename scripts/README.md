# `scripts/`

The four scripts that enforce the five rules from `METHODOLOGY.md`.

| Script | Role | When it runs |
|---|---|---|
| `generate_docs.py` | Re-renders AUTO sections of living docs from Issue state. Reads `config/*.yml` for the active vocabulary. | On every PR merge (`.github/workflows/regen-docs.yml`) and manually |
| `pr_rollup.py` | Sole writer of `status: verified` and `status: validated`. Closes Milestones when their UNs roll up. | On every PR merge (`.github/workflows/pr-close-issues.yml`) |
| `migrate_wiki.py` | One-way render of `dev-docs/` to the GitHub Wiki. Diff-mode preview, LOCAL-ONLY escape hatch. | On push to main (`.github/workflows/wiki-publish.yml`) and manually with `--diff` / `--push` |
| `github_comment.py` | Agent-safe CLI for posting Issue comments. Required `--next-action` flag enforces the breadcrumb rule. | Invoked by `verification` and `validation` agents |
| `kpm_rollup.py` | Aggregates child KPM measurements into parent KPMs (sum/max/min). The V-model rollup engine. | On every PR merge + manually (`.github/workflows/kpm-rollup.yml`) |
| `export_sysml.py` | Renders the requirement tree as SysMLv2 textual notation into `model/system.sysml`. | On `requirement-map.yml` change + manually (`.github/workflows/sysml-export.yml`) |
| `init_project.py` | One-command bootstrapper: validate config, sync labels, create milestones, activate agent packs, regen docs. | Manually after first clone |

Plus shared infrastructure:

- `github_client.py` — thin REST + GraphQL wrapper. The token-holder.
- `sync_labels.py` — pure-Python label syncer (uses `gh`); reconciles
  the repo's labels to `.github/labels.yml`.

## Configuration-driven

The scripts read `config/disciplines.yml`, `config/evidence-kinds.yml`,
`config/stages.yml`, plus the requirement + KPM tree at
`requirements/requirement-map.yml`. Edit the config, not the scripts,
to adapt to your domain.

## Repo identity

Every script resolves the GitHub owner/repo from:
1. Explicit `--owner` / `--repo` (or `owner=` / `repo=` kwargs)
2. `REPO_OWNER` and `REPO_NAME` env vars
3. `git config --get remote.origin.url`

CI workflows set the env vars explicitly; local runs auto-detect.
