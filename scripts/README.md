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
- `requirement_map.yml` — reads from `requirements/requirement-map.yml`
  (the canonical location; this is a legacy alias).

## Configuration-driven

All four scripts read `config/disciplines.yml`, `config/evidence-kinds.yml`,
`config/stages.yml`, and `config/budgets.yml`. Edit the config, not the
scripts, to adapt to your domain.

## Pass 1 status

The PHOTONForge versions of these scripts are the starting point. Pass 1
generalizes them to read `config/` instead of hardcoded constants. Pass 2+
adds discipline-specific evidence kinds and artifact references.
