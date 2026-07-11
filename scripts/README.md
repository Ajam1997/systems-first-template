# `scripts/`

The process machinery that used to live here (`generate_docs.py`,
`pr_rollup.py`, `migrate_wiki.py`, `github_comment.py`, `kpm_rollup.py`,
`export_sysml.py`, `init_project.py`, `validate_artifacts.py`,
`github_client.py`, `sync_labels.py`) now ships as the `systems-first`
pip package, installed from the
[PHOTONFORGE](https://github.com/Ajam1997/PHOTONFORGE) marketplace repo —
see the root [`README.md`](../README.md#install-per-project) for the
install command.

| Old script | Now |
|---|---|
| `generate_docs.py` | `sf-docs` |
| `pr_rollup.py` | `sf-pr-rollup` |
| `migrate_wiki.py` | `sf-wiki` |
| `github_comment.py` | `sf-comment` |
| `kpm_rollup.py` | `sf-kpm-rollup` |
| `export_sysml.py` | `sf-sysml` |
| `init_project.py` | `sf-init` |
| `validate_artifacts.py` | `sf-artifacts` |
| `sync_labels.py` | `sf-labels` |
| `github_client.py` | internal to the `systems-first` package (no CLI) |

The `sf-*` CLIs still read `config/disciplines.yml`,
`config/evidence-kinds.yml`, `config/stages.yml`, and
`requirements/requirement-map.yml` from your project — edit the config,
not the package, to adapt to your domain. Repo identity resolution
(`--owner`/`--repo`, `REPO_OWNER`/`REPO_NAME` env vars, or
`git config --get remote.origin.url`) is unchanged.

This directory is now reserved for **project-specific scripts** — the
kind of thing `photo-workflow` keeps here (`safe_eject.sh`,
`manage_ssd.sh`, etc.). It ships empty in the template.
