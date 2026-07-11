# `.claude/` — Agent harness

Claude Code agents that implement the systems-first workflow now ship
from the [PHOTONFORGE](https://github.com/Ajam1997/PHOTONFORGE)
marketplace as plugins, not as files in this directory. See the root
[`README.md`](../README.md#install-per-project) for the install
commands.

## `systems-first-core` — Always-on roster

Universal agents that work for every project regardless of discipline:

- `systemmaster` — operator-invoked cross-cutting review
- `verification` — per-commit verification cycle
- `validation` — per-milestone E2E validation
- `systems_lead` — requirements tree, architecture, interfaces

## `systems-first-<discipline>` — Opt-in discipline packs

One thin plugin per discipline. Activate by:

1. Edit `config/disciplines.yml` and set the discipline to active.
2. `claude plugin install systems-first-<discipline>@photonforge`.

Available packs:

| Pack | Contains | Use when |
|---|---|---|
| `systems-first-software` | `software_lead` | Pure software project |
| `systems-first-firmware` | `firmware_lead` | Embedded / RTOS work |
| `systems-first-electrical` | `electrical_lead` | PCB / schematic work |
| `systems-first-mechanical` | `mechanical_lead` | CAD / FEA / DVT work |
| `systems-first-manufacturing` | `manufacturing_lead` | DFM / DFA / EVT / PVT |
| `systems-first-regulatory` | `regulatory_lead` | FCC / CE / UL / safety standards |

You can mix packs freely. A battery-powered IoT device with a custom
enclosure pulls in software + firmware + electrical + mechanical +
manufacturing + regulatory.

## Authoring conventions (for the marketplace repo, not this one)

Agent definitions are now authored and versioned in PHOTONFORGE, not
here. For reference, every agent file there follows the same
structure (lifted from PHOTONForge):

```yaml
---
name: <agent-name>
description: >
  <one-paragraph description of what the agent does and when to invoke it>
tools: Read, Write, Edit, Bash, Grep, Glob
model: inherit | sonnet | haiku | opus
memory: project | user
color: <named color>
---

# <Agent Name>

<Operating prompt: what the agent does, what it reads, what it writes,
 what it doesn't do.>

## Paired Superpowers Skills

<List of `superpowers:<skill>` cues. Mandate vs recommend per role.>
```

Keep them short (≤300 lines). Long agent definitions accumulate cruft
and reduce the agent's signal-to-noise. To propose a change to an
agent's behavior, open a PR against PHOTONFORGE.
