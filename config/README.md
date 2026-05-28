# `config/` — Project configuration

This directory holds the three files that adapt the template to *your*
project. Edit them once at project start; revisit on stage transitions.

| File | Purpose |
|---|---|
| `disciplines.yml` | Which discipline-lead agents are active. Activates files in `.claude/agents/`. |
| `evidence-kinds.yml` | Which V&V evidence kinds are valid in your domain (pytest? fea? dvt? bench?). |
| `stages.yml` | Your project's phase model. Each entry maps 1:1 to a GitHub Milestone. |

All three are YAML. `scripts/generate_docs.py` and the agents read them
on every run, so changes take effect immediately.

Resource budgets (mass, power, cost, thermal, etc.) live as
**aggregated KPMs** in `requirements/requirement-map.yml`, not as a
separate file. A budget is a KPM with `aggregation: sum` and a list
of subsystem allocations as children — see `METHODOLOGY.md` "The
V-model and where KPMs live".

## Worked examples

Each file's worked-example section at the top shows typical profiles:
pure software, pure mechanical, mixed-discipline IoT device.

When you change these files, run:

```bash
python -m scripts.generate_docs    # re-render docs from current config + Issues
```

to refresh the AUTO sections of `dev-docs/` immediately.
