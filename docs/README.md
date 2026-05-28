# `docs/` — Placeholder for end-user documentation

This folder is reserved for **customer-facing** or **end-user**
documentation — installation guides, how-tos, API reference, product
manuals. Whatever your downstream users need.

Developer documentation lives in `dev-docs/`. Don't mix the two.

When user-facing docs land, decide whether to:
- Serve them via GitHub Pages (`mkdocs.yml` + `gh-pages` workflow)
- Publish them outside the repo (Read the Docs, your own static host)
- Embed them in your product (Help → Documentation)

This template doesn't pre-pick that decision. Add the appropriate
config + workflow when you know.
