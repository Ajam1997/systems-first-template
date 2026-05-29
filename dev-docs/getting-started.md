# Getting Started — From Zero to First Bootstrap

This walks you from a machine with **nothing installed** to a running
project bootstrap. Allow ~30–45 minutes the first time. Subsequent
projects skip everything in Part 1.

If you already have VS Code + Claude Code + Git + Python + gh CLI
installed and authenticated, skip to [Part 2](#part-2--use-the-template).

---

## What you'll have at the end

- A new private GitHub repo, created from the template
- The repo open in VS Code with the Claude Code extension running
- A classic Personal Access Token wired up so the wiki auto-publishes
- A filled `prompts/bootstrap_<your-name>.md` worksheet, committed as
  the project's inception record
- Claude having executed the bootstrap: profile activated, agents
  installed, first 6–12 user-need Issues filed, requirement map drafted,
  documentation and SysML model regenerated
- A clear next action: hand the first FR to a discipline lead

---

## Part 1 — Install the tools

### 1.1 — Visual Studio Code

Download from <https://code.visualstudio.com/> and run the installer.

**Windows:** during install, check the boxes for:
- "Add 'Open with Code' action to Windows Explorer file context menu"
- "Add 'Open with Code' action to Windows Explorer directory context menu"
- "Add to PATH"

**Mac:** after install, open VS Code, press `Cmd+Shift+P`, type
`Shell Command: Install 'code' command in PATH`, and run it.

Verify in a terminal:

```bash
code --version
```

### 1.2 — Claude Code (CLI + VS Code extension)

Claude Code is two things working together:

1. The **Claude Code CLI** — the actual agent runtime.
2. The **VS Code extension** — a thin UI on top of the CLI. The
   extension is useless without the CLI.

Install in that order.

#### 1.2a — Install the Claude Code CLI

Anthropic distributes Claude Code via a **native installer** on each
OS (no Node.js required) and via npm as a cross-platform fallback.
The native path is simpler.

**Canonical install instructions:** <https://claude.ai/code>
(or <https://docs.claude.com/en/docs/claude-code/setup>).

Follow whatever the page recommends for your OS — Anthropic updates
that page as the install paths evolve. As of writing, the typical
flows are:

- **Mac:** Homebrew or a one-line `curl ... | sh` installer.
- **Linux:** the one-line `curl ... | sh` installer.
- **Windows:** native installer or `winget`; npm is still the most
  reliable Windows path at the moment.

**npm fallback (any OS):** if the native installer isn't available
for your platform yet, install Node.js 18+ first
(<https://nodejs.org/>) and then:

```bash
npm install -g @anthropic-ai/claude-code
```

Mac/Linux may need `sudo` for the global install or a user-local npm
prefix.

Verify the install regardless of path:

```bash
claude --version
```

Run `claude` from any project directory to start a session. Sign in
when prompted (browser opens; uses your Anthropic account).

#### 1.2b — Install the VS Code extension

1. Open VS Code.
2. Click the Extensions icon in the left sidebar (or `Ctrl+Shift+X`).
3. Search for **"Claude Code"** (publisher: Anthropic).
4. Click Install.
5. After install, click the Claude icon in the left sidebar. The
   extension auto-detects the CLI you installed in 1.2a and inherits
   its sign-in. If it prompts for sign-in again, that's normal on
   first launch.

Verify: a chat panel opens in VS Code with a working input. If you
see "Claude Code CLI not found," the extension didn't find `claude`
on your PATH — restart VS Code, or re-check that
`claude --version` works in a fresh terminal.

### 1.3 — Git

**Windows:** Install from <https://git-scm.com/download/win>. Accept
all defaults except the line-ending setting — choose
**"Checkout as-is, commit as-is"** to avoid CRLF surprises on shared
shell scripts.

**Mac:** Git ships with Xcode Command Line Tools:

```bash
xcode-select --install
```

**Linux:** `sudo apt install git` (Debian/Ubuntu) or equivalent.

Verify:

```bash
git --version       # >= 2.30
```

Configure your identity once:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Use the email tied to your GitHub account so commits attribute
correctly.

### 1.4 — Python (version depends on your project)

The template's own scripts run on **Python 3.11+** (any modern Python
works). But if your project will use the recommended EE/ME tool stack
(Build123d, CadQuery, Atopile), you need **Python 3.13 specifically** —
those libraries don't yet support 3.14, and Atopile 0.3+ requires
3.13. See `dev-docs/architecture/external-tools.md`.

**Recommended:** install Python 3.13 even if you're not sure you'll
need the EE/ME stack. It works for everything in the template.

**Windows (PowerShell, user scope, no admin):**

```powershell
winget install Python.Python.3.13 --scope user
```

**Mac:** `brew install python@3.13` (install Homebrew from
<https://brew.sh/> first if needed).

**Linux:** `sudo apt install python3.13 python3.13-venv python3-pip`
(or deadsnakes PPA on older Ubuntu).

Verify:

```bash
python --version    # >= 3.11
pip --version
```

(On Mac/Linux you may need `python3` and `pip3` instead of `python`
and `pip` — both work.)

### 1.5 — GitHub CLI (`gh`)

Required: every script in `scripts/` shells out to `gh` for GitHub
operations.

**Windows (PowerShell admin):**

```powershell
winget install --id GitHub.cli
```

**Mac:** `brew install gh`

**Linux:** see <https://github.com/cli/cli#installation>.

Verify:

```bash
gh --version
```

### 1.6 — Authenticate `gh`

```bash
gh auth login
```

Answer the prompts:

| Prompt | Answer |
|---|---|
| Where do you use GitHub? | **GitHub.com** |
| Protocol for Git operations? | **HTTPS** |
| Authenticate Git with your GitHub credentials? | **Yes** |
| How would you like to authenticate? | **Login with a web browser** |

The CLI opens your browser, you paste a one-time code, and approve.
This handles 95% of GitHub operations. You'll add a separate classic
PAT in Part 3 for the wiki.

Verify:

```bash
gh auth status
```

Should show "Logged in to github.com as <your-handle>".

### 1.7 — Superpowers plugin (recommended)

**Superpowers** is a Claude Code plugin that ships a curated bundle
of skills (`brainstorming`, `writing-plans`,
`subagent-driven-development`, `test-driven-development`,
`systematic-debugging`, `verification-before-completion`,
`using-git-worktrees`, `dispatching-parallel-agents`, and more).

The template's discipline-lead agents reference these skills
extensively — every agent pack has a "Paired Superpowers Skills"
section that recommends or mandates specific skills for that lead's
work. Without Superpowers installed:

- `@verification` and `@validation` mandate
  `verification-before-completion`. Without it, the mandate becomes a
  docstring with no enforcement — agents may claim completion before
  evidence is in.
- Discipline lead recommendations (e.g. "use `systematic-debugging`
  when a yield drop appears") still apply as guidance but you lose
  the structured skill flow.
- The `start-work-checklist.md` SOPs cite skill invocations directly;
  those references become dead links in the agent's context.

You can run the template without it, but the agent harness is
designed around it. Install it before your first bootstrap if you
can.

**Install** (from any Claude Code session — works in the CLI or
inside VS Code's Claude Code panel):

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

The exact slash-command syntax can drift between Claude Code
versions. If the above fails, check the canonical install instructions
at <https://github.com/obra/superpowers>.

Verify (in a Claude Code session):

```
/plugin list
```

Should show `superpowers` in the list, status `enabled`.

After install, the skills are available globally — every project's
Claude Code session sees them, regardless of which repo you're in.
You don't reinstall per-project.

### 1.8 — Discipline-specific tools (when your project needs them)

Skip this if you're on Profile A (software-only). For Profiles B/C
or any project that activates `electrical_lead` or `mechanical_lead`,
you need the tool stack documented in
[`dev-docs/architecture/external-tools.md`](architecture/external-tools.md).
TL;DR install:

| Tool | Why | Install |
|---|---|---|
| **KiCad 9.x** | PCB layout + `kicad-cli` for CI verification | <https://www.kicad.org/download/> — native installer per OS |
| **FreeCAD 1.0+** | FEA via FreeCAD FEM workbench; TechDraw drawings fallback | <https://www.freecad.org/downloads.php> — native installer per OS |
| **build123d, ezdxf, cadquery, atopile** | Code-CAD + code-PCB Python libraries | In your project's venv: `pip install -r requirements.txt` (after the project's bootstrap adds them) |

Verify after install:

```bash
kicad-cli --version       # >= 9.x
FreeCADCmd --version      # >= 1.0  (on macOS/Linux: freecadcmd)
python -c "import build123d, ezdxf, cadquery, atopile; print('ok')"
```

**Windows PATH gotcha:** the KiCad and FreeCAD installers on Windows
**don't add their `bin/` directories to PATH automatically.** After
install, manually add:

- `<KiCad install root>\bin` (typical: `C:\Program Files\KiCad\<version>\bin`)
- `<FreeCAD install root>\bin` (typical: `C:\Program Files\FreeCAD\bin`)

…to your **user** PATH. Then restart your shell / VS Code so the new
PATH is picked up. PowerShell one-liner (adjust paths):

```powershell
$kicad = "C:\Program Files\KiCad\9.0\bin"
$freecad = "C:\Program Files\FreeCAD\bin"
$cur = [Environment]::GetEnvironmentVariable("PATH", "User")
$parts = $cur -split ';' | Where-Object { $_ }
foreach ($p in @($kicad, $freecad)) { if ($parts -notcontains $p) { $parts += $p } }
[Environment]::SetEnvironmentVariable("PATH", ($parts -join ';'), "User")
```

If you installed to a non-default location (e.g. `E:\PHOTONForge\KiCAD`),
substitute that as the install root.

On Mac and Linux the binaries usually land on PATH automatically via
Homebrew or the package manager; if not, symlink them into
`/usr/local/bin` or `~/.local/bin`.

**Python version pinning for the EE/ME stack.** As of writing:
- `build123d` requires Python **<3.14** (OCCT bindings)
- `atopile` requires Python **>=3.13**
- Sweet spot: **Python 3.13**

If your system Python is 3.14 (bleeding edge) or 3.12 (lagging),
create a project venv with 3.13:

```powershell
# Windows: install Python 3.13 user-scope
winget install Python.Python.3.13 --scope user
# In your project root:
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Add `.venv/` to `.gitignore` if it isn't already.

---

## Part 2 — Use the template

### 2.1 — Create your project repo from the template

1. Browse to <https://github.com/Ajam1997/systems-first-template>.
2. Click **"Use this template"** → **"Create a new repository"**.
3. Fill in:
   - **Owner:** your account (or org).
   - **Repository name:** something short and slug-friendly
     (e.g. `feline-enrichment-device`, `solar-charge-controller`).
   - **Description:** one sentence — this becomes the GitHub repo
     description, not Field A1.
   - **Private** (recommended for early-stage work).
   - **Include all branches:** unchecked (only `main` is needed).
4. Click **"Create repository"**.

### 2.2 — Clone the repo to your machine

In a terminal:

```bash
cd ~/projects                   # or wherever you keep code
gh repo clone <your-handle>/<your-repo-name>
cd <your-repo-name>
```

### 2.3 — Install Python dependencies (in a venv)

Use a project-local virtual environment so deps don't fight with other
projects on your machine. Especially important if the project uses
the EE/ME stack (Build123d, Atopile) — those pin to specific Python
versions and pull heavy OCCT binaries.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If your system Python is too new (3.14+), point the venv at 3.13
explicitly:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
```

**Mac/Linux:**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Heads-up on install size: a project with the full EE/ME stack pulls
~800 MB on first install (OCCT binaries via `cadquery-ocp`). Cached
after that. The template's bare minimum (PyYAML + requests) is ~5 MB.

The `.venv/` directory is already gitignored.

### 2.4 — Open in VS Code

```bash
code .
```

The Claude Code panel opens automatically. You'll come back to it in
Part 4.

---

## Part 3 — Tokens & wiki setup

The template has a workflow (`.github/workflows/wiki-publish.yml`)
that auto-publishes `dev-docs/` to the repo's GitHub Wiki on every
push to `main`. It needs a Personal Access Token because GitHub's
default `GITHUB_TOKEN` cannot push to wiki repos — this is a GitHub
platform limitation (no permission scope grants wiki write to the
auto-issued token), not a template choice.

If you'd rather skip the PAT, you can publish the wiki manually from
your machine instead: `python scripts/migrate_wiki.py --push` uses
your local git credentials, which already have wiki write access on
repos you own. The trade-off is that the wiki stays stale until you
remember to run it.

### 3.1 — Why a *classic* PAT (not fine-grained)

GitHub has two PAT formats:

| Type | Wiki write? |
|---|---|
| **Classic PAT** | Yes (with `repo` scope) |
| **Fine-grained PAT** | No — fails with HTTP 403 even on repos you own |

You must use a classic PAT. The fine-grained type has no wiki
permission to grant.

### 3.2 — Generate the token

1. Browse to <https://github.com/settings/tokens?type=beta> — *do
   NOT* click "Generate new token" on this page; that's the
   fine-grained one. Instead, click **"Tokens (classic)"** in the
   left sidebar, then **"Generate new token (classic)"**.
2. Fill in:
   - **Note:** `<your-repo-name> wiki push` (so future-you knows
     what it's for).
   - **Expiration:** 1 year is reasonable. Calendar-flag yourself
     for renewal.
   - **Scopes:** check **`repo`** (Full control of private
     repositories). This is the narrowest scope that includes wiki
     write on a private repo. Don't tick anything else.
3. Click **"Generate token"** at the bottom.
4. **Copy the token immediately** — GitHub only shows it once. If
   you close the page without copying, you'll have to regenerate.

### 3.3 — Store the token as a repo secret

The token grants write access to your repos, so it never goes in
the repo itself. It lives as a GitHub Actions secret.

1. Browse to your repo on GitHub.
2. **Settings** → **Secrets and variables** → **Actions**.
3. Click **"New repository secret"**.
4. Fill in:
   - **Name:** `WIKI_PUSH_TOKEN` (exact spelling, case matters).
   - **Secret:** paste the token from step 3.2.
5. Click **"Add secret"**.

The secret is now write-only — you can never read it back, only
overwrite or delete it. That's correct behavior.

### 3.4 — Seed the wiki's first page

GitHub doesn't create the wiki Git repo (`<repo>.wiki.git`) until
the wiki has at least one page. The auto-publish workflow can't
push to a repo that doesn't exist yet.

1. Browse to your repo on GitHub.
2. Click the **Wiki** tab.
3. Click **"Create the first page"**.
4. Title it `Home`. Body can be one line — the workflow will
   overwrite it on its first run.
5. Click **"Save Page"**.

Now the wiki repo exists. The next push to `main` will trigger
`Publish Dev Docs to Wiki` and replace the page with the full
auto-generated content from `dev-docs/`.

### 3.5 — Verify the auth chain

In your repo on GitHub:

1. **Actions** tab → **Publish Dev Docs to Wiki**.
2. Click **"Run workflow"** → **"Run workflow"** (use main branch).
3. Watch it run. Success = ~30 seconds with all green checks.

Failure modes:

| Symptom | Cause | Fix |
|---|---|---|
| `403 Forbidden` | Fine-grained PAT used | Regenerate as classic PAT (3.2) |
| `repository not found` | Wiki page not seeded | Do step 3.4 |
| `bad credentials` | Token typo in secret | Re-paste in 3.3 |
| `secret WIKI_PUSH_TOKEN not set` | Missed step 3.3 entirely | Do step 3.3 |

---

## Part 4 — Run the bootstrap

### 4.1 — Copy and fill the worksheet

Pick a name for your filled copy. Use your GitHub handle so it
identifies the operator:

```bash
cp prompts/bootstrap.md prompts/bootstrap_<your-handle>.md
```

Open `prompts/bootstrap_<your-handle>.md` in VS Code's editor (not
the preview). Fill **Section A** by replacing each
`<<fill in: ...>>` sentinel with a real answer. See
[`prompts/bootstrap-faq.md`](../prompts/bootstrap-faq.md) for help
on each field.

> **VS Code tip:** if the file opens in preview mode (italic tab
> name, can't type), close it and re-open with **right-click →
> Open With → Text Editor**. Or hit `Ctrl+Shift+P` →
> "Preferences: Open User Settings (JSON)" and add
> `"workbench.editor.enablePreview": false`.

### 4.2 — Commit the inception record

```bash
git add prompts/bootstrap_<your-handle>.md
git commit -m "chore(inception): scoping worksheet by <your-handle>"
git push
```

This is the project's permanent "this is how it started" record.
It does not get deleted.

### 4.3 — Paste into Claude Code

In VS Code, open the Claude Code panel. Start a new session. Paste
**the entire filled file**.

Claude will:

1. Validate Section A (refuse if any `<<fill in: ...>>` remains)
2. Read the methodology files
3. Run `init_project.py --activate-profile <X>` (with `--dry-run`
   first; you confirm, then it runs for real)
4. Walk you through 6–12 user needs, filing each as a GitHub Issue
5. Decompose each UN into FR / NFR / IF / KPM Issues
6. Write `requirements/requirement-map.yml`
7. Run the render chain (`generate_docs`, `kpm_rollup`,
   `export_sysml`, `validate_artifacts`)
8. Commit and report

Expect the conversation to take ~30–60 min depending on how clean
your UNs are.

---

## Part 5 — After the bootstrap

### 5.1 — Watch the wiki populate

After the bootstrap's final push, the **Publish Dev Docs to Wiki**
workflow fires. Browse to the **Wiki** tab on your repo a minute
later — `dev-docs/` content should be there, navigable via the
sidebar.

### 5.2 — Find your first FR

The bootstrap's final message names a next action — usually:

> *Open `dev-docs/architecture/<feature>-engineer-brief.md` for the
> first FR and hand it to @<discipline>_lead.*

Open Claude Code, paste:

> *"Author the engineer brief for FR-1.1. Use the systems_lead
> agent."*

The lead agent reads the requirement map, drafts the brief, and
hands off to the discipline lead named in its `Owner:` line.

### 5.3 — Daily-driver workflow

From now on, every session starts by reading
[`dev-docs/start-work-checklist.md`](start-work-checklist.md) (~60 s).
That picks the right agent for the work in front of you.

---

## Troubleshooting cheat-sheet

| Symptom | Probably | Fix |
|---|---|---|
| `gh: command not found` | Step 1.5 missing | Install `gh`, restart shell |
| `ModuleNotFoundError: yaml` | Skipped 2.3 | `pip install -r requirements.txt` |
| Claude Code panel empty | Not signed in | Click Claude icon, sign in |
| Bootstrap refuses with "field still has `<<fill in>>`" | Missed a worksheet field | Open `bootstrap_<handle>.md`, find the sentinel, replace it |
| `init_project.py` complains "No active disciplines" | Profile not activated | Re-run with `--activate-profile A|B|C` |
| Milestones created but Issues have no milestone | Stale issue filed before milestone existed | Edit the Issue, set the milestone manually |
| Wiki tab shows 404 / "Pages" empty | Step 3.4 not done | Seed the first page via the GitHub UI |
| Wiki workflow runs but content is stale | `generate_docs.py` ran before Issues existed | Trigger **Regenerate Docs from Issues** manually from the Actions tab |
| Wiki workflow fails: `Missing nav config at dev-docs/_wiki-nav.yml` | Custom dev-docs/ doesn't have a nav config | Copy the template's `dev-docs/_wiki-nav.yml` into your repo and edit to match your docs layout |
| Agent recommends `superpowers:<skill>` but nothing happens | Superpowers plugin not installed | Step 1.7 — install the plugin globally; works in any project after |
| `kicad-cli: command not found` (Windows) | KiCad installer didn't add `bin\` to PATH | Step 1.8 — manually add `<KiCad>\bin` to user PATH, restart shell |
| `FreeCADCmd: command not found` (Windows) | Same as KiCad | Step 1.8 — manually add `<FreeCAD>\bin` to user PATH, restart shell |
| `pip install` errors: `Could not find a version that satisfies build123d>=0.9` | Python version too new (>=3.14) or too old (<3.10) | Step 1.8 — create a Python 3.13 venv for this project |
| `pip install` errors: `Could not find a version that satisfies atopile>=0.3` | Python version is 3.12 (atopile needs >=3.13) | Step 1.8 — create a Python 3.13 venv |
| `import atopile` works but `atopile.__version__` raises AttributeError | Atopile doesn't expose `__version__` as an attribute | Use `python -m atopile --version` instead; this is a known atopile quirk, not a broken install |
| `UnicodeEncodeError: 'charmap' codec can't encode character '\\u2728'` (Windows, running atopile) | Atopile uses Rich for console output; PowerShell's default cp1252 codec can't render Unicode glyphs Rich emits | Set `$env:PYTHONIOENCODING = "utf-8"` per session, or set it globally in user environment variables, or use Windows Terminal which handles UTF-8 natively |
| Render chain produces empty AUTO sections | No Issues with the right labels yet | Normal during bootstrap — Issues get filed in Step 4/B.4 |

---

## See also

- [`prompts/bootstrap.md`](../prompts/bootstrap.md) — the bootstrap worksheet
- [`prompts/bootstrap-faq.md`](../prompts/bootstrap-faq.md) — every Section A field, in detail
- [`METHODOLOGY.md`](../METHODOLOGY.md) — the five rules
- [`dev-docs/start-work-checklist.md`](start-work-checklist.md) — pick the right agent each session
- [`dev-docs/architecture/doc-source-of-truth.md`](architecture/doc-source-of-truth.md) — who writes what
