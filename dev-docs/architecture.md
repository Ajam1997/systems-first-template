# Architecture

> **Template placeholder.** Replace this preamble with your project's
> own architecture narrative. The AUTO sections below are filled in
> automatically by `scripts/generate_docs.py` from GitHub Issues —
> don't hand-edit between the sentinels.

## 1. System Overview

<One-paragraph description of what the system is, its operating
environment, and the top-level technical approach.>

## 2. Requirements

### 2.1 Functional Requirements

<!-- AUTO:fr_table -->
| ID | Description | Implementation | Status |
|:---|:---|:---|:---|
<!-- /AUTO:fr_table -->

### 2.2 Non-Functional Requirements

<!-- AUTO:nfr_table -->
| ID | Description | Specification | Status |
|:---|:---|:---|:---|
<!-- /AUTO:nfr_table -->

### 2.3 Interface Requirements

<!-- AUTO:if_table -->
| ID | Side A | Side B | What crosses | Status |
|:---|:---|:---|:---|:---|
<!-- /AUTO:if_table -->

### 2.4 Key Performance Measures

<!-- AUTO:kpm_table -->
| KPM | Metric | Target | Owner | Verified By | Last Measured | Status |
|:---|:---|:---|:---|:---|:---|:---|
<!-- /AUTO:kpm_table -->

### 2.5 V&V Matrix

The «verify» relationship between requirements and their proofs.
Lines are auto-extracted from the `**Verified By:**` and `**Validated By:**`
sections of each Issue body — see
[V&V format spec](architecture/vv-matrix.md). Coverage column: ✓ fully
covered, ⚠ partial, ✗ unverified.

<!-- AUTO:vv_matrix -->
| ID | Type | Verified By | Validated By | Coverage |
|:---|:---|:---|:---|:---:|
<!-- /AUTO:vv_matrix -->

## 3. Behavior & Structure Models

Add SysML-flavored Mermaid diagrams under `dev-docs/architecture/` and
link them here:

- State machines — pipeline lifecycle, mode transitions
- Activity diagrams — flow-of-control with «flow item» types on arrows
- Block Definition Diagrams — subsystem composition
- Use Case diagrams (optional) — actors and system boundary

The PHOTONForge System Review §6 has a worked example of all four.

## 4. Decision Log

<Per major architecture decision, a short entry: date, decision,
alternatives considered, rationale. Append-only.>

## 5. References

- [METHODOLOGY.md](../METHODOLOGY.md) — the five rules
- [requirements/requirement-map.yml](../requirements/requirement-map.yml) — decomposition tree
- [config/disciplines.yml](../config/disciplines.yml) — active discipline leads
- Resource budgets: aggregated KPMs in [requirements/requirement-map.yml](../requirements/requirement-map.yml)
