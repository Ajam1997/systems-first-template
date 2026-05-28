#!/usr/bin/env python3
"""Render dev-docs/ markdown into the GitHub Wiki — one-way, idempotent.

This is the source-of-truth chain (HB-3):

    GitHub Issues  --generate_docs.py-->  dev-docs/<AUTO files>
                                              |
                                              | (other dev-docs/ files are hand-authored)
                                              v
                                   migrate_wiki.py --push
                                              |
                                              v
                                       github.com/.../wiki

Wiki page names are auto-derived from the dev-docs/ path: title-case each
component, join with `-`. `index.md` becomes `Home`; `<dir>/index.md`
becomes `<Dir>`.

A wiki page may opt out of overwrite by carrying `<!-- WIKI:LOCAL-ONLY -->`
on its first line. That page is preserved verbatim even if the source file
in dev-docs/ has changed. Use this for hand-edited wiki-only memory aids.

Sidebar (`_Sidebar.md`) is generated from `dev-docs/_wiki-nav.yml`. Do not
hand-edit the sidebar on the wiki — your edits will be overwritten on the
next push (it cannot be marked LOCAL-ONLY).

Usage:
  python scripts/migrate_wiki.py --diff   # preview, no writes
  python scripts/migrate_wiki.py --push   # apply

Auth: requires `gh auth login` (HTTPS push uses gh as credential helper) OR
a WIKI_PUSH_TOKEN env var (used by .github/workflows/wiki-publish.yml).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml

def _resolve_repo() -> str:
    """Return '<owner>/<repo>'. Tries env vars, then git remote."""
    owner = os.environ.get("REPO_OWNER")
    repo = os.environ.get("REPO_NAME")
    if owner and repo:
        return f"{owner}/{repo}"
    # Parse from git remote
    try:
        url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
        if m:
            return f"{m.group(1)}/{m.group(2)}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    raise SystemExit(
        "Cannot resolve repo. Set REPO_OWNER + REPO_NAME or run from a git "
        "checkout with origin pointed at github.com."
    )


REPO = _resolve_repo()
WIKI_URL = f"https://github.com/{REPO}.wiki.git"
REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "dev-docs"
NAV_PATH = DOCS_DIR / "_wiki-nav.yml"

LOCAL_ONLY_MARKER = "<!-- WIKI:LOCAL-ONLY -->"

WIKI_PAGE_EXTENSION = ".md"


class Action(Enum):
    NEW = "NEW"
    OVERWRITE = "OVERWRITE"
    SKIP_UNCHANGED = "SKIP-UNCHANGED"
    SKIP_LOCAL_ONLY = "SKIP-LOCAL-ONLY"
    DELETE = "DELETED-IN-SOURCE"


@dataclass
class PageOp:
    source: Path | None      # dev-docs/<rel>, or None if source-deleted
    rel: str                  # path relative to dev-docs/
    wiki_name: str            # wiki page name (no extension)
    action: Action
    reason: str = ""

    def describe(self) -> str:
        src = self.rel if self.source else "(deleted)"
        extra = f" — {self.reason}" if self.reason else ""
        return f"{self.action.value:18s}  {src:60s} -> {self.wiki_name}{extra}"


# ---------------------------------------------------------------------------
# Wiki page name derivation
# ---------------------------------------------------------------------------

def _title_word(word: str) -> str:
    """Title-case a single word, leaving date-like tokens alone."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", word):
        return word
    if not word:
        return word
    return word[0].upper() + word[1:]


def derive_wiki_name(rel: str) -> str:
    """Map a dev-docs-relative path to a wiki page name.

    Examples:
      index.md                                 -> Home
      research/index.md                        -> Research
      architecture/doc-source-of-truth.md      -> Architecture-Doc-Source-Of-Truth
      superpowers/specs/2026-05-23-foo.md      -> Superpowers-Specs-2026-05-23-Foo
    """
    p = Path(rel)
    stem_parts = list(p.parts[:-1])
    name = p.stem

    if name == "index" and not stem_parts:
        return "Home"
    if name == "index" and stem_parts:
        # <dir>/index.md -> title-case the directory name word-by-word
        dirname = stem_parts[-1].replace("_", "-")
        return "-".join(_title_word(w) for w in dirname.split("-"))

    components: list[str] = []
    for part in stem_parts:
        # e.g. "github-issues" -> "Github-Issues"
        components.append("-".join(_title_word(w) for w in part.replace("_", "-").split("-")))
    # filename
    components.append("-".join(_title_word(w) for w in name.replace("_", "-").split("-")))
    return "-".join(components)


# ---------------------------------------------------------------------------
# Link rewriting
# ---------------------------------------------------------------------------

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _resolve_md_link(source_rel: str, target: str) -> str | None:
    """Resolve a relative .md link to a wiki page name, or None to leave alone."""
    if target.startswith(("http://", "https://", "#", "mailto:")):
        return None
    anchor = ""
    if "#" in target:
        target, _, anchor = target.partition("#")
        anchor = "#" + anchor
    if not target.endswith(".md"):
        return None
    source_dir = Path(source_rel).parent
    resolved = (source_dir / target).as_posix()
    resolved = re.sub(r"^\./", "", resolved)
    # Drop a leading dev-docs/ if present (some authors include it)
    resolved = re.sub(r"^dev-docs/", "", resolved)
    wiki_name = derive_wiki_name(resolved)
    return wiki_name + anchor


def rewrite_links(content: str, source_rel: str) -> str:
    def repl(m: re.Match) -> str:
        text, target = m.group(1), m.group(2)
        wiki_name = _resolve_md_link(source_rel, target)
        if wiki_name is None:
            return m.group(0)
        return f"[{text}]({wiki_name})"

    return LINK_RE.sub(repl, content)


# ---------------------------------------------------------------------------
# Sidebar generation
# ---------------------------------------------------------------------------

def render_sidebar(nav: dict) -> str:
    """Generate _Sidebar.md content from nav config."""
    lines: list[str] = []
    sections = nav.get("sections", [])
    for i, section in enumerate(sections):
        if i > 0:
            lines.append("---")
            lines.append("")
        title = section.get("title")
        if title:
            lines.append(f"### {title}")
        for item in section.get("items", []):
            label = item["label"]
            page_rel = item["page"]
            wiki_name = derive_wiki_name(page_rel)
            lines.append(f"- [{label}]({wiki_name})")
        lines.append("")
    return "\n".join(lines)


def render_footer() -> str:
    return f"_PHOTONForge — [Source](https://github.com/{REPO})_\n"


# ---------------------------------------------------------------------------
# Plan: compare source tree to wiki tree, emit per-file ops
# ---------------------------------------------------------------------------

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_local_only(wiki_text: str) -> bool:
    return wiki_text.lstrip().startswith(LOCAL_ONLY_MARKER)


def collect_source_pages(nav: dict) -> list[tuple[str, str]]:
    """Walk dev-docs/ and return [(rel, wiki_name)] for every .md not excluded.

    The nav file primarily drives sidebar order; *every* .md in dev-docs/
    that isn't `_wiki-nav.yml` itself gets pushed (so the nav and the
    pushed set are decoupled — easier to extend).
    """
    pairs: list[tuple[str, str]] = []
    seen_wiki_names: dict[str, str] = {}
    for md in sorted(DOCS_DIR.rglob("*.md")):
        rel = md.relative_to(DOCS_DIR).as_posix()
        # Skip hidden / underscore files (e.g. _Sidebar templates, _wiki-nav)
        if any(part.startswith(("_", ".")) for part in Path(rel).parts):
            continue
        wiki_name = derive_wiki_name(rel)
        if wiki_name in seen_wiki_names:
            raise SystemExit(
                f"WIKI PAGE NAME COLLISION: '{wiki_name}'\n"
                f"  {seen_wiki_names[wiki_name]}\n"
                f"  {rel}\n"
                f"Rename one of the source files."
            )
        seen_wiki_names[wiki_name] = rel
        pairs.append((rel, wiki_name))
    return pairs


def plan_operations(source_pairs: list[tuple[str, str]], wiki_dir: Path) -> list[PageOp]:
    """Build a list of PageOps comparing dev-docs/ to the cloned wiki."""
    ops: list[PageOp] = []
    source_wiki_names: set[str] = set()

    for rel, wiki_name in source_pairs:
        source_wiki_names.add(wiki_name)
        source = DOCS_DIR / rel
        dest = wiki_dir / f"{wiki_name}{WIKI_PAGE_EXTENSION}"
        new_content = rewrite_links(source.read_text(encoding="utf-8"), rel)

        if not dest.exists():
            ops.append(PageOp(source, rel, wiki_name, Action.NEW))
            continue

        existing = dest.read_text(encoding="utf-8")
        if _is_local_only(existing):
            ops.append(PageOp(source, rel, wiki_name, Action.SKIP_LOCAL_ONLY,
                              reason=f"{LOCAL_ONLY_MARKER} on line 1 of wiki page"))
            continue

        if _sha256(existing) == _sha256(new_content):
            ops.append(PageOp(source, rel, wiki_name, Action.SKIP_UNCHANGED))
            continue

        ops.append(PageOp(source, rel, wiki_name, Action.OVERWRITE))

    # Detect wiki pages that no longer have a source (DELETE)
    for md in wiki_dir.glob("*.md"):
        name = md.stem
        if name in ("_Sidebar", "_Footer"):
            continue
        if name in source_wiki_names:
            continue
        existing = md.read_text(encoding="utf-8")
        if _is_local_only(existing):
            ops.append(PageOp(None, name, name, Action.SKIP_LOCAL_ONLY,
                              reason="orphan wiki page is LOCAL-ONLY; keeping"))
            continue
        ops.append(PageOp(None, name, name, Action.DELETE,
                          reason="no matching dev-docs/ source"))

    return ops


# ---------------------------------------------------------------------------
# Wiki repo plumbing
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        sys.stderr.write(f"FAILED: {' '.join(cmd)}\n{result.stderr}\n")
        sys.exit(1)
    return result


def _setup_auth_for_clone() -> str:
    """Return the clone URL (with embedded token if WIKI_PUSH_TOKEN is set)."""
    token = os.environ.get("WIKI_PUSH_TOKEN", "").strip()
    if token:
        return f"https://x-access-token:{token}@github.com/{REPO}.wiki.git"
    # Fall back to gh credential helper for local interactive use
    subprocess.run(["gh", "auth", "setup-git"], capture_output=True)
    return WIKI_URL


def clone_wiki(tmpdir: Path) -> Path:
    wiki_dir = tmpdir / "wiki"
    clone_url = _setup_auth_for_clone()
    result = subprocess.run(
        ["git", "clone", clone_url, str(wiki_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        # Empty wiki on first push
        wiki_dir.mkdir(exist_ok=True)
        _run(["git", "init", "-b", "master"], cwd=wiki_dir)
        _run(["git", "remote", "add", "origin", clone_url], cwd=wiki_dir)
    return wiki_dir


def apply_operations(ops: list[PageOp], wiki_dir: Path, nav: dict) -> int:
    """Apply OVERWRITE / NEW / DELETE ops in the wiki working tree.

    Returns the number of changes made.
    """
    changes = 0
    for op in ops:
        dest = wiki_dir / f"{op.wiki_name}{WIKI_PAGE_EXTENSION}"
        if op.action in (Action.NEW, Action.OVERWRITE):
            new_content = rewrite_links(op.source.read_text(encoding="utf-8"), op.rel)
            dest.write_text(new_content, encoding="utf-8")
            changes += 1
        elif op.action == Action.DELETE:
            dest.unlink(missing_ok=True)
            changes += 1
        # SKIP_* actions intentionally do nothing

    # Always regenerate sidebar + footer
    (wiki_dir / "_Sidebar.md").write_text(render_sidebar(nav), encoding="utf-8")
    (wiki_dir / "_Footer.md").write_text(render_footer(), encoding="utf-8")
    return changes


def commit_and_push(wiki_dir: Path) -> None:
    _run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
         cwd=wiki_dir)
    _run(["git", "config", "user.name", "github-actions[bot]"], cwd=wiki_dir)
    _run(["git", "add", "-A"], cwd=wiki_dir)

    status = _run(["git", "status", "--porcelain"], cwd=wiki_dir, check=False)
    if not status.stdout.strip():
        print("No changes to push.")
        return

    _run(["git", "commit", "-m", "docs: regenerate wiki from dev-docs/ [skip ci]"],
         cwd=wiki_dir)

    # Wiki default branch is `master` historically; some are `main`
    push = subprocess.run(["git", "push", "origin", "HEAD:master"],
                          cwd=wiki_dir, capture_output=True, text=True)
    if push.returncode != 0:
        push2 = subprocess.run(["git", "push", "origin", "HEAD:main"],
                               cwd=wiki_dir, capture_output=True, text=True)
        if push2.returncode != 0:
            sys.stderr.write("Push failed on both master and main:\n")
            sys.stderr.write(push.stderr + "\n" + push2.stderr + "\n")
            sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--diff", action="store_true",
                      help="Preview per-file actions; make no writes.")
    mode.add_argument("--push", action="store_true",
                      help="Apply changes and push to the wiki repo.")
    args = ap.parse_args()

    if not NAV_PATH.exists():
        sys.exit(f"Missing nav config at {NAV_PATH}")
    nav = yaml.safe_load(NAV_PATH.read_text(encoding="utf-8"))

    source_pairs = collect_source_pages(nav)

    tmpdir = Path(tempfile.mkdtemp(prefix="photonforge-wiki-"))
    try:
        wiki_dir = clone_wiki(tmpdir)
        ops = plan_operations(source_pairs, wiki_dir)

        print(f"Plan ({len(ops)} ops):")
        for op in ops:
            print("  " + op.describe())

        # Counts
        counts: dict[Action, int] = {}
        for op in ops:
            counts[op.action] = counts.get(op.action, 0) + 1
        summary = " · ".join(f"{a.value}={n}" for a, n in counts.items())
        print(f"\nSummary: {summary}")

        if args.diff:
            print("\n(--diff mode — no writes)")
            return

        # --push
        changes = apply_operations(ops, wiki_dir, nav)
        if changes == 0:
            # Sidebar/footer might still have changed; let commit_and_push decide
            print("\nNo content changes; sidebar/footer regenerated unconditionally.")
        commit_and_push(wiki_dir)
        print(f"\nDone. Wiki: https://github.com/{REPO}/wiki")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
