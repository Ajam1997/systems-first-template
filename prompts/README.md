# prompts/

Paste-into-Claude-Code prompts that drive long-running, multi-step
workflows the template can't fully automate but doesn't want the
operator to author from scratch each time.

Each prompt is self-contained: it tells Claude what to read, what to
ask the operator, what to do, and what state to leave the repo in.

| Prompt | Purpose |
|---|---|
| [bootstrap.md](bootstrap.md) | Take a fresh clone of the template through scoping → profile activation → UN drafting → requirement-map.yml → render chain. Run once per project. |
| [bootstrap-faq.md](bootstrap-faq.md) | Operator-facing Q&A for the bootstrap prompt — what profile to pick, UN vs FR, KPM aggregation rules, etc. Look here if you get stuck on one of Claude's questions. |

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
