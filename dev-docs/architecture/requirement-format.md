# Requirement Format — Default Guide

How every User Need, Functional Requirement, Non-Functional Requirement,
Interface Requirement and KPM in a systems-first project is written. This
is the **default**; a project may tighten it in its own `CLAUDE.md`, but
should not loosen it without recording why.

The rules were derived from a review of 638 requirements extracted from
an existing product, where the same information had been written five
different ways. Each rule exists because its absence produced a specific
defect: statuses nobody could trust, evidence that proved nothing,
duplicates across subsystems, and Issues that hid the decisions behind
them.

> **Mental model:** the requirement body is a form, not an essay. Every
> line has one job, and most lines can be checked by a script.

The examples use five invented systems, one per kind of engineering, so
the format can be seen independent of any real project:

| System | Kind | What it is |
|---|---|---|
| **Waypost** | Software | A parcel-tracking web service |
| **Tern** | Hardware (integrated device) | A handheld weather station with firmware |
| **Brick-48** | Electrical | A 48 V battery charger board |
| **Latchgate** | Mechanical | A folding cargo-bike rack hinge |
| **Northside walk-in** | Human | A clinic's walk-in triage procedure |

A human system is specified the same way as a machine: the "component"
is a role, the "interface" is a handover, and the "test" is an
observation or an audit.

---

## The fourteen rules at a glance

| # | Rule | Checkable by script |
|---|---|---|
| R1 | UNs in user voice; FR, NFR, IF in EARS with **shall** and a named component | yes |
| R2 | Title is a noun phrase, 60 characters or fewer | yes |
| R3 | **What** holds behaviour only; **Rationale** and **Notes** are their own lines | partly |
| R4 | Acceptance is two to four plain sentences, each one check | partly |
| R5 | Implementation is one path per line, verified to exist | yes |
| R6 | NFRs carry **Constraint**, **Threshold**, **Scope** | yes |
| R7 | The ICD file is the contract; the Issue points at it; every crossing has a direction | yes |
| R8 | A KPM has one number, an operator, a unit and an aggregation | yes |
| R9 | A shipped requirement names a test, or says `unverified` and stays open | yes |
| R10 | Four statuses, all filed; a **Decisions** line records what changed it | yes |
| R11 | Stage is the requirement's own; parents may cross subsystems | yes |
| R12 | Source anchors resolve | yes |
| R13 | One behaviour, one test, one FR | no |
| R14 | A requirement lives with the module that implements it | no |

---

## R1. Voice

**User Needs are written in the user's voice.** First person, black-box,
no component names, no mechanisms.

**FR, NFR and IF `What` statements use EARS** (Easy Approach to
Requirements Syntax). One of five keyword patterns, always with
**shall**, always naming a component from the project's architecture
contracts doc. A `What` with no pattern is malformed.

**KPM `What`** states what is measured. No "shall".

### The five EARS patterns

| Pattern | Template |
|---|---|
| Ubiquitous | The `<component>` shall `<response>`. |
| Event | **When** `<trigger>`, the `<component>` shall `<response>`. |
| State | **While** `<state>`, the `<component>` shall `<response>`. |
| Unwanted behaviour | **If** `<condition>`, **then** the `<component>` shall `<response>`. |
| Optional feature | **Where** `<feature is present>`, the `<component>` shall `<response>`. |

Patterns combine in that keyword order: *While … when … the X shall …*.

### Each pattern in each domain

| | Software (Waypost) | Hardware (Tern) | Electrical (Brick-48) | Mechanical (Latchgate) | Human (Northside) |
|---|---|---|---|---|---|
| **Ubiquitous** | The Tracking API shall return timestamps in UTC. | The Enclosure shall admit no water at 1 m depth for 30 minutes. | The Output Stage shall regulate to 54.6 V. | The Hinge shall carry a 60 kg static load. | The Triage Nurse shall record a pain score for every patient. |
| **Event** | When a carrier posts a scan, the Tracking API shall update the parcel's status. | When the user presses Log, the Firmware shall store a reading. | When a battery is connected, the Controller shall begin pre-charge. | When the release lever is pulled, the Latch shall disengage. | When a patient arrives, the Receptionist shall issue a queue number. |
| **State** | While a parcel is in customs, the Notifier shall suppress delivery estimates. | While on battery, the Firmware shall sample every 60 s. | While the cell temperature is below 0 °C, the Controller shall hold charge current at zero. | While folded, the Hinge shall hold the rack within its stowed envelope. | While the waiting room exceeds 12 patients, the Charge Nurse shall open a second triage desk. |
| **Unwanted** | If a carrier feed is silent for 30 minutes, then the Ingest Service shall raise an alert. | If the barometer self-test fails, then the Firmware shall display a sensor fault. | If output current exceeds 12 A, then the Protection Circuit shall open the output. | If the latch is not fully engaged, then the Indicator shall show red. | If a patient reports chest pain, then the Triage Nurse shall escalate to a physician at once. |
| **Optional** | Where SMS is enabled, the Notifier shall send delivery texts. | Where a GPS module is fitted, the Firmware shall tag readings with position. | Where a CAN port is populated, the Controller shall report state of charge. | Where the child-seat kit is fitted, the Hinge shall lock in the upright position only. | Where an interpreter is on shift, the Receptionist shall offer one. |

### User Need voice

| Written as a system description | Written as a need |
|---|---|
| Users can view parcel status on a web page that polls the API every 30 s and shows a map. | I can see where my parcel is right now without contacting anyone. |
| The clinic uses a numbered ticket system with a display board. | I know my place in the queue and roughly how long I will wait. |

The polling interval, the map and the display board are FR material.

---

## R2. Title

A noun phrase naming the capability or constraint. Sixty characters at
most. No verb is required. Never: code identifiers, command syntax, plan
tags ("Phase 2"), or work verbs ("Add", "Create", "Refactor"). The Issue
title is `[ID] <title>`.

| Kind | Poor | Good |
|---|---|---|
| UN | Users can see where their parcel is | Live parcel location |
| FR | Add scan ingest endpoint (Phase 2) | Carrier scan ingest |
| FR | `raiseFault()` called when baro self-test fails | Barometer fault display |
| NFR | The charger must never exceed 60 °C on the case in any mode | Case temperature limit |
| IF | Hinge to frame bolts | Hinge ↔ Frame: mounting pattern and loads |
| KPM | How fast triage is | Arrival-to-triage time, p95 |

KPM titles name the measure and its aggregation. IF titles are
`A ↔ B: <what crosses>`.

---

## R3. What, Rationale, Notes

`What` is one to three EARS sentences: behaviour or constraint, nothing
else. Two more lines exist on every kind:

- **Rationale:** why the requirement exists. One or two sentences, or `NONE`.
- **Notes:** history, superseded approaches, cross-references, intended
  location of unbuilt work, or `NONE`.

Mechanisms and formulas go to the kind's own field: `Implementation`
(FR), `Constraint` (NFR), the ICD file (IF), `Method` (KPM).

**Before**

> **What:** If output current exceeds 12 A the charger opens the output.
> 12 A is used because the connector is rated 15 A and the sense resistor
> has 10 % tolerance. Rev A used a polyfuse; Rev B moves to a comparator.

**After**

> **What:** If output current exceeds 12 A, then the Protection Circuit
> shall open the output within 10 ms.
> **Rationale:** 12 A leaves margin under the connector's 15 A rating
> after 10 % sense tolerance.
> **Notes:** Rev A used a polyfuse; Rev B uses a comparator trip.

---

## R4. Acceptance

Two to four bullets on UN, FR, NFR and IF. None on a KPM. Each bullet is
one plain sentence naming an actor or input and an observable outcome
that **one test or one person** can check. Put any setup in the same
sentence. Do not restate the `What`. No subjective adverbs
("appropriately", "smoothly", "reads as"). No function names.

| Domain | Poor | Good |
|---|---|---|
| Software | Status updates work correctly. | A scan posted for parcel P appears in `GET /parcels/P` within 2 s. |
| Hardware | Device is waterproof. | After 30 minutes at 1 m in fresh water, the opened enclosure shows no moisture on the indicator strip. |
| Electrical | Over-current protection functions. | With a 13 A electronic load applied, the output voltage falls below 1 V within 10 ms. |
| Mechanical | Latch feels secure. | With the latch engaged, a 600 N pull along the rack axis produces less than 1 mm of travel. |
| Human | Nurses escalate properly. | In an audit of 50 chest-pain arrivals, every record shows a physician page within 2 minutes of triage. |

---

## R5. Implementation (FR)

Where the behaviour is realised. One entry per line, `path` or
`path::symbol`, repository-relative. No line numbers (they rot), no
prose, no parentheticals. For non-software artifacts the path is the
artifact's manifest path (schematic sheet, CAD part, procedure
document).

- A `planned` FR shows `(none yet)`. An intended location goes in Notes.
- A `shipped` FR with `(none yet)` is malformed.
- Every path is checked to exist.

| Domain | Entry |
|---|---|
| Software | `services/ingest/src/scan.ts::handleScan` |
| Hardware | `firmware/src/log.c::log_store` |
| Electrical | `electrical/brick48/protection.kicad_sch` |
| Mechanical | `mechanical/latchgate/latch-pawl.step` |
| Human | `procedures/triage/escalation.md` |

---

## R6. Non-Functional Requirements

### Is it an FR or an NFR?

An FR meets a need by **doing something** in response to an input. An
NFR meets a need by **holding a property** across everything the system
does. Both serve user needs; an NFR protects a quality the user assumes,
and other parts of the system depend on it holding.

| Question | FR | NFR |
|---|---|---|
| Does it have a trigger? | yes | no, always true |
| What proves it? | one test with one input | a property check, lint, benchmark, audit or inspection |
| Capability or quality? | capability | quality: speed, safety, limits, portability, maintainability |

A requirement whose natural EARS form is *When …* is usually an FR. One
whose form is ubiquitous or *While …* is usually an NFR.

A **cap, limit or timeout is an NFR**, not a KPM: other parts of the
system rely on it. A KPM is a goal that is measured.

### Fields

| Field | Content |
|---|---|
| **Constraint** | The rule, one sentence. |
| **Threshold** | A number with unit, or `none` for an invariant. |
| **Scope** | The modules that break if the constraint is violated. |

**An invariant (software)**

> **What:** The Database Service shall be the only process that opens the
> parcel store.
> **Constraint:** No service other than the Database Service links the
> storage driver.
> **Threshold:** none
> **Scope:** Database Service, Tracking API, Ingest Service, Notifier

**A budget (electrical)**

> **What:** The Charger shall keep its case temperature within the touch
> limit in every operating mode.
> **Constraint:** Case temperature never exceeds the threshold at full
> load in a 40 °C ambient.
> **Threshold:** 60 °C
> **Scope:** Output Stage, Enclosure, Thermal Pad

**A budget (human)**

> **What:** The Triage Desk shall never be unstaffed during opening hours.
> **Constraint:** A break is taken only after a named replacement is at
> the desk.
> **Threshold:** 0 minutes unstaffed
> **Scope:** Triage Nurse, Charge Nurse

A Scope with one module in it is a warning sign: the requirement is
probably an FR.

---

## R7. Interfaces

The ICD file (`requirements/interfaces/IF-x.y.md`) **is** the contract.
The Issue is a pointer to it, plus the checks that the contract holds.
Signal levels, message shapes, bolt patterns and handover scripts live
only in the ICD.

| Field | Content |
|---|---|
| **Side A / Side B** | Module names from the architecture contracts doc, as `Name (location)`. |
| **What Crosses** | A numbered list of nouns, each with a direction. |
| **Spec** | Path to the ICD file. |
| **Status** | `living` or `planned`. Never `shipped`. |
| **Acceptance** | Two to four checks that the contract holds. |

### Direction

Every crossing starts with `A → B`, `B → A` or `A ↔ B`. The arrow points
**from the side that sends**. A request and its response are one crossing
in the direction of the request. A push or event is its own line. `↔`
only when both directions carry the same thing. The head of each arrow is
the side that must validate what arrives.

**Hardware / electrical: Tern firmware ↔ barometer**

> **Side A:** Firmware (firmware/)
> **Side B:** Barometer Module (electrical/tern/baro)
> **What Crosses:**
> 1. A → B  Measurement request over I²C
> 2. B → A  Data-ready interrupt
> 3. A → B  3.3 V supply
> **Spec:** requirements/interfaces/IF-2.1.md
> **Status:** living
> **Acceptance:**
> - A bus capture shows every request in the ICD's register table acknowledged.
> - The firmware driver and the ICD name the same register addresses.

**Mechanical: Latchgate hinge ↔ bike frame**

> **Side A:** Hinge (mechanical/latchgate)
> **Side B:** Frame (customer-supplied)
> **What Crosses:**
> 1. A ↔ B  Four-bolt M6 mounting pattern
> 2. A → B  Static and shock loads
> 3. B → A  Frame tube envelope

**Human: Northside reception ↔ triage**

> **Side A:** Receptionist (front desk)
> **Side B:** Triage Nurse (triage desk)
> **What Crosses:**
> 1. A → B  Patient record with arrival time and stated complaint
> 2. B → A  Triage category for the queue board
> **Acceptance:**
> - Every handover form in a week's sample has all fields in the ICD completed.

---

## R8. KPMs

One number per KPM.

| Field | Content |
|---|---|
| **Target** | A bare number. |
| **Op** | `<=` `<` `>=` `>` `=` |
| **Unit** | From the project's unit list. |
| **Aggregation** | `independent`, `mean`, `p50`, `p95`, `max`, or a rollup (`sum`, `min`) for budget KPMs. |
| **Method** | How and on what it is measured. |
| **Baseline** | Value at filing, or `none`. |
| **Last Measured** | Filled by `sf-kpm-rollup`. |

A compound target is two KPMs. A target with no number is not a KPM; it
is an NFR or it is not a requirement. The KPM's status lives in the map
and the dashboard, not as a second line in the body.

| Domain | Title | Target | Op | Unit | Aggregation |
|---|---|---|---|---|---|
| Software | Scan-to-status latency, p95 | 2 | <= | s | p95 |
| Hardware | Battery life at 60 s sampling | 30 | >= | days | independent |
| Electrical | Full-load efficiency | 93 | >= | percent | independent |
| Mechanical | Assembly mass | 1.8 | <= | kg | sum |
| Human | Arrival-to-triage time, p95 | 10 | <= | min | p95 |

*Poor:* `Target: usually under 2 s, 5 s at worst, and no timeouts`.
*Good:* two KPMs (p95 `<= 2 s`, max `<= 5 s`) and one NFR (no request
times out).

---

## R9. Evidence

Evidence kinds come from `config/evidence-kinds.yml`. Each line is
`<kind>: <reference>`.

- A test reference names the test, not only the file:
  `pytest: tests/test_ingest.py::test_scan_updates_status`. The name is
  checked to occur in the file.
- `inspection` and `script` are for NFRs: a lint, a search, a structural
  check.
- A User Need is verified by `e2e` or by a recorded demonstration
  (`manual`, `review`, `dvt`), never by a unit test.
- **A `shipped` requirement names at least one piece of evidence of that
  behaviour.** One that cannot renders `Verified By: unverified`, is left
  out of the PR's `Closes` list, and stays open as a V&V gap.
- One artifact may back several requirements only through distinct test
  names or sections.
- `Validated By` is filled by validation at stage close, never at
  authoring time.

| Domain | Verified By line |
|---|---|
| Software | `pytest: tests/test_ingest.py::test_scan_updates_status` |
| Hardware | `dvt: verification/tern/ip67-2026-03.md` |
| Electrical | `bench: verification/brick48/ocp-trip-revB.csv` |
| Mechanical | `fea: mechanical/latchgate/hinge-static-rev3.fea` |
| Human | `review: verification/northside/escalation-audit-q1.md` |

---

## R10. Status and decisions

| Status | Meaning | Issue |
|---|---|---|
| `planned` | Not built. | open |
| `shipped` | Built and staying. | closes when verified |
| `retired` | Built today; a recorded decision removes it. | open until the removal lands |
| `superseded` | Never built; replaced by another requirement. | filed closed, `Superseded by <ID>` |

Every status is filed, so the Issue set and the requirement map always
agree on what exists.

A **Decisions** line appears on any requirement a recorded decision
creates, changes or retires:

> **Decisions:** D-14 replaces the polyfuse with a comparator trip
> (dev-docs/decisions.md#d-14)

| Domain | A retired requirement |
|---|---|
| Software | SMS delivery texts, removed when push notifications replace them |
| Electrical | Polyfuse over-current protection, replaced in Rev B |
| Human | Paper queue tickets, replaced by the display board |

---

## R11. Stage and parents

- Every requirement carries **its own stage**. The milestone comes from
  it, not from a parent.
- `Parent:` may list User Needs from any subsystem and cross-cutting
  NFRs. A requirement serving two needs lists both.
- A requirement whose stage is earlier than every parent's is flagged.
- Cross-cutting NFRs take the first stage.

---

## R12. Source

`Source:` holds one or more `path#heading-slug` entries, one per line,
each resolvable by the link checker. Decision logs carry one anchor per
decision.

*Poor:* `spec.md §4 + notes`. *Good:* `dev-docs/specs/ingest.md#carrier-feeds`.

---

## R13. Granularity

**One FR is one observable behaviour verifiable by one test.**

- Variants along a single axis are one FR whose acceptance enumerates
  them: per carrier, per sensor, per connector, per mounting position,
  per shift.
- A `What` needing more than three EARS sentences, or naming more than
  three independent outcomes, is split.
- When items merge, the lowest id survives and the rest become
  `superseded`. Ids are never reused.

| Too fine | Right |
|---|---|
| FR: UPS scans update status · FR: DHL scans update status · FR: FedEx scans update status | **Carrier scan ingest**, acceptance: "A scan from each of the three supported carriers updates status." |
| FR: Dial position 1 … FR: Dial position 4 | **Sampling interval selection**, acceptance lists the four intervals |

| Too coarse | Right |
|---|---|
| FR: The charger handles all fault conditions (over-current, over-voltage, reverse polarity, over-temperature, cell imbalance) | One FR per protection that has its own trip threshold and its own test |

---

## R14. Ownership

A requirement lives in the subsystem that owns the **component named in
its EARS sentence**. It lives once and lists every need it serves as a
parent. A surface that merely exposes another subsystem's behaviour (a
command, a button, a report line) is an acceptance bullet on the owning
requirement, unless the surface has behaviour of its own.

A requirement filed in the wrong subsystem keeps its id and becomes
`superseded` by a new id in the right one.

---

## Complete bodies, one per kind

### User Need (human system)

```
[UN-301] Known place in the queue

Stage: 2
Status: shipped

What: I know my place in the queue and roughly how long I will wait.

Rationale: Patients who cannot see progress leave or interrupt reception.

Acceptance:
- A patient given a queue number can see that number and the number being served from any waiting-room seat.
- The displayed wait estimate is within 10 minutes of the actual wait for 9 of 10 sampled patients.

Decisions: NONE
Notes: NONE

Verified By:
- manual: verification/northside/queue-walkthrough-2026-02.md

Validated By:
- (none yet)

Source: dev-docs/specs/walk-in.md#waiting
```

### Functional Requirement (software)

```
[FR-1.4] Carrier scan ingest

Parent: UN-101
Stage: 2
Status: shipped

What: When a carrier posts a scan, the Ingest Service shall record it and
the Tracking API shall report the parcel's new status. If the scan names
an unknown parcel, then the Ingest Service shall reject it with a 404.

Rationale: Status must follow the carrier without manual entry.

Acceptance:
- A scan posted for parcel P appears in GET /parcels/P within 2 s.
- A scan from each of the three supported carriers updates status.
- A scan for an unknown tracking number returns 404 and stores nothing.

Implementation:
services/ingest/src/scan.ts::handleScan
services/api/src/parcels.ts::getParcel

Decisions: NONE
Notes: NONE

Verified By:
- pytest: tests/test_ingest.py::test_scan_updates_status
- pytest: tests/test_ingest.py::test_unknown_parcel_rejected

Validated By:
- (none yet)

Source: dev-docs/specs/ingest.md#carrier-feeds
```

### Non-Functional Requirement (electrical)

```
[NFR-2.1] Case temperature limit

Parent: UN-201, NFR-0.2
Stage: 3
Status: planned

What: The Charger shall keep its case temperature within the touch limit
in every operating mode.

Rationale: The case is handled while charging.

Constraint: Case temperature never exceeds the threshold at full load in a 40 °C ambient.
Threshold: 60 °C
Scope: Output Stage, Enclosure, Thermal Pad

Acceptance:
- After 2 hours at 12 A in a 40 °C chamber, no thermocouple on the case reads above 60 °C.
- With the thermal pad omitted, the over-temperature protection trips before the case reaches 60 °C.

Decisions: NONE
Notes: Rev A measured 67 °C; Rev B adds the thermal pad.

Verified By:
- (none yet)

Validated By:
- (none yet)

Source: dev-docs/specs/brick48.md#thermal
```

### Interface Requirement (hardware)

```
[IF-2.1] Firmware ↔ Barometer: I²C measurement

Parent: UN-202
Stage: 2
Status: living

What: The Firmware shall read pressure from the Barometer Module only
through the register interface defined in the ICD.

Side A: Firmware (firmware/)
Side B: Barometer Module (electrical/tern/baro)
What Crosses:
1. A → B  Measurement request over I²C
2. B → A  Data-ready interrupt
3. A → B  3.3 V supply
Spec: requirements/interfaces/IF-2.1.md

Acceptance:
- A bus capture shows every request in the ICD's register table acknowledged.
- The firmware driver and the ICD name the same register addresses.

Verified By:
- hil: verification/tern/baro-bus-capture.md

Source: dev-docs/specs/tern-sensors.md#barometer
```

### KPM (mechanical)

```
[KPM-3.1] Assembly mass

Parent: UN-302
Stage: 3
Status: planned

What: Total mass of the hinge assembly as fitted, including fasteners.

Target: 1.8
Op: <=
Unit: kg
Aggregation: sum
Method: Sum of part masses from the CAD bill of materials, confirmed by weighing the first article.
Baseline: 2.1
Last Measured: (none yet)

Rationale: The rack's rated payload assumes a hinge under 2 kg.

Source: dev-docs/specs/latchgate.md#mass-budget
```

---

## Tooling status

The guide is ahead of the tooling in places. Until the `systems-first`
package and the Issue forms catch up, apply these rules by convention
and review.

| Rule | Issue forms and `systems-first` today | Needed |
|---|---|---|
| R1 EARS check | not enforced | a `What` pattern lint in `sf-docs` or a pre-file script |
| R3 Rationale, Notes, Decisions lines | not in the forms | three optional fields on every form |
| R6 Constraint, Threshold, Scope | forms have `Specification`, `Linked Budget` | replace the two NFR fields; `Threshold` may reference `config/budgets.yml` |
| R7 direction on crossings | free text | a per-line arrow check |
| R8 Target, Op, Unit, Aggregation in the body | aggregation metadata lives in `requirement-map.yml` | keep the map as the source; render the four lines from it |
| R9 `unverified`, test-name check | `file_check` validates paths only | name-in-file check; `Closes` excludes unverified |
| R10 `retired`, `superseded` | labels are `defined`, `verified` and so on | two labels in `sf-labels`; `sf-pr-rollup` must leave them alone |
| R11 explicit stage | stage via milestone | a `Stage` line read by the filing script |
| R12 anchors | not checked | heading resolution in the link checker |
