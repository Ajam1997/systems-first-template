# Bootstrap Prompt — FAQ

Quick reference for operators running [bootstrap.md](bootstrap.md).
Look here if Claude asks a question and you're not sure how to answer.

Organized in the order of the bootstrap steps. Section A questions
are the fields the operator fills in `bootstrap_<their-name>.md`
*before* pasting into Claude; Section B steps are what Claude
executes after.

---

## Section A — Scoping worksheet fields

### A1. "What is the project, in one sentence?"

The sentence should name **who** uses it, **what** it does, and **why**
(or a constraint that defines it). Skip implementation.

| Good | Bad |
|---|---|
| "An offline photo workflow for hobbyist photographers that scores and renames RAW files." | "A Python CLI." |
| "A handheld inventory scanner for warehouse staff with sub-second barcode reads." | "An ESP32-based device." |
| "An automatic cat-play device that aims a laser around the home when nobody is there." | "A pan-tilt servo project." |

If you can't write the sentence, the project isn't scoped yet — go
brainstorm before bootstrapping.

### A2. "Which disciplines are in scope?" → profile A/B/C

| Profile | Active leads | When |
|---|---|---|
| **A — Software** | systems, software | Code-only artifact: web app, CLI, library, service |
| **B — Mechanical / hardware-led** | systems, mechanical, manufacturing | Machined / molded / fabricated physical thing, no firmware or major electronics |
| **C — Mixed-discipline IoT** | all seven (systems, software, mechanical, electrical, firmware, manufacturing, regulatory) | MCU + PCB + enclosure that ships to consumers (needs FCC/CE) |
| custom | — | Nothing fits cleanly: pick the closest profile, then hand-edit `config/disciplines.yml` after |

**Rule of thumb:** if the system has a microcontroller *and* you ship
it to someone outside your house, you're profile C.

Inactive leads stay in `.claude/agent-packs/` as dormant inventory.
Activate one later by toggling its `active: true` in `disciplines.yml`
and re-running `init_project.py` (without `--activate-profile`).

**If you pick Profile B or C**, your bootstrap will activate
`electrical_lead` and/or `mechanical_lead`. Those agents assume a
specific FOSS code-first tool stack (Atopile + KiCad for electrical,
Build123d + ezdxf for mechanical, FreeCAD FEM for analysis). Read
[../dev-docs/architecture/external-tools.md](../dev-docs/architecture/external-tools.md)
before the first electrical or mechanical engineer brief lands so you
know what tools the agents will name in their authoring instructions.
Install steps are in
[../dev-docs/getting-started.md](../dev-docs/getting-started.md) §1.8.

### A3. "How many top-level user needs do you expect?"

Aim for **6–12 on the first pass.** Fewer than 6 usually means you're
collapsing distinct needs into one. More than 12 usually means you're
sneaking acceptance criteria into the UN list.

You can always add UNs later — the bootstrap is the first pass, not
the only pass.

### A4. "What target markets / certification regimes apply?"

This is what drives `regulatory_lead` activation and how strict V&V
needs to be. Common answers:

| Answer | Implications |
|---|---|
| "Hobby / personal use only" | No regulatory lead. No formal compliance work. |
| "FCC Part 15B (digital device)" | Regulatory lead on. EMC pre-compliance during DVT. Test-house engagement at EVT-gate. |
| "FCC + CE-RED (intentional radiator)" | As above plus radio compliance. Modular cert vs intentional radiator decision early. |
| "UL / IEC 62368 (consumer power)" | Safety standards. Drop test, flame rating, IP rating affect enclosure design. |
| "Medical / IEC 62304" | Heavy software process overhead. Different doc set entirely — this template is *not* the right starting point. |
| "Laser product (IEC 60825)" | Class 1/2/3R determination drives the entire optical-path design. |

If unsure, list the markets you intend to sell into — Claude can map
each to the standards stack.

### A5. "What's the GitHub repo slug?"

`owner/name`. Verify with `gh repo view <slug>` — if that returns the
repo, it's correct.

### A6. "Operator + date"

Your GitHub handle and today's date (YYYY-MM-DD). These stamp the
inception record so future maintainers know who scoped the project
and when.

---

## Section B — Steps Claude executes

## Step 2 — Profile activation

### "Should I run --dry-run first?"

Yes, always. It shows you which YAML files will be overwritten, which
agents will be copied in, and which Milestones will be created. If
anything looks wrong, fix the config before applying.

### "I picked the wrong profile. How do I undo?"

`init_project.py --activate-profile` overwrites `disciplines.yml` and
`stages.yml` — it does *not* delete Milestones already created on
GitHub. To switch:

1. Run again with the new profile (overwrites the YAML).
2. Manually close + delete the Milestones from the old profile in the
   GitHub UI (or via `gh api`) if they don't match the new phase model.

---

## Step 3 — Evidence kinds

### "Which evidence kinds do I keep?"

Trim `config/evidence-kinds.yml` to the ones your project will
actually produce. A pure-software project usually keeps:

`pytest`, `review`, `manual`, `inspection`

A hardware project adds:

`bench`, `dvt`, `evt`, `pvt`, `fea`, `simulation`

A regulated hardware project adds:

`emc`, `regulatory`, `dfm`

You can re-add a kind later. Trimming up front just keeps the V&V
matrix legible.

---

## Step 4 — User-need drafting

### "What's the difference between a UN and an FR?"

| | UN — user need | FR — functional requirement |
|---|---|---|
| **Voice** | "The operator needs to ..." | "The system shall ..." |
| **Granularity** | One per outcome the user values | One per behavior the system delivers to satisfy a UN |
| **Count per project** | 6–12 | 20–60 |
| **Decomposes into** | FRs, NFRs, IFs, KPMs | (leaf — verified directly) |

UN: *"The operator needs to ingest a full SD card without manual
sorting."*
FR: *"The system shall cluster RAW files by capture timestamp within
± 2 s."*

If you can write an `assert` for it, it's an FR. If you write a user
journey for it, it's a UN.

### "What's an interface requirement (IF)?"

A boundary between two components, disciplines, or systems where the
contract has to be explicit. Examples:

- USB-C PD negotiation profile between the PCB and the power supply
- REST API between the mobile app and the backend
- M.2 mechanical interface between the SSD cartridge and the enclosure
- Image format handed from `ingest.py` to `grouping.py`

IFs get their own ICD file at `requirements/interfaces/IF-X.Y.md`.
File one whenever a decision lives on a boundary that two leads have
to agree on.

### "What goes in acceptance criteria?"

Each criterion must be a testable assertion with a measurement. Bad:
"fast enough." Good: "ingest 32 GB SD card in < 4 min on i7-7500U
USB 3.0." If you can't measure it, refine until you can — or admit
it's a wish, not a requirement.

### "What if a UN's acceptance criteria aren't all known yet?"

File the UN with `status:defined` and the criteria you *do* know.
Open a comment on the Issue describing the open questions. The UN
won't move to `status:verified` until every criterion has evidence,
so the gap stays visible.

### "Should I write UNs for non-features (reliability, security,
performance)?"

No — those belong as NFRs hung off the UNs they constrain. UNs are
about the outcome the user values. "RSS stays under 1.5 GB" is an
NFR on the UN that describes the workflow that has to fit in that
budget.

Exception: if a non-functional concern is *the entire reason the
product exists* (e.g., "the system shall preserve photographs for
100 years"), then yes, it's a UN.

---

## Step 5 — Decomposition

### "Can an FR support more than one UN?"

Yes — that's the multi-parent case. Write `fr_to_uns` as a list:

```yaml
functional_requirements:
  FR-1.1:
    fr_to_uns: [UN-001, UN-003]
```

Multi-parent FRs are normal. A "log all errors" FR can serve a
debuggability UN *and* an audit-trail UN simultaneously.

### "When should a KPM aggregate vs stay independent?"

| Aggregation | When to use | Example |
|---|---|---|
| **`independent`** | The KPM is measured directly, not derived from children | "ingest throughput ≥ 80% of USB 3.0 bandwidth" |
| **`sum`** | Parent value = sum of leaf values; budgets work this way | total enclosure mass = sum of mass of each part |
| **`max`** | Parent value = worst (largest) of the leaves; latency budgets | end-to-end latency = max along the critical path |
| **`min`** | Parent value = best-case bound from the leaves; rare | minimum guaranteed battery life across modes |

If you're not sure, start with `independent` and add `aggregates_from`
later when you discover the parent really is built from children.

### "What's a reasonable `margin_target`?"

Depends on how confident you are in the leaf measurements:

| Margin | When |
|---|---|
| **0.10** (10%) | Software KPMs (latency, RSS) — measurements are repeatable |
| **0.20** (20%) | Hardware bench measurements — instrument tolerance + sample variance |
| **0.30** (30%) | Early-design estimates with no measurement yet |
| **0.50** (50%) | Wild guesses — flag it as a known weak spot |

Margin erodes over the project. If you start with 20% and end with
3%, the design is fine but fragile to scope creep.

### "I don't know the KPM target value yet."

File the KPM Issue with `target_value: TBD` and a comment explaining
why. The rollup script will skip it; nothing breaks. Update the
Issue body when you have a number.

### "Do I file all the FRs before the next UN, or all UNs first?"

Either works, but **UNs first** is usually easier — you write the
whole user-need set in one mental mode, then decompose each into
FR/NFR/IF/KPM in a second pass. The bootstrap prompt does it
UN-by-UN because conversation flow favors depth-first, but if you
want breadth-first ask Claude to do it that way.

---

## Step 6 — Render chain

### "`generate_docs.py` ran but the AUTO sections are empty."

Two common causes:

1. The Issues weren't filed with the right labels. Run `gh issue list
   --label UN` and confirm the count matches what you filed.
2. The Issue body doesn't have a `**Verified By:**` section so the
   V&V row renders blank — that's normal until evidence accumulates.

### "`kpm_rollup.py` printed `[skip] KPM-X.Y — no leaf data`."

Expected at bootstrap — there are no measurements yet. The script
becomes useful once leaf KPMs start receiving `KPM Rollup` comments
or artifact-manifest values.

### "`export_sysml.py` produced a file but Syson won't open it."

Most likely cause: a UN/FR title contains a character SysMLv2 doesn't
allow in identifiers. Check `model/system.sysml` for any malformed
`requirement def` line. The script ASCII-sanitizes IDs but not
titles — keep titles plain.

### "`validate_artifacts.py` says PASS but I have no artifacts."

Expected — there's nothing to validate yet. The script becomes a CI
gate once `artifacts/<discipline>/*.md` manifests exist.

---

## Step 7 — After bootstrap

### "What do I do next?"

Open the first FR's Issue. Ask @systems_lead to author the engineer
brief: `dev-docs/architecture/<feature>-engineer-brief.md`. Hand the
brief to the discipline lead named in its `Owner:` line. They write
the implementation; @verification posts evidence; `pr_rollup.py`
moves status labels on merge.

The agent harness is the work surface from here. The bootstrap was
just the runway.

### "How do I bootstrap a second batch of UNs later?"

Open Claude Code on the repo and paste a smaller variant of the
bootstrap prompt, scoped to "draft UN-013 through UN-018." Claude
will read the existing `requirement-map.yml`, infer the numbering and
discipline mix, and resume from where the last bootstrap left off.

---

## Things that look broken but aren't

- **Milestones already exist after a profile change** — `init_project.py`
  is additive. Old Milestones from the previous profile remain unless
  you delete them. Close them by hand if they no longer match the
  active stages.
- **`master` branch on the remote** — if you cloned from a template
  that was created before the default branch was renamed to `main`,
  GitHub may have created a transient `master` branch. Delete it
  with `git push origin --delete master`.
- **Wiki workflow fails with 403** — fine-grained PATs don't support
  wiki write. Generate a classic PAT with `repo` scope and store it
  as the `WIKI_PUSH_TOKEN` repository secret.
- **`generate_docs.py` silently ignored your edit to a living doc** —
  you edited inside an `<!-- AUTO:key -->` sentinel. AUTO sections are
  regenerated from Issues; edit the Issue body instead.

---

## See also

- [bootstrap.md](bootstrap.md) — the prompt itself
- [../METHODOLOGY.md](../METHODOLOGY.md) — the five rules
- [../dev-docs/architecture/doc-source-of-truth.md](../dev-docs/architecture/doc-source-of-truth.md) — who writes what
- [../dev-docs/start-work-checklist.md](../dev-docs/start-work-checklist.md) — picking the right agent
