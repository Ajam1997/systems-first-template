# PHOTONFORGE / PHOTONFOUNDRY Plugin Marketplaces — Design Spec

**Date:** 2026-07-10
**Status:** Approved (brainstormed with Alex; this document records the validated design)
**Scope:** Phase 1 of 3 — plugin skeleton + migration path. Phases 2 (documentation
object hierarchy) and 3 (change-management agent) get their own specs later; this
spec only reserves their homes.

## 1. Problem

The systems-first-template ships its agent harness (agent `.md` files,
`scripts/*.py`, conventions) by **copying** into each instantiated project.
Copies drift — photo-workflow's roster migration already proved it. There is no
upgrade path: machinery improvements do not flow to existing projects.

Separately, the machinery's document formats are hardcoded in Python
(`generate_docs.py`), and the doc-system brain dump
(`Documentation system Brain Dump.md`, 2026-07-10) calls for templates,
conventions, and styles as first-class, agent-editable artifacts. That work
(phase 2) needs a versioned home before it can start.

## 2. Design principles (locked)

- **Plugin = engine, repo = policy.** Plugins ship machinery (agents, skills,
  scripts, seed templates). Each project owns its policy instances (its House
  Style, glossary, doc templates, requirement data) as repo files.
- **Two storefronts split by abstraction level, source lives where it
  belongs.** All repos live under the `Ajam1997` GitHub account (private
  until ready to share):
  - **`PHOTONFORGE`** — the process/systems marketplace: systems-first-core,
    the discipline packs, and the pip package live *in* this repo. The "how
    projects are run" layer, lockstep-versioned.
  - **`PHOTONFOUNDRY`** — the tool marketplace: a catalog-only repo that
    cross-lists granular design toolkits (kicad-pcba today; mechanical,
    firmware, enclosure tools later). Each tool plugin lives in **its own
    repo** (they are large and version independently); the foundry is the
    shared storefront. The "how things get built" layer.
  A full-stack project adds both marketplaces; discipline packs *recommend*
  foundry tools in their docs rather than auto-installing them.
- **Objective state over honor system** (adopted from kicad-pcba's `gates.py`):
  skills and agents derive next actions from machine-computed state, not from
  narrative claims. "The failing gates ARE the to-do list."
- **Packs are thin.** A discipline pack is process wiring (lead agent +
  pairings). Heavyweight domain tooling is a separate tool plugin the pack
  recommends — the electrical pack + kicad-pcba is the reference example.

## 3. Repo topology

New repo: **`Ajam1997/PHOTONFORGE`** — simultaneously the process
marketplace, the process-plugin monorepo, and home of the Python package.

```
.claude-plugin/marketplace.json      # catalog: the internal process plugins
plugins/
  core/                              # plugin: systems-first-core
    .claude-plugin/plugin.json
    agents/   systemmaster.md, verification.md, validation.md, systems_lead.md
    skills/   start-work/SKILL.md (+ references/)
              write-back/SKILL.md  (+ references/)
  software/                          # plugin: systems-first-software
    .claude-plugin/plugin.json
    agents/   software_lead.md
  electrical/  mechanical/  firmware/  manufacturing/  regulatory/
                                     # same thin-pack shape as software/
packages/
  systems-first/                     # pip package: systems-first
    pyproject.toml
    src/systems_first/
      generate_docs.py  github_comment.py  github_client.py
      kpm_rollup.py     pr_rollup.py       migrate_wiki.py
      sync_labels.py    validate_artifacts.py
      export_sysml.py   init_project.py
    tests/                           # migrated with the scripts
README.md                            # catalog docs + install instructions
.github/workflows/ci.yml             # package tests + plugin manifest validation
```

Deliberate changes from the template's current layout:

- **`systems_lead` moves to core.** It is discipline-agnostic; today it is
  duplicated into every agent-pack, which is the drift bug in miniature.
- **`nightly-drift` does not migrate.** It never worked and is abandoned;
  the photo-workflow migration deletes it.

## 4. Marketplace catalogs

**PHOTONFORGE** `marketplace.json` (process plugins, all internal):

| Entry | Source | Contents |
|---|---|---|
| `systems-first-core` | internal (`plugins/core`) | systemmaster, verification, validation, systems_lead + shared skills |
| `systems-first-software` | internal | software_lead |
| `systems-first-electrical` | internal | electrical_lead (wired to kicad-pcba, §6) |
| `systems-first-mechanical` … `-regulatory` | internal | one lead each |

**PHOTONFOUNDRY** (`Ajam1997/PHOTONFOUNDRY`) is catalog-only — a
`marketplace.json` + README, no plugin source. Every entry is external:

| Entry | Source | Contents |
|---|---|---|
| `kicad-pcba` | external: `Ajam1997/kicad-pcba` (see §9.3) | EE tool plugin (skills + scripts + MCP), versioned independently (currently 0.10.0) |
| *(future)* mechanical / firmware / enclosure toolkits | external, one repo each | added as they exist |

A project installs core + the packs matching its profile from PHOTONFORGE.
Profile A (photo-workflow) = core + software. A mechatronics project = core +
software + electrical + mechanical, plus the PHOTONFOUNDRY marketplace for
kicad-pcba as tooling. Nobody's roster carries disciplines they don't have.

Future tool plugins cost one PHOTONFOUNDRY catalog entry each — no changes to
PHOTONFORGE.

## 5. The Python package

The `scripts/` machinery becomes pip package **`systems-first`**, and only the
package — plugins do not vendor script copies. Console entry points replace
`scripts/*.py` invocations:

| Command | Replaces |
|---|---|
| `sf-docs` | `generate_docs.py` |
| `sf-comment` | `github_comment.py` |
| `sf-kpm-rollup` | `kpm_rollup.py` |
| `sf-pr-rollup` | `pr_rollup.py` |
| `sf-wiki` | `migrate_wiki.py` |
| `sf-labels` | `sync_labels.py` |
| `sf-artifacts` | `validate_artifacts.py` |
| `sf-sysml` | `export_sysml.py` |
| `sf-init` | `init_project.py` |

Both consumers install the same versioned artifact, no PyPI required:

```
pip install "systems-first @ git+https://github.com/Ajam1997/PHOTONFORGE@v0.1.0#subdirectory=packages/systems-first"
```

- **Agents** (via plugin instructions) call the `sf-*` commands from the
  project venv.
- **CI workflows** pin the same tag in their install step.

Known work item, not scope creep: the scripts likely contain
photo-workflow-isms (hardcoded repo names, label assumptions). Packaging is
where these get flushed into configuration (env vars / a `systems-first.toml`
the package reads per-project).

## 6. kicad-pcba integration (electrical reference pattern)

kicad-pcba stays in its own repo with its own version stream (currently
0.10.0). The systems-first side:

- PHOTONFOUNDRY cross-lists it as an external entry (requires §9.3).
- `plugins/electrical/agents/electrical_lead.md` pairs the lead with
  kicad-pcba's skills: the plugin's spec→schematic→library→layout→sourcing→
  production sequence maps onto systems-first stage gates, and its
  `docs/gates.json` output is the lead's verification-evidence source.

This is the template for every future discipline: thin pack = process,
tool plugin = implementation capability.

## 7. Versioning & releases

- PHOTONFORGE repo tags `vX.Y.Z` version **core + all internal packs + the
  pip package in lockstep**. Every plugin.json version and the pyproject
  version bump together; one tag = one coherent release.
- Tool plugins version independently in their own repos; PHOTONFOUNDRY is
  catalog-only and needs no version stream of its own — its entries just
  point at tool repos.
- Projects pin: CI pins the package tag; plugin installs track the
  marketplace. An explicit project-upgrade note ships in the README (the
  kicad-pcba pilot already needed a cross-version project migration once —
  this is a real requirement, not speculation).

## 8. Skills in v0.1 (minimal, with adopted patterns)

Two skills, both conversions of prose that already exists, both using the
`references/` progressive-disclosure layout from kicad-pcba:

1. **`start-work`** — the 60-second session-start checklist as an invocable
   skill, restructured on the orchestrator pattern: run objective state
   commands (`git status`, `gh issue list`, `sf-kpm-rollup --check`, CI
   status), derive the to-do list from computed state, dispatch. Trust
   computed state over narrative logs.
2. **`write-back`** — the agent write-back protocol: `sf-comment` usage,
   requirement-ID resolution, the `**Next action:**` (HB-8) and `via:` (HB-7)
   footer rules.

House Style, template-writer, and doc-object skills are **phase 2** and land
in core later; the skeleton just gives them a home.

## 9. Migration plan

### 9.1 Template repo (`systems-first-template`)

- Delete `.claude/agents/`, `.claude/agent-packs/`, and the migrated scripts
  (the nine CLIs plus `github_client.py`; project-agnostic machinery only —
  anything template-specific stays).
- Workflows call `sf-*` commands at a pinned tag instead of `scripts/*.py`.
- README/setup becomes: use the GitHub template → add the PHOTONFORGE
  marketplace (plus PHOTONFOUNDRY if the project needs tool plugins) →
  install core + your packs → `pip install` the package → `sf-init`.
- The template keeps what is genuinely per-project scaffolding:
  `requirements/`, `dev-docs/` seeds, `config/`, CI workflow files,
  METHODOLOGY.md.

### 9.2 photo-workflow (pilot + acceptance test)

- Install core + software from the marketplace; delete local agent files and
  migrated doc-automation scripts.
- Repoint live workflows (tests, docs-integrity, regen-docs, wiki-publish) at
  the pinned package. **Delete nightly-drift outright.**
- Project-specific scripts stay (`safe_eject.sh`, `manage_ssd.sh`,
  `remote_test.sh`, polkit install) — they are policy, not engine.
- Update CLAUDE.md roster/protocol sections to reference plugin agents and
  `sf-*` commands.

### 9.3 kicad-pcba + PHOTONFOUNDRY

- Push the plugin to `Ajam1997/kicad-pcba` (repo root = the current
  `kicad-pcba-plugin/` folder contents; fresh git init — the local ClaudePCBA
  folder has no history). The kicad-mcp clone and the rack-pdu-12v pilot
  project stay local.
- Create `Ajam1997/PHOTONFOUNDRY` (catalog-only) with the kicad-pcba entry.
- The local ClaudePCBA marketplace flow remains the dev-time install path.

## 10. Acceptance criteria

1. **Package:** migrated script tests pass in marketplace-repo CI.
2. **Plugins:** installing core + software from the marketplace resolves every
   agent and both skills invoke.
3. **End-to-end (the strong signal):** photo-workflow's regen-docs workflow
   produces **byte-identical `dev-docs/` output** pre- and post-migration.
   The engine transplant must change nothing.
4. photo-workflow CI is green with zero references to deleted local scripts.

## 11. Roadmap (recorded, out of scope here)

- **v0.2 — `sf-gates`:** objective stage-gate checker for systems-first
  (milestone gates computed from Issue labels, V&V coverage, KPM rollup,
  docs-integrity), with recorded sign-offs; release/merge producers refuse
  while gates fail. Direct port of the `gates.py` pattern.
- **Phase 2 — documentation objects:** House Style router skill,
  template-writer meta-skill, conventions-as-data (generalizing kicad-pcba's
  `templates/production/*/profile.json` precedent), glossary/system-bible as
  queryable data, CI enforcement of conventions. Styles (fonts/colors) stays
  YAGNI while render targets are GitHub markdown/wiki.
- **Phase 2+ — live dashboard:** a systems-first "viewport" (requirements
  status, KPM margins, V&V matrix) on the kicad-pcba `dashboard.py` model:
  live server + durable `build` snapshots.
- **Phase 3 — change-management agent:** impact analysis on requirement
  change (stale V&V evidence, child requirements via `requirement-map.yml`,
  affected leads). Lands in core.
- **Nice-to-have:** `sf-doctor` environment checker (gh auth, token, python,
  repo layout), on the `kicad_env.py` model.

## 12. Risks

| Risk | Mitigation |
|---|---|
| Scripts have photo-workflow-isms baked in | Flushed into per-project config during packaging (§5); acceptance test 3 catches behavior changes |
| All repos start private: plugin installs and pip installs need GitHub auth | Sole author with `gh` auth — acceptable; flip repos public when ready to share |
| Plugin agent names must match existing CLAUDE.md rosters | Keep agent names identical (`software_lead`, etc.); photo-workflow CLAUDE.md updated in the same migration PR |
| Lockstep versioning breaks if a tool plugin moved in-repo | Standing rule: tool plugins never live in PHOTONFORGE; they live in their own repos, cross-listed in PHOTONFOUNDRY (§2) |
