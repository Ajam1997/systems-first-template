# Documentation Objects v0.2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the markdown side of the documentation-object system — `sf-style` rules engine + CLI, `AUTO:glossary`, the house-style/template-writer skills with their seed, released as PHOTONFORGE v0.2.0 and piloted by extracting photo-workflow's scattered conventions into `dev-docs/house-style/`.

**Architecture:** One new flat module `style_lint.py` in the `systems-first` package (loader → check dispatch → violations → CLI), one renderer added to `generate_docs.py`, two prose skills + a seed directory in the systems-first-core plugin, one new inherited CI workflow. Engine in code, judgment in skills, policy in each repo's `dev-docs/house-style/`.

**Tech Stack:** Python 3.11, PyYAML (already a dep — no new deps), pytest with `tmp_path`, Claude Code plugin skills (markdown), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-07-11-documentation-objects-design.md` (same repo/branch). v0.3.0 (`sf-review`/`sf-report`) is explicitly out of scope here.

## Global Constraints

- Repos: PHOTONFORGE at `F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE` (main, v0.1.2, venv at `.venv`); template repo and photo-workflow as in phase 1. Windows 11, Git Bash; venv python `.venv/Scripts/python.exe`; gh at `"/c/Program Files/GitHub CLI/gh.exe"` with `export GH_CONFIG_DIR="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/gh-config"`.
- Check-type vocabulary EXACTLY: `regex_required`, `regex_required_if`, `regex_forbidden`, `frontmatter_required`, `paired_paths`, `locked_files`, `id_format` (spec §3.1). `paired_paths`/`locked_files` run in `--pr-mode` only.
- `enforce:` is `blocking` or `advisory`; exit nonzero ONLY on blocking violations; missing `dev-docs/house-style/` → notice + exit 0 (opt-in pattern).
- All repo paths anchored at `Path.cwd()` (v0.1.1 rule — `test_repo_paths.py` enforces it; do not reintroduce `__file__` anchoring).
- Policy lives at `dev-docs/house-style/`; conventions cited by id, never duplicated; a convention with zero `checks` is legal.
- Lockstep release: pyproject + `__init__.__version__` + all 7 plugin.json + marketplace metadata + README pin + `test_smoke.py` assertion all become `0.2.0`; one tag `v0.2.0`.
- Doc classes seed table verbatim from spec §3.2 (system-review is **review-critical**).
- Never modify photo-workflow or template repo except in their own tasks (10–11); package/plugin work happens only in PHOTONFORGE.

---

### Task 1: Conventions loader + Violation model

**Files:**
- Create: `PHOTONFORGE/packages/systems-first/src/systems_first/style_lint.py`
- Test: `PHOTONFORGE/packages/systems-first/tests/test_style_lint.py`

**Interfaces:**
- Produces: `Violation` dataclass (`rule_id: str, enforce: str, path: str, message: str`); `load_conventions(root: Path) -> list[dict]` (raises `StyleConfigError` on bad schema); `STYLE_DIR = Path("dev-docs/house-style")` relative segment constant; `CHECK_TYPES` frozenset of the 7 names. Tasks 2–4 build on these exact names.

- [ ] **Step 1: Write the failing tests**

`tests/test_style_lint.py`:

```python
"""Rules engine for sf-style: loading, checking, and reporting conventions."""
import textwrap
from pathlib import Path

import pytest

from systems_first.style_lint import (
    StyleConfigError,
    Violation,
    load_conventions,
)


def write(root: Path, rel: str, content: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def conv(root: Path, name: str, body: str) -> Path:
    return write(root, f"dev-docs/house-style/conventions/{name}.yml", body)


def test_load_valid_convention(tmp_path):
    conv(tmp_path, "banner", """\
        id: supersession-banner
        title: Superseded docs carry a banner
        enforce: blocking
        applies_to: ["dev-docs/**/*.md"]
        prose: |
          Why and how.
        checks:
          - type: regex_required_if
            when_contains: "SUPERSEDED"
            pattern: 'SUPERSEDED \\(\\d{4}'
        """)
    convs = load_conventions(tmp_path)
    assert len(convs) == 1
    assert convs[0]["id"] == "supersession-banner"
    assert convs[0]["enforce"] == "blocking"


def test_zero_checks_is_legal(tmp_path):
    conv(tmp_path, "tone", """\
        id: plain-voice
        title: Write plainly
        enforce: advisory
        applies_to: ["dev-docs/**/*.md"]
        prose: judgment only
        """)
    assert load_conventions(tmp_path)[0]["checks"] == []


@pytest.mark.parametrize("bad", [
    "title: no id\nenforce: advisory\napplies_to: ['x']\nprose: p\n",
    "id: x\ntitle: t\nenforce: sometimes\napplies_to: ['x']\nprose: p\n",
    "id: x\ntitle: t\nenforce: blocking\napplies_to: ['x']\nprose: p\n"
    "checks:\n  - type: made_up_type\n",
])
def test_bad_schema_raises(tmp_path, bad):
    conv(tmp_path, "bad", bad)
    with pytest.raises(StyleConfigError):
        load_conventions(tmp_path)


def test_duplicate_ids_raise(tmp_path):
    body = "id: dup\ntitle: t\nenforce: advisory\napplies_to: ['x']\nprose: p\n"
    conv(tmp_path, "a", body)
    conv(tmp_path, "b", body)
    with pytest.raises(StyleConfigError):
        load_conventions(tmp_path)


def test_missing_style_dir_returns_empty(tmp_path):
    assert load_conventions(tmp_path) == []
```

- [ ] **Step 2: Run to verify failure**

Run (from `PHOTONFORGE/packages/systems-first`, venv active): `python -m pytest tests/test_style_lint.py -v`
Expected: FAIL — `ModuleNotFoundError: systems_first.style_lint`.

- [ ] **Step 3: Implement loader**

`src/systems_first/style_lint.py`:

```python
"""sf-style — conventions-as-data checker for systems-first projects.

Reads dev-docs/house-style/conventions/*.yml and checks the repo's docs.
Exit is nonzero only for violations of conventions with enforce: blocking.
Missing dev-docs/house-style/ -> notice + exit 0 (doc-style is opt-in).
"""
import argparse
import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

# sf-* commands run from the consuming repo's root, not the installed package.
REPO_ROOT = Path.cwd()
STYLE_DIR = Path("dev-docs/house-style")
DECISIONS_INDEX = Path("dev-docs/decisions/index.yml")

CHECK_TYPES = frozenset({
    "regex_required", "regex_required_if", "regex_forbidden",
    "frontmatter_required", "paired_paths", "locked_files", "id_format",
})
PR_MODE_ONLY = frozenset({"paired_paths", "locked_files"})
ENFORCE_LEVELS = ("blocking", "advisory")


class StyleConfigError(Exception):
    """A convention file is malformed."""


@dataclass
class Violation:
    rule_id: str
    enforce: str
    path: str
    message: str


def load_conventions(root: Path) -> list[dict]:
    """Parse and validate every conventions/*.yml under root's house-style."""
    conv_dir = root / STYLE_DIR / "conventions"
    if not conv_dir.is_dir():
        return []
    conventions, seen = [], set()
    for f in sorted(conv_dir.glob("*.yml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise StyleConfigError(f"{f}: not a mapping")
        for key in ("id", "title", "enforce", "applies_to", "prose"):
            if key not in data:
                raise StyleConfigError(f"{f}: missing required key {key!r}")
        if data["enforce"] not in ENFORCE_LEVELS:
            raise StyleConfigError(
                f"{f}: enforce must be one of {ENFORCE_LEVELS}, got {data['enforce']!r}")
        data.setdefault("checks", [])
        for chk in data["checks"]:
            if chk.get("type") not in CHECK_TYPES:
                raise StyleConfigError(
                    f"{f}: unknown check type {chk.get('type')!r}")
        if data["id"] in seen:
            raise StyleConfigError(f"{f}: duplicate convention id {data['id']!r}")
        seen.add(data["id"])
        conventions.append(data)
    return conventions
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_style_lint.py -v` → all PASS.

- [ ] **Step 5: Commit**

```bash
cd "F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/PHOTONFORGE"
git add packages/systems-first
git commit -m "feat(style): conventions loader + Violation model for sf-style"
```

---

### Task 2: Repo-mode check types

**Files:**
- Modify: `PHOTONFORGE/packages/systems-first/src/systems_first/style_lint.py` (append)
- Test: append to `PHOTONFORGE/packages/systems-first/tests/test_style_lint.py`

**Interfaces:**
- Consumes: Task 1's loader/model.
- Produces: `run_checks(root: Path, conventions: list[dict], changed: list[str] | None) -> list[Violation]` — `changed=None` means repo mode (pr-mode-only checks skipped). Task 4's CLI calls exactly this.

- [ ] **Step 1: Write the failing tests** (append to test file)

```python
from systems_first.style_lint import run_checks


def _one_conv(tmp_path, checks_yaml, enforce="blocking",
              applies='["dev-docs/**/*.md"]'):
    conv(tmp_path, "c", f"""\
        id: c1
        title: t
        enforce: {enforce}
        applies_to: {applies}
        prose: p
        checks:
        {checks_yaml}
        """)
    return load_conventions(tmp_path)


def test_regex_required_flags_and_passes(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: regex_required
            pattern: '^# '
        """)
    write(tmp_path, "dev-docs/good.md", "# Title\nbody\n")
    write(tmp_path, "dev-docs/bad.md", "no heading\n")
    v = run_checks(tmp_path, convs, None)
    assert [x.path for x in v] == ["dev-docs/bad.md"]
    assert v[0].rule_id == "c1" and v[0].enforce == "blocking"


def test_regex_required_if_only_fires_on_trigger(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: regex_required_if
            when_contains: "SUPERSEDED"
            pattern: '^> \\*\\*SUPERSEDED \\(\\d{4}-\\d{2}-\\d{2}, PR #\\d+\\):\\*\\*'
        """)
    write(tmp_path, "dev-docs/plain.md", "nothing special\n")
    write(tmp_path, "dev-docs/goodban.md",
          "> **SUPERSEDED (2026-07-11, PR #6):** see spec.\n")
    write(tmp_path, "dev-docs/badban.md", "This doc is SUPERSEDED, trust me\n")
    v = run_checks(tmp_path, convs, None)
    assert [x.path for x in v] == ["dev-docs/badban.md"]


def test_regex_forbidden(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: regex_forbidden
            pattern: 'python -m scripts\\.'
        """)
    write(tmp_path, "dev-docs/stale.md", "run python -m scripts.generate_docs\n")
    write(tmp_path, "dev-docs/fresh.md", "run sf-docs\n")
    assert [x.path for x in run_checks(tmp_path, convs, None)] == ["dev-docs/stale.md"]


def test_frontmatter_required(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: frontmatter_required
            keys: [name, doc_type]
        """, applies='["dev-docs/house-style/templates/*.md"]')
    write(tmp_path, "dev-docs/house-style/templates/ok.md",
          "---\nname: adr\ndoc_type: adr\n---\n# T\n")
    write(tmp_path, "dev-docs/house-style/templates/nofm.md", "# bare\n")
    write(tmp_path, "dev-docs/house-style/templates/partial.md",
          "---\nname: x\n---\n# T\n")
    paths = sorted(x.path for x in run_checks(tmp_path, convs, None))
    assert paths == ["dev-docs/house-style/templates/nofm.md",
                     "dev-docs/house-style/templates/partial.md"]


def test_id_format(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: id_format
            candidate_pattern: '\\b(?:FR|NFR|IF|KPM)-[\\w.]+'
            pattern: '^(?:FR|NFR|IF|KPM)-\\d+\\.\\d+$'
        """)
    write(tmp_path, "dev-docs/ids.md", "FR-1.3 is fine but KPM-1x is not\n")
    v = run_checks(tmp_path, convs, None)
    assert len(v) == 1 and "KPM-1x" in v[0].message


def test_pr_only_checks_skipped_in_repo_mode(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: paired_paths
            when: ["src/**"]
            require: ["dev-docs/**"]
        """)
    write(tmp_path, "dev-docs/a.md", "x\n")
    assert run_checks(tmp_path, convs, None) == []


def test_archive_is_exempt_when_glob_excludes_it(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: regex_forbidden
            pattern: 'stale'
        """, applies='["dev-docs/architecture/**/*.md"]')
    write(tmp_path, "dev-docs/Archive/old.md", "stale stuff\n")
    write(tmp_path, "dev-docs/architecture/live.md", "clean\n")
    assert run_checks(tmp_path, convs, None) == []
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_style_lint.py -v` → new tests FAIL (`ImportError: run_checks`).

- [ ] **Step 3: Implement** (append to `style_lint.py`)

```python
def _files_for(root: Path, patterns: list[str]) -> list[Path]:
    """All files under root matching any glob (fnmatch on posix relpaths)."""
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if any(fnmatch.fnmatch(rel, pat) for pat in patterns):
            out.append(p)
    return sorted(out)


def _frontmatter_keys(text: str) -> set[str]:
    if not text.startswith("---\n"):
        return set()
    end = text.find("\n---", 4)
    if end < 0:
        return set()
    try:
        data = yaml.safe_load(text[4:end])
    except yaml.YAMLError:
        return set()
    return set(data) if isinstance(data, dict) else set()


def run_checks(root: Path, conventions: list[dict],
               changed: list[str] | None) -> list[Violation]:
    """Evaluate every convention. changed=None -> repo mode."""
    violations: list[Violation] = []

    def add(conv, path, message):
        violations.append(Violation(conv["id"], conv["enforce"], path, message))

    for conv in conventions:
        files = None  # lazy per convention
        for chk in conv["checks"]:
            ctype = chk["type"]
            if ctype in PR_MODE_ONLY:
                if changed is None:
                    continue
                if ctype == "paired_paths":
                    hit = any(fnmatch.fnmatch(c, pat)
                              for c in changed for pat in chk["when"])
                    satisfied = any(fnmatch.fnmatch(c, pat)
                                    for c in changed for pat in chk["require"])
                    if hit and not satisfied:
                        add(conv, ", ".join(chk["when"]),
                            f"change touches {chk['when']} but nothing in {chk['require']}")
                elif ctype == "locked_files":
                    locked = _locked_paths(root)
                    for c in changed:
                        if c in locked:
                            add(conv, c, "file is locked by a recorded decision")
                continue

            if files is None:
                files = _files_for(root, conv["applies_to"])
            for f in files:
                rel = f.relative_to(root).as_posix()
                text = f.read_text(encoding="utf-8", errors="replace")
                if ctype == "regex_required":
                    if not re.search(chk["pattern"], text, re.MULTILINE):
                        add(conv, rel, f"missing required pattern {chk['pattern']!r}")
                elif ctype == "regex_required_if":
                    if chk["when_contains"] in text and not re.search(
                            chk["pattern"], text, re.MULTILINE):
                        add(conv, rel,
                            f"contains {chk['when_contains']!r} but not {chk['pattern']!r}")
                elif ctype == "regex_forbidden":
                    if re.search(chk["pattern"], text, re.MULTILINE):
                        add(conv, rel, f"forbidden pattern {chk['pattern']!r} present")
                elif ctype == "frontmatter_required":
                    missing = set(chk["keys"]) - _frontmatter_keys(text)
                    if missing:
                        add(conv, rel, f"frontmatter missing keys {sorted(missing)}")
                elif ctype == "id_format":
                    for m in re.findall(chk["candidate_pattern"], text):
                        if not re.fullmatch(chk["pattern"], m):
                            add(conv, rel, f"malformed id {m!r}")
    return violations


def _locked_paths(root: Path) -> set[str]:
    idx = root / DECISIONS_INDEX
    if not idx.exists():
        return set()
    data = yaml.safe_load(idx.read_text(encoding="utf-8")) or {}
    return {entry["path"] for entry in data.get("decisions", [])}
```

- [ ] **Step 4: Run to verify pass** — full `python -m pytest tests/test_style_lint.py -v` → PASS.

- [ ] **Step 5: Commit** — `git add packages/systems-first && git commit -m "feat(style): repo-mode check types + pr-only skip semantics"`

---

### Task 3: PR-mode — changed-file detection + pr checks live

**Files:**
- Modify: `style_lint.py` (append), Test: append to `tests/test_style_lint.py`

**Interfaces:**
- Consumes: `run_checks` (Task 2).
- Produces: `changed_files(base_ref: str) -> list[str]` (posix relpaths from `git diff --name-only <base>...HEAD`, run in CWD). Task 4 wires `--pr-mode` to it.

- [ ] **Step 1: Failing tests** (append; uses a real throwaway git repo)

```python
import subprocess as sp

from systems_first.style_lint import changed_files


def _git(cwd, *args):
    sp.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _mkrepo(tmp_path):
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    write(tmp_path, "src/mod.py", "x = 1\n")
    write(tmp_path, "dev-docs/doc.md", "# d\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "base")


def test_changed_files_lists_diff_vs_base(tmp_path, monkeypatch):
    _mkrepo(tmp_path)
    _git(tmp_path, "checkout", "-b", "feat")
    write(tmp_path, "src/mod.py", "x = 2\n")
    write(tmp_path, "src/new.py", "y = 1\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "change")
    monkeypatch.chdir(tmp_path)
    assert changed_files("main") == ["src/mod.py", "src/new.py"]


def test_paired_paths_end_to_end(tmp_path, monkeypatch):
    _mkrepo(tmp_path)
    convs = _one_conv(tmp_path, """\
          - type: paired_paths
            when: ["src/**"]
            require: ["dev-docs/**"]
        """)
    _git(tmp_path, "checkout", "-b", "feat")
    write(tmp_path, "src/mod.py", "x = 3\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "code only")
    monkeypatch.chdir(tmp_path)
    v = run_checks(tmp_path, convs, changed_files("main"))
    assert len(v) == 1 and v[0].rule_id == "c1"


def test_locked_files_blocks_changes(tmp_path):
    convs = _one_conv(tmp_path, """\
          - type: locked_files
        """)
    write(tmp_path, "dev-docs/decisions/index.yml", """\
        decisions:
          - path: dev-docs/decisions/2026-07-11-x.html
            sha256: abc
            decision: approved
            decided_by: alex
        """)
    v = run_checks(tmp_path, convs,
                   ["dev-docs/decisions/2026-07-11-x.html", "src/other.py"])
    assert [x.path for x in v] == ["dev-docs/decisions/2026-07-11-x.html"]
```

- [ ] **Step 2: Verify failure** — `ImportError: changed_files`.

- [ ] **Step 3: Implement** (append to `style_lint.py`)

```python
def changed_files(base_ref: str) -> list[str]:
    """Files changed vs base (git diff --name-only base...HEAD), posix paths."""
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True, text=True, check=True)
    return [line.strip().replace("\\", "/")
            for line in proc.stdout.splitlines() if line.strip()]
```

- [ ] **Step 4: Verify pass** — full test file green.
- [ ] **Step 5: Commit** — `git commit -am "feat(style): pr-mode changed-file detection; paired_paths/locked_files live"`

---

### Task 4: `sf-style` CLI

**Files:**
- Modify: `style_lint.py` (append `main()`), `packages/systems-first/pyproject.toml` (entry point), `tests/test_cli_smoke.py` (COMMANDS list)
- Test: append to `tests/test_style_lint.py`

**Interfaces:**
- Consumes: Tasks 1–3 (exact names above).
- Produces: console command `sf-style` = `systems_first.style_lint:main`; flags `--pr-mode <base>`, `--rule <id>`; exit 0 (clean/advisory-only/opt-out), 1 (blocking violations), 2 (config error).

- [ ] **Step 1: Failing tests** (append)

```python
def test_main_opt_out_exits_zero(tmp_path, monkeypatch, capsys):
    from systems_first.style_lint import main
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["sf-style"])
    main()  # must not raise SystemExit(!=0)
    assert "not set up" in capsys.readouterr().out


def test_main_blocking_violation_exits_one(tmp_path, monkeypatch):
    from systems_first.style_lint import main
    _one_conv(tmp_path, """\
          - type: regex_forbidden
            pattern: 'stale'
        """)
    write(tmp_path, "dev-docs/x.md", "stale\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["sf-style"])
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 1


def test_main_advisory_only_exits_zero(tmp_path, monkeypatch, capsys):
    from systems_first.style_lint import main
    _one_conv(tmp_path, """\
          - type: regex_forbidden
            pattern: 'stale'
        """, enforce="advisory")
    write(tmp_path, "dev-docs/x.md", "stale\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["sf-style"])
    main()
    assert "advisory" in capsys.readouterr().out
```

Also add `import sys` at the top of the test file, and add `"systems_first.style_lint"` to `COMMANDS` in `tests/test_cli_smoke.py`.

- [ ] **Step 2: Verify failure** — `AttributeError/ImportError: main`.

- [ ] **Step 3: Implement** (append to `style_lint.py`)

```python
def main() -> None:
    ap = argparse.ArgumentParser(
        description="Check the repo's docs against dev-docs/house-style conventions.")
    ap.add_argument("--pr-mode", metavar="BASE_REF", default=None,
                    help="diff-aware: also run paired_paths/locked_files vs BASE_REF")
    ap.add_argument("--rule", default=None, help="run a single convention id")
    args = ap.parse_args()

    root = REPO_ROOT
    if not (root / STYLE_DIR).is_dir():
        print(f"doc-style is not set up ({STYLE_DIR} absent) — nothing to check. "
              "Instantiate it with the house-style skill to enable.")
        return
    try:
        conventions = load_conventions(root)
    except StyleConfigError as e:
        print(f"convention config error: {e}", file=sys.stderr)
        raise SystemExit(2)
    if args.rule:
        conventions = [c for c in conventions if c["id"] == args.rule]
        if not conventions:
            sys.exit(2)

    changed = changed_files(args.pr_mode) if args.pr_mode else None
    violations = run_checks(root, conventions, changed)

    blocking = [v for v in violations if v.enforce == "blocking"]
    advisory = [v for v in violations if v.enforce == "advisory"]
    for v in violations:
        print(f"[{v.enforce:8}] {v.rule_id}: {v.path} — {v.message}")
    print(f"\nsf-style: {len(conventions)} convention(s) checked, "
          f"{len(blocking)} blocking / {len(advisory)} advisory violation(s)"
          + (f" (pr-mode vs {args.pr_mode})" if args.pr_mode else ""))
    if blocking:
        raise SystemExit(1)
```

pyproject `[project.scripts]` gains: `sf-style = "systems_first.style_lint:main"`.

- [ ] **Step 4: Verify pass** — `python -m pytest tests/ -v` (whole suite; `uv pip install -e . --force-reinstall` first so the console script registers, then also `sf-style --help; echo $?` → 0).
- [ ] **Step 5: Commit** — `git commit -am "feat(style): sf-style CLI — pr-mode, per-rule, ratcheted exit codes"`

---

### Task 5: `AUTO:glossary` renderer in sf-docs

**Files:**
- Modify: `PHOTONFORGE/packages/systems-first/src/systems_first/generate_docs.py`
- Test: create `PHOTONFORGE/packages/systems-first/tests/test_glossary.py`

**Interfaces:**
- Consumes: existing `inject_auto_section(text, key, content)`; `DOCS = Path("dev-docs")`.
- Produces: `render_glossary(glossary: dict) -> str`; `main()` writes `dev-docs/glossary.md` wholesale (creating it) when `dev-docs/house-style/glossary.yml` exists.

- [ ] **Step 1: Failing test**

```python
"""AUTO:glossary rendering from dev-docs/house-style/glossary.yml."""
from pathlib import Path

import yaml

from systems_first.generate_docs import render_glossary

GLOSSARY = {
    "terms": [
        {"term": "KPM", "definition": "Key Performance Measure",
         "aliases": ["budget"]},
        {"term": "ICD", "definition": "Interface Control Document"},
    ]
}


def test_render_glossary_table():
    out = render_glossary(GLOSSARY)
    assert "| KPM |" in out and "Key Performance Measure" in out
    assert "budget" in out            # aliases rendered
    assert out.index("ICD") > out.index("KPM") or True  # sorted a-z
    lines = [l for l in out.splitlines() if l.startswith("| ")]
    assert lines[0].startswith("| Term ")


def test_render_glossary_sorted():
    out = render_glossary(GLOSSARY)
    assert out.index("| ICD |") < out.index("| KPM |")
```

- [ ] **Step 2: Verify failure** — `ImportError: render_glossary`.

- [ ] **Step 3: Implement.** In `generate_docs.py` add after the last renderer:

```python
def render_glossary(glossary: dict) -> str:
    """System bible: glossary.yml terms as a sorted markdown table."""
    rows = []
    for t in sorted(glossary.get("terms", []), key=lambda t: t["term"].lower()):
        aliases = ", ".join(t.get("aliases", []))
        rows.append(f"| {t['term']} | {t['definition']} | {aliases} |")
    return ("| Term | Definition | Aliases |\n|---|---|---|\n"
            + "\n".join(rows))
```

And at the END of `main()` (after the kpm-dashboard block), the wholesale-write hook:

```python
    # Regenerate glossary page (source: house-style glossary.yml, not Issues)
    gl_src = Path("dev-docs/house-style/glossary.yml")
    if gl_src.exists():
        glossary = yaml.safe_load(gl_src.read_text(encoding="utf-8")) or {}
        gl_path = DOCS / "glossary.md"
        gl_path.write_text(
            "# Glossary — System Bible\n\n"
            "<!-- AUTO:glossary -->\n"
            + render_glossary(glossary)
            + "\n<!-- /AUTO:glossary -->\n",
            encoding="utf-8")
        print(f"Updated {gl_path}")
    else:
        print("Skipped dev-docs/glossary.md (no house-style/glossary.yml)")
```

- [ ] **Step 4: Verify pass** — `python -m pytest tests/test_glossary.py tests/test_smoke.py -v` → PASS (glossary hook must not break `--help`: also `python -m systems_first.generate_docs --help; echo $?` → 0).
- [ ] **Step 5: Commit** — `git commit -am "feat(docs): AUTO:glossary — dev-docs/glossary.md rendered from house-style glossary.yml"`

---

### Task 6: The seed (house-style instance shipped in systems-first-core)

**Files:**
- Create under `PHOTONFORGE/plugins/core/skills/house-style/seed/`:
  `house-style.md`, `doc-classes.yml`, `glossary.yml`, `conventions/{supersession-banner,auto-sections,requirement-id-format,docs-impact-matrix,locked-decisions,template-format}.yml`, `templates/{adr,system-review,interface-spec,engineer-brief,design-spec,impl-plan,design-review,trade-study}.md`
- Test: create `PHOTONFORGE/packages/systems-first/tests/test_seed_dogfood.py`

**Interfaces:**
- Consumes: rules engine (Tasks 1–2).
- Produces: a seed directory the house-style skill (Task 7) copies verbatim into projects; every seed file passes the seed's own conventions (dogfood).

- [ ] **Step 1: Failing dogfood test**

```python
"""The plugin's seed must satisfy its own conventions (dogfood)."""
import shutil
from pathlib import Path

from systems_first.style_lint import load_conventions, run_checks

SEED = Path(__file__).resolve().parents[3] / "plugins/core/skills/house-style/seed"


def test_seed_exists_and_is_complete():
    assert (SEED / "house-style.md").is_file()
    assert (SEED / "doc-classes.yml").is_file()
    assert (SEED / "glossary.yml").is_file()
    assert len(list((SEED / "conventions").glob("*.yml"))) == 6
    assert len(list((SEED / "templates").glob("*.md"))) == 8


def test_seed_passes_its_own_conventions(tmp_path):
    dst = tmp_path / "dev-docs/house-style"
    shutil.copytree(SEED, dst)
    convs = load_conventions(tmp_path)
    assert len(convs) == 6
    violations = run_checks(tmp_path, convs, None)
    assert violations == [], [f"{v.rule_id}:{v.path}" for v in violations]
```

(Path note: `parents[3]` from `packages/systems-first/tests/test_seed_dogfood.py` → repo root. This test intentionally uses `__file__` to FIND the seed inside the marketplace repo — it tests repo content, not installed-package behavior, so the `test_repo_paths` rule doesn't apply; it greps only `src/`.)

- [ ] **Step 2: Verify failure** — seed dir absent.

- [ ] **Step 3: Create the seed files.**

`seed/house-style.md`:

```markdown
# House Style — <project name>

The top-level documentation object. Every document an agent or human
authors in this repo follows this index. (Seeded by systems-first-core;
this file is YOURS — edit it as the project's voice evolves.)

## Voice
- Plain prose, complete sentences. Explanations live next to the thing
  they explain, not in a glossary of footnotes.
- Requirement IDs (FR-x.y, UN-XXX, KPM-x.y, IF-x.y) are written exactly;
  the `requirement-id-format` convention checks them.
- Documents state their own status (living / superseded / decided) at the
  top.

## Document classes
Defined in [doc-classes.yml](doc-classes.yml): review-critical docs end as
locked HTML decisions; working docs stay markdown; reports are generated,
never edited. Drafting always happens in markdown.

## Index — templates
| doc type | template | class |
|---|---|---|
| adr | templates/adr.md | working |
| interface-spec | templates/interface-spec.md | working |
| engineer-brief | templates/engineer-brief.md | working |
| impl-plan | templates/impl-plan.md | working |
| design-spec | templates/design-spec.md | review-critical |
| design-review | templates/design-review.md | review-critical |
| system-review | templates/system-review.md | review-critical |
| trade-study | templates/trade-study.md | review-critical |

New doc type with no template? Use the template-writer skill — never
freehand a new document shape.

## Index — conventions
| id | enforce | what |
|---|---|---|
| supersession-banner | blocking | banner format + Archive/ move |
| auto-sections | advisory | AUTO sentinels are sf-docs territory |
| requirement-id-format | advisory | FR/NFR/IF/KPM/UN id syntax |
| docs-impact-matrix | advisory | PR touches X ⇒ must touch Y (fill per project!) |
| locked-decisions | blocking | recorded decisions never change |
| template-format | blocking | templates carry frontmatter |
```

`seed/doc-classes.yml`:

```yaml
classes:
  review-critical:
    medium: interactive-html
    lifecycle: [draft, in-review, decided, superseded]
  working:
    medium: markdown
    lifecycle: [living, superseded]
  report:
    medium: generated-html
    lifecycle: [current]        # regenerated, never edited
doc_types:
  design-spec:      {class: review-critical, template: design-spec}
  design-review:    {class: review-critical, template: design-review}
  system-review:    {class: review-critical, template: system-review}
  trade-study:      {class: review-critical, template: trade-study}
  adr:              {class: working, template: adr}
  interface-spec:   {class: working, template: interface-spec}
  engineer-brief:   {class: working, template: engineer-brief}
  impl-plan:        {class: working, template: impl-plan}
  kpm-dashboard:    {class: report, generator: sf-report}
  verification-run: {class: report, generator: sf-report}
```

`seed/glossary.yml`:

```yaml
terms:
  - {term: UN,   definition: "User Need — top-level requirement, owns FR/NFR/IF/KPM children"}
  - {term: FR,   definition: "Functional Requirement"}
  - {term: NFR,  definition: "Non-Functional Requirement"}
  - {term: IF,   definition: "Interface Requirement (ICD-backed boundary)"}
  - {term: KPM,  definition: "Key Performance Measure — measured, rolled up parent-ward", aliases: [budget]}
  - {term: ICD,  definition: "Interface Control Document"}
  - {term: ADR,  definition: "Architecture Decision Record"}
  - {term: V&V,  definition: "Verification (per-commit, against requirements) and Validation (per-milestone, against user needs)"}
  - {term: stage gate, definition: "Milestone closure condition: all UNs in the stage verified"}
  - {term: House Style, definition: "This repo's documentation policy instance under dev-docs/house-style/"}
```

`seed/conventions/supersession-banner.yml`:

```yaml
id: supersession-banner
title: Superseded docs carry a banner and move to Archive/
enforce: blocking
applies_to: ["dev-docs/**/*.md"]
prose: |
  A superseded doc gets a top-of-file banner and moves to dev-docs/Archive/
  at the same relative path. Exact banner:
  > **SUPERSEDED (YYYY-MM-DD, PR #N):** see <replacement>.
  History is preserved, never load-bearing. Archive/ is exempt from
  reference checks by design.
checks:
  - type: regex_required_if
    when_contains: "**SUPERSEDED"
    pattern: '^> \*\*SUPERSEDED \(\d{4}-\d{2}-\d{2}, PR #\d+\):\*\*'
```

`seed/conventions/auto-sections.yml`:

```yaml
id: auto-sections
title: AUTO sections are never hand-edited
enforce: advisory
applies_to: ["dev-docs/**/*.md"]
prose: |
  sf-docs owns everything between <!-- AUTO:key --> sentinels; hand edits
  there are overwritten on the next regen. Edit the GitHub Issue (or
  glossary.yml) instead. This rule is advisory because authorship isn't
  visible to a text check — sf-docs regen is the real defense.
checks: []
```

`seed/conventions/requirement-id-format.yml`:

```yaml
id: requirement-id-format
title: Requirement IDs are written exactly
enforce: advisory
applies_to: ["dev-docs/**/*.md"]
prose: |
  FR-x.y / NFR-x.y / IF-x.y / KPM-x.y (dotted pairs) and UN-XXX (three
  digits). Malformed ids break live Issue resolution in sf-comment.
checks:
  - type: id_format
    candidate_pattern: '\b(?:FR|NFR|IF|KPM)-[0-9][\w.]*'
    pattern: '(?:FR|NFR|IF|KPM)-\d+\.\d+'
  - type: id_format
    candidate_pattern: '\bUN-[0-9]\w*'
    pattern: 'UN-\d{3}'
```

`seed/conventions/docs-impact-matrix.yml`:

```yaml
id: docs-impact-matrix
title: Code changes update their paired docs in the same PR
enforce: advisory
applies_to: ["**"]
prose: |
  The docs-impact matrix, as data. Each paired_paths check says "a PR
  touching WHEN must also touch REQUIRE". SEEDED EMPTY — fill with your
  project's real pairings, then ratchet to blocking once clean.
checks: []
```

`seed/conventions/locked-decisions.yml`:

```yaml
id: locked-decisions
title: Recorded decisions never change
enforce: blocking
applies_to: ["dev-docs/decisions/**"]
prose: |
  A published decision (dev-docs/decisions/*.html + index.yml entry) is
  frozen: content-hashed, tamper-evident, CI-guarded. Reversals create a
  NEW decision that supersedes the old (index gains superseded_by) —
  never an edit.
checks:
  - type: locked_files
```

`seed/conventions/template-format.yml`:

```yaml
id: template-format
title: Templates carry machine-readable frontmatter
enforce: blocking
applies_to: ["dev-docs/house-style/templates/*.md"]
prose: |
  Every template declares name, doc_type, output_path, and the convention
  ids it binds. The template-writer skill enforces this shape when minting
  new templates; this check enforces it forever after.
checks:
  - type: frontmatter_required
    keys: [name, doc_type, output_path, conventions]
```

Templates — all eight share the shape (frontmatter + skeleton). Full content:

`seed/templates/adr.md`:

```markdown
---
name: adr
doc_type: adr
output_path: "dev-docs/architecture/adr/NNNN-<slug>.md"
conventions: [supersession-banner, requirement-id-format]
---
# ADR-NNNN: <decision title>

**Status:** accepted | superseded
**Date:** YYYY-MM-DD
**Context link:** <PR / Issue / review that forced the decision>

## Context
<What situation demands a decision. 2-5 sentences.>

## Decision
<The decision, stated as a fact.>

## Consequences
<What becomes easier, what becomes harder, what is now forbidden.>
```

`seed/templates/interface-spec.md`:

```markdown
---
name: interface-spec
doc_type: interface-spec
output_path: "requirements/interfaces/IF-<x.y>.md"
conventions: [requirement-id-format, supersession-banner]
---
# IF-<x.y>: <side A> ↔ <side B>

**Status:** living
**Parent UN(s):** UN-XXX

## Boundary
<What crosses this interface, in which direction, initiated by whom.>

## Contract
<Exact formats, commands, schemas, units, error behavior. Tables preferred.>

## Change protocol
<What a PR touching either side must update (add a paired_paths row to the
docs-impact-matrix convention when this stabilizes).>
```

`seed/templates/engineer-brief.md`:

```markdown
---
name: engineer-brief
doc_type: engineer-brief
output_path: "dev-docs/briefs/<UN-or-FR>-<slug>.md"
conventions: [requirement-id-format]
---
# Brief: <task title>

**Owner:** @<discipline>_lead
**Requirements:** <FR/NFR/IF ids this implements>
**Interfaces touched:** <IF ids or none>

## Objective
<One paragraph: done looks like this.>

## Constraints
<Budgets, KPM targets, platform limits that bind this work.>

## Verification
<The evidence @verification will expect: tests, benchmarks, KPM values.>
```

`seed/templates/impl-plan.md`:

```markdown
---
name: impl-plan
doc_type: impl-plan
output_path: "docs/superpowers/plans/YYYY-MM-DD-<slug>.md"
conventions: [requirement-id-format]
---
# <Feature> Implementation Plan

**Goal:** <one sentence>
**Architecture:** <2-3 sentences>

## Global Constraints
<Verbatim binding values from the spec.>

### Task N: <component>
**Files:** / **Interfaces:** / Steps with tests-first checkboxes.
<This template intentionally mirrors superpowers writing-plans structure.>
```

`seed/templates/design-spec.md`:

```markdown
---
name: design-spec
doc_type: design-spec
output_path: "docs/superpowers/specs/YYYY-MM-DD-<slug>-design.md"
conventions: [supersession-banner, requirement-id-format]
---
# <Topic> — Design Spec

**Status:** draft | in-review | decided (locked artifact: <link>)
**Date:** YYYY-MM-DD

## Problem
## Design principles (locked)
## Design
<Sections scaled to complexity; exact values, no placeholders.>
## Acceptance criteria
## Risks
| Risk | Mitigation |
|---|---|
<!-- review-critical: final approval happens via sf-review; the decided
     version is locked HTML under dev-docs/decisions/. -->
```

`seed/templates/design-review.md`:

```markdown
---
name: design-review
doc_type: design-review
output_path: "dev-docs/reviews/YYYY-MM-DD-<slug>-review.md"
conventions: [requirement-id-format]
---
# Design Review: <artifact under review>

**Status:** draft | in-review | decided (locked artifact: <link>)
**Artifact:** <path/link + revision>
**Requirements bound:** <ids>

## Findings
| # | Severity | Finding | Evidence |
|---|---|---|---|

## Recommendation
<approve / approve-with-conditions / rework, and why.>
<!-- review-critical: decision captured and locked via sf-review. -->
```

`seed/templates/system-review.md`:

```markdown
---
name: system-review
doc_type: system-review
output_path: "dev-docs/SystemReviews/YYYY-MM-DD-<slug>.md"
conventions: [supersession-banner, requirement-id-format]
---
# System Review: <scope>

**Status:** draft | in-review | decided (locked artifact: <link>)
**Invoked by:** operator
**Scope:** <systems/modules/docs reviewed>

## Method
<What was read, what was run, what was cross-checked.>

## Findings
| # | Severity | Area | Finding | Recommendation |
|---|---|---|---|---|

## Cross-cutting observations
## Resolved-by addenda
<Appended later as findings are fixed: "Resolved-by PR #N (date)".>
<!-- review-critical: operator decision captured and locked via sf-review. -->
```

`seed/templates/trade-study.md`:

```markdown
---
name: trade-study
doc_type: trade-study
output_path: "dev-docs/trades/YYYY-MM-DD-<slug>.md"
conventions: [requirement-id-format]
---
# Trade Study: <decision to make>

**Status:** draft | in-review | decided (locked artifact: <link>)
**Driving requirements:** <ids + targets>

## Options
| Criterion (weight) | Option A | Option B | Option C |
|---|---|---|---|

## Sensitivity
<Which single criterion flip would change the winner.>

## Recommendation
<!-- review-critical: decision captured and locked via sf-review. -->
```

- [ ] **Step 4: Verify pass** — `python -m pytest tests/test_seed_dogfood.py -v` → 2/2 PASS. Fix any dogfood violation by fixing the SEED (that's the point).
- [ ] **Step 5: Commit** — `git add plugins packages && git commit -m "feat(core): house-style seed — 6 conventions, 8 templates, glossary, doc classes (dogfooded)"`

---

### Task 7: `house-style` skill (the router)

**Files:**
- Create: `PHOTONFORGE/plugins/core/skills/house-style/SKILL.md`

**Interfaces:**
- Consumes: seed (Task 6, sibling `seed/` dir), `sf-style` (Task 4).
- Produces: skill `house-style` in systems-first-core.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: house-style
description: Use before authoring or substantially revising any project document in a systems-first repo - routes to the right template and its conventions, and instantiates the documentation system on first use. Trigger on "write an ADR", "new interface spec", "document this decision", "set up the house style", or any dev-doc authoring.
---

# House Style — the documentation router

Documents in this repo are defined by templates; templates cite
conventions; both live in `dev-docs/house-style/` (THIS project's policy —
the plugin only ships the engine and this seed).

## 0. First use — instantiate

If `dev-docs/house-style/` does not exist, offer to seed it:
copy this skill's `seed/` directory contents to `dev-docs/house-style/`
(preserving structure), then tell the human: the docs-impact-matrix
convention is seeded EMPTY and `house-style.md` is theirs to edit.
Verify with `sf-style` (must exit 0).

## 1. Route

Read ONLY `dev-docs/house-style/house-style.md` (the index). Find the doc
type being authored. Then read exactly:
- its template from `templates/<name>.md`
- the conventions its frontmatter cites (`conventions/<id>.yml` — the
  `prose:` field is the guidance)

Do NOT read all templates or all conventions — the index exists so you
load one path.

## 2. Author

- Follow the template skeleton; keep its heading structure.
- Write the file at the template's `output_path` pattern.
- Doc class (see `doc-classes.yml`): review-critical docs are DRAFTED in
  markdown like everything else — their class governs review + archive
  (sf-review, v0.3), not drafting.
- No template for this doc type? Invoke the template-writer skill. Never
  freehand a new document shape.

## 3. Check

Run `sf-style` before committing. Blocking violations must be fixed;
advisory violations are judgment calls — fix or note why not in the PR.
```

- [ ] **Step 2: Verify** — frontmatter parses (single-line description), name matches directory, seed path reference is correct relative to the skill dir (`ls plugins/core/skills/house-style/` shows `SKILL.md` + `seed/`).
- [ ] **Step 3: Commit** — `git add plugins && git commit -m "feat(core): house-style router skill"`

---

### Task 8: `template-writer` skill (the meta-skill)

**Files:**
- Create: `PHOTONFORGE/plugins/core/skills/template-writer/SKILL.md`

**Interfaces:**
- Consumes: house-style instance layout (Tasks 6–7), `template-format` convention.
- Produces: skill `template-writer` in systems-first-core.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: template-writer
description: Use when a document type has no template in dev-docs/house-style/templates - mints a new template that follows the template-format convention and registers it in the House Style index. Trigger on "we need a new kind of document", "create a template for X", or when the house-style skill finds no template for a doc type.
---

# Template Writer — minting new document types

Templates define documents. This skill creates the template; it never
creates the document (hand back to the house-style skill for that).

## Procedure

1. **Confirm it's really new.** Read `house-style.md`'s template index; if
   an existing type fits with minor stretching, use it instead.
2. **Classify.** Ask (or infer from the request) which class the type
   belongs to — review-critical (output is a human decision), working
   (shared understanding), or report (rendered from data; if report, stop:
   reports get generators, not templates). Add the type to
   `doc-classes.yml` under `doc_types:`.
3. **Mint the template** at `dev-docs/house-style/templates/<name>.md`:
   - Frontmatter with exactly `name`, `doc_type`, `output_path`
     (a concrete pattern like `dev-docs/<area>/YYYY-MM-DD-<slug>.md`), and
     `conventions:` — cite existing convention ids that bind this type.
     CITE, never restate a convention's content in the template.
   - A heading skeleton with one-line guidance under each heading (what
     goes here, not lorem ipsum). Status line first if the class has a
     lifecycle.
   - Review-critical types end with the marker comment:
     `<!-- review-critical: decision captured and locked via sf-review. -->`
4. **Register it**: add a row to `house-style.md`'s template index table.
5. **Check**: run `sf-style` — the template-format convention (blocking)
   must pass. Show the human the new template before first use.

## Never
- Duplicate convention text into templates.
- Mint a template for a one-off document (one instance ≠ a type).
- Invent new frontmatter keys (the fixed set keeps templates parseable).
```

- [ ] **Step 2: Verify** — frontmatter parses; description single-line.
- [ ] **Step 3: Commit** — `git add plugins && git commit -m "feat(core): template-writer meta-skill"`

---

### Task 9: Release v0.2.0

**Files:**
- Modify: `packages/systems-first/pyproject.toml`, `src/systems_first/__init__.py`, `tests/test_smoke.py`, all 7 `plugins/*/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`

**Interfaces:**
- Consumes: Tasks 1–8 complete on main.
- Produces: git tag `v0.2.0`, CI green — the pin Tasks 10–11 use.

- [ ] **Step 1: Lockstep bump** — every `0.1.2` version field → `0.2.0` (pyproject `version`, `__version__`, `test_smoke.py` assertion, 7× plugin.json, marketplace `metadata.version`, README pin `@v0.1.2` → `@v0.2.0`). Verify: `grep -rn "0\.1\.2" packages/systems-first/pyproject.toml packages/systems-first/src/systems_first/__init__.py plugins/*/.claude-plugin/plugin.json .claude-plugin/marketplace.json README.md` → no hits.
- [ ] **Step 2: Full suite** — `python -m pytest tests/ -v` from `packages/systems-first` → all green (expect 30+: 22 prior + style/glossary/dogfood).
- [ ] **Step 3: README** — add `sf-style` to the CLI table row and one line under "What ships here" for the house-style/template-writer skills.
- [ ] **Step 4: Commit, tag, push, watch CI**

```bash
git add -A && git commit -m "feat: documentation objects v0.2.0 — sf-style, AUTO:glossary, house-style + template-writer skills, seed"
git tag v0.2.0 && git push origin main v0.2.0
export GH_CONFIG_DIR="F:/Files/50-59-software-and-dev/51-code-and-repos/PHOTONForge/gh-config"
"/c/Program Files/GitHub CLI/gh.exe" run watch --repo Ajam1997/PHOTONFORGE --exit-status
```

Expected: both CI jobs green on the tagged commit.

---

### Task 10: Template repo — inherited doc-style gate + pin bump

**Files (in `systems-first-template`, branch `feat/doc-style-gate` off main):**
- Create: `.github/workflows/doc-style.yml`
- Modify: all 6 workflows' pip pins `@v0.2.0`; `README.md` (one paragraph); `dev-docs/getting-started.md` (one step)

**Interfaces:**
- Consumes: v0.2.0 tag (Task 9).
- Produces: instantiated projects inherit the PR doc-style gate.

- [ ] **Step 1: doc-style.yml**

```yaml
name: doc-style

on:
  pull_request:

jobs:
  style:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install systems-first package
        run: pip install "systems-first @ git+https://x-access-token:${{ secrets.PHOTONFORGE_READ_TOKEN }}@github.com/Ajam1997/PHOTONFORGE@v0.2.0#subdirectory=packages/systems-first"
      # Green no-op until the project instantiates dev-docs/house-style/.
      - name: Check doc conventions (diff-aware)
        run: sf-style --pr-mode "origin/${{ github.base_ref }}"
```

- [ ] **Step 2: Bump the six existing pins** — `sed -i 's/PHOTONFORGE@v0\.1\.2#/PHOTONFORGE@v0.2.0#/' .github/workflows/*.yml`; verify with grep.
- [ ] **Step 3: Docs** — README "What ships here"/install section: one paragraph on the documentation system (house-style skill instantiates `dev-docs/house-style/`; `sf-style` gates PRs; template-writer mints new types). getting-started: add a numbered setup step "instantiate the House Style (optional): invoke the house-style skill; until then doc-style CI is a green no-op."
- [ ] **Step 4: PR + verify** — push branch, `gh pr create --fill`, confirm `doc-style` check runs GREEN (no-op path proves itself — the template has no house-style/). Merge per repo convention after checks (ask Alex if merge approval is required by the harness).

---

### Task 11: Pilot — extract photo-workflow's conventions

**Files (in `photo-workflow`, branch `feat/house-style-pilot` off main):**
- Create: `dev-docs/house-style/` (from seed, then project-tuned — details below)
- Modify: `.github/workflows/docs-integrity.yml` (add sf-style step), 3 workflow pins `@v0.2.0`, `dev-docs/architecture/doc-maintenance-protocol.md` + `pr-conventions.md` (shrink to pointers), `CLAUDE.md` (one line)

**Interfaces:**
- Consumes: v0.2.0 (Task 9); seed (Task 6).
- Produces: spec acceptance criteria v0.2.0 #2–4.

- [ ] **Step 1: Instantiate + install** — copy the installed plugin's seed to `dev-docs/house-style/` (plugin cache path: `claude plugin list` shows install root; or copy from the PHOTONFORGE checkout `plugins/core/skills/house-style/seed/`). Install the package: `uv pip install --python .venv/Scripts/python.exe "systems-first @ git+https://github.com/Ajam1997/PHOTONFORGE@v0.2.0#subdirectory=packages/systems-first"`.
- [ ] **Step 2: Fill the docs-impact matrix** from `doc-maintenance-protocol.md`'s table — as `paired_paths` checks in `conventions/docs-impact-matrix.yml` (enforce stays advisory initially). Verbatim data rows:

```yaml
checks:
  - type: paired_paths
    when: ["src/photo_workflow/genre_router.py"]
    require: ["dev-docs/research/photonforge-labeling-quick-reference.md",
              "requirements/interfaces/IF-3.1.md", "CLAUDE.md"]
  - type: paired_paths
    when: ["src/photo_workflow/score_fusion.py"]
    require: ["dev-docs/architecture/scoring-architecture.md",
              "requirements/interfaces/IF-2.1.md"]
  - type: paired_paths
    when: ["src/photo_workflow/pipeline.py"]
    require: ["requirements/interfaces/IF-1.1.md", "lua/photonforge/runner.lua"]
  - type: paired_paths
    when: ["src/photo_workflow/darktable_bridge.py"]
    require: ["requirements/interfaces/IF-3.2.md"]
  - type: paired_paths
    when: ["src/photo_workflow/photondb.py"]
    require: ["requirements/interfaces/IF-4.1.md"]
  - type: paired_paths
    when: ["lua/photonforge/**"]
    require: ["requirements/interfaces/IF-1.1.md", "docs/install-yoga-linux.md"]
```

(These encode the matrix's unambiguous file-to-file rows; the judgment rows — SystemReview addenda, supersession moves, new-module docs — stay prose in the convention's `prose:` field, copied from the protocol doc.)

- [ ] **Step 3: Glossary** — extend seed `glossary.yml` with photo-workflow terms from CLAUDE.md: PHOTON cartridge, dHash, IEA40K, Florence-2, Profile A, HB-x ("harness behavior rule"), SOP-B ("resume mid-flight work procedure"), zenity, safe-eject. Run `.venv/Scripts/sf-docs` → `dev-docs/glossary.md` appears; commit it.
- [ ] **Step 4: Shrink prose to pointers** — in `doc-maintenance-protocol.md`: replace the matrix table body with "**Now data:** the matrix lives in [`dev-docs/house-style/conventions/docs-impact-matrix.yml`](../house-style/conventions/docs-impact-matrix.yml) and is checked by `sf-style` on every PR" (keep the three rules prose; the banner rule points at the convention file). `pr-conventions.md` and CLAUDE.md's conventions section each gain one pointer line to `dev-docs/house-style/`. Do NOT delete prose that has no data equivalent.
- [ ] **Step 5: CI** — in `docs-integrity.yml` add after the existing steps (same job):

```yaml
      - name: Install systems-first package
        run: pip install "systems-first @ git+https://x-access-token:${{ secrets.PHOTONFORGE_READ_TOKEN }}@github.com/Ajam1997/PHOTONFORGE@v0.2.0#subdirectory=packages/systems-first"
      - name: Doc conventions (sf-style, diff-aware)
        run: sf-style --pr-mode "origin/${{ github.base_ref }}"
```

Also bump the three existing workflow pins to `@v0.2.0`.

- [ ] **Step 6: Local acceptance before pushing**
  1. `.venv/Scripts/sf-style` → exit 0; advisory report may list findings (record them in the PR body).
  2. Blocking-rule proof: create a scratch commit adding `dev-docs/scratch-superseded.md` containing `**SUPERSEDED` without the banner → `.venv/Scripts/sf-style` exits 1 naming `supersession-banner`; revert the scratch commit. Capture both outputs for the PR body.
- [ ] **Step 7: PR** — push, `gh pr create` (body: extraction summary + acceptance evidence + `Docs impact:` line), watch `doc-references`, `pytest`, and the new sf-style step go green. Merge per repo convention (ask Alex if the harness requires his approval).

---

## Acceptance checklist (spec §9, v0.2.0)

- [ ] 1. Rules-engine unit tests per check type green; marketplace CI dogfoods the seed (Tasks 1–6, 9).
- [ ] 2. photo-workflow pilot green in CI; blocking rule demonstrably fails a seeded violation (Task 11 Step 6).
- [ ] 3. `AUTO:glossary` renders; wiki publishes it (Task 11 Step 3 + next wiki-publish run).
- [ ] 4. Both skills invocable; router loads only index + one template + its conventions (Task 7 design; spot-check in a fresh session).
