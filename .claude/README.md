# `.claude/` — Agent harness

Claude Code agents that implement the systems-first workflow.

## `agents/` — Always-on roster

Three universal agents that work for every project regardless of
discipline:

- `systemmaster.md` — operator-invoked cross-cutting review
- `verification.md` — per-commit verification cycle
- `validation.md` — per-milestone E2E validation

## `agent-packs/` — Opt-in discipline packs

One subdirectory per discipline. Activate by:

1. Edit `config/disciplines.yml` and set the discipline to active.
2. Copy or symlink the pack's agents into `.claude/agents/`.

Available packs:

| Pack | Contains | Use when |
|---|---|---|
| `software/` | `systems_lead`, `software_lead` | Pure software project |
| `firmware/` | `firmware_lead` | Embedded / RTOS work |
| `electrical/` | `electrical_lead` | PCB / schematic work |
| `mechanical/` | `mechanical_lead` | CAD / FEA / DVT work |
| `manufacturing/` | `manufacturing_lead` | DFM / DFA / EVT / PVT |
| `regulatory/` | `regulatory_lead` | FCC / CE / UL / safety standards |

You can mix packs freely. A battery-powered IoT device with a custom
enclosure pulls in software + firmware + electrical + mechanical +
manufacturing + regulatory.

## Pass 1 status

Pass 1 ships only the `software/` pack and the three universal agents.
Mechanical, electrical, firmware, manufacturing, regulatory are
roadmapped — see `dev-docs/architecture/template-roadmap.md` (to be
written).

## Authoring conventions

Every agent file has the same structure (lifted from PHOTONForge):

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
and reduce the agent's signal-to-noise.
