# prompts/

Paste-into-Claude-Code prompts that drive long-running, multi-step
workflows the template can't fully automate but doesn't want the
operator to author from scratch each time.

Each prompt is self-contained: it tells Claude what to read, what to
ask the operator, what to do, and what state to leave the repo in.

| Prompt | Purpose |
|---|---|
| [bootstrap.md](bootstrap.md) | Copy-and-fill scoping worksheet *and* execution prompt. Operator copies to `bootstrap_<their-name>.md`, fills Section A, commits as the project's inception record, then pastes into Claude. Claude reads Section A and executes Section B. Run once per project. |
| [bootstrap-faq.md](bootstrap-faq.md) | Operator-facing Q&A for filling Section A of the bootstrap worksheet and for understanding the decisions Claude faces in Section B. Look here if you get stuck on a field. |

## The `bootstrap_<operator>.md` inception record

The bootstrap workflow is **copy-fill-commit-paste**, not interactive:

1. Operator copies `bootstrap.md` to `bootstrap_<their-name>.md`
2. Fills the Section A worksheet by hand
3. Commits it — this becomes the project's permanent "how it started"
   artifact, with operator handle, date, and the five scoping answers
4. Pastes the whole file into a Claude Code session, which executes
   Section B against those answers

The filled file is never deleted. A second operator re-bootstrapping
later makes their own copy. The series of `bootstrap_*.md` files in
`prompts/` is the project's traceable inception history.

## Why prompts and not scripts

A script can do anything deterministic. A prompt earns its keep when
the workflow needs *judgment* — the right discipline mix, the right
first 8–12 user needs, the right KPM aggregation strategy. Those don't
have a right answer without a conversation.

If a prompt's logic stabilizes to the point where it never needs to
ask, promote it to a script and delete it from here.

## Authoring conventions

- Self-contained: the prompt assumes Claude has no prior session
  context. Tell it what files to read first.
- Explicit stop points: name the questions Claude must ask the
  operator before continuing.
- No tokens, no secrets: prompts never instruct Claude to write a PAT
  or API key to disk.
- End with a state report: every prompt's last step is "tell the
  operator what changed and what's next."
