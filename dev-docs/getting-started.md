# Getting Started — From Zero to First Bootstrap

This walks you from a machine with **nothing installed** to a running
project bootstrap. Allow ~30–45 minutes the first time. Subsequent
projects skip everything in Part 1.

If you already have VS Code + Claude Code + Git + Python + gh CLI
installed and authenticated, skip to [Part 4](#part-4--create-your-project-repo).

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

1. The **Claude Code CLI** — the actual agent runtime, distributed as
   an npm package.
2. The **VS Code extension** — a thin UI on top of the CLI. The
   extension is useless without the CLI.

Install in that order.

#### 1.2a — Install Node.js (required by the CLI)

**Windows (PowerShell admin):**

```powershell
winget install --id OpenJS.NodeJS.LTS
```

**Mac:** `brew install node`

**Linux:** see <https://nodejs.org/en/download/package-manager>.

Verify:

```bash
node --version    # >= 18
npm --version
```

Restart your shell after install so the new PATH entries take effect.

#### 1.2b — Install the Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

On Mac/Linux you may need `sudo` for the global install, or set up
a user-local npm prefix to avoid it.

Verify:

```bash
claude --version
```

Run `claude` from any project directory to start a CLI session. Sign
in when prompted (browser opens; uses your Anthropic account).

#### 1.2c — Install the VS Code extension

1. Open VS Code.
2. Click the Extensions icon in the left sidebar (or `Ctrl+Shift+X`).
3. Search for **"Claude Code"** (publisher: Anthropic).
4. Click Install.
5. After install, click the Claude icon in the left sidebar. The
   extension auto-detects the CLI you installed in 1.2b and inherits
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

### 1.4 — Python 3.11+

**Windows:** install from <https://www.python.org/downloads/windows/>.
On the first installer screen, check **"Add python.exe to PATH"**
before clicking Install.

**Mac:** `brew install python@3.12` (install Homebrew from
<https://brew.sh/> first if needed).

**Linux:** `sudo apt install python3.11 python3-pip`.

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

### 2.3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs PyYAML and requests — the only third-party deps.

### 2.4 — Open in VS Code

```bash
code .
```

The Claude Code panel opens automatically. You'll come back to it in
Part 5.

---

## Part 3 — Tokens & wiki setup

The template has a workflow (`.github/workflows/wiki-publish.yml`)
that auto-publishes `dev-docs/` to the repo's GitHub Wiki on every
push to `main`. It needs a Personal Access Token because GitHub's
default `GITHUB_TOKEN` cannot push to wiki repos.

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

## Part 4 — Create your project repo

Already done in Part 2 if you followed in order. If you skipped
Part 1 because the tools were installed, do Part 2 now.

---

## Part 5 — Run the bootstrap

### 5.1 — Copy and fill the worksheet

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

### 5.2 — Commit the inception record

```bash
git add prompts/bootstrap_<your-handle>.md
git commit -m "chore(inception): scoping worksheet by <your-handle>"
git push
```

This is the project's permanent "this is how it started" record.
It does not get deleted.

### 5.3 — Paste into Claude Code

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

## Part 6 — After the bootstrap

### 6.1 — Watch the wiki populate

After the bootstrap's final push, the **Publish Dev Docs to Wiki**
workflow fires. Browse to the **Wiki** tab on your repo a minute
later — `dev-docs/` content should be there, navigable via the
sidebar.

### 6.2 — Find your first FR

The bootstrap's final message names a next action — usually:

> *Open `dev-docs/architecture/<feature>-engineer-brief.md` for the
> first FR and hand it to @<discipline>_lead.*

Open Claude Code, paste:

> *"Author the engineer brief for FR-1.1. Use the systems_lead
> agent."*

The lead agent reads the requirement map, drafts the brief, and
hands off to the discipline lead named in its `Owner:` line.

### 6.3 — Daily-driver workflow

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
| Render chain produces empty AUTO sections | No Issues with the right labels yet | Normal during bootstrap — Issues get filed in Step 5/B.4 |

---

## See also

- [`prompts/bootstrap.md`](../prompts/bootstrap.md) — the bootstrap worksheet
- [`prompts/bootstrap-faq.md`](../prompts/bootstrap-faq.md) — every Section A field, in detail
- [`METHODOLOGY.md`](../METHODOLOGY.md) — the five rules
- [`dev-docs/start-work-checklist.md`](start-work-checklist.md) — pick the right agent each session
- [`dev-docs/architecture/doc-source-of-truth.md`](architecture/doc-source-of-truth.md) — who writes what
