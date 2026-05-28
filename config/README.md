# `config/` — Project configuration

This directory holds the four files that adapt the template to *your*
project. Edit them once at project start; revisit on stage transitions.

| File | Purpose |
|---|---|
| `disciplines.yml` | Which discipline-lead agents are active. Activates files in `.claude/agents/`. |
| `evidence-kinds.yml` | Which V&V evidence kinds are valid in your domain (pytest? fea? dvt? bench?). |
| `stages.yml` | Your project's phase model. Each entry maps 1:1 to a GitHub Milestone. |
| `budgets.yml` | Tracked resources: mass, power, cost, thermal envelope, schedule margin. |

All four are YAML. `scripts/generate_docs.py` and the agents read them
on every run, so changes take effect immediately.

## Worked examples

Each file's worked-example section at the top shows three typical
profiles: pure software, pure mechanical, mixed-discipline IoT device.

When you change these files, run:

```bash
python -m scripts.generate_docs    # re-render docs from current config + Issues
```

to refresh the AUTO sections of `dev-docs/` immediately.

## Pass 1 status

Files in this directory will be added in Pass 1. Until then, the agent
roster runs in software-only mode and assumes the PHOTONForge defaults
for evidence kinds and stages.
