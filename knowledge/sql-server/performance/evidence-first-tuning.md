---
title: Evidence-first query performance workflow
topic: performance
source: https://learn.microsoft.com/en-us/sql/relational-databases/performance/display-an-actual-execution-plan
consulted: 2026-09-09
---

## Summary

Performance tuning begins with a reproducible symptom and measured workload context. An Actual Execution Plan adds runtime counters because the statement executes; an Estimated Execution Plan describes the compiled shape without running it. `SET SHOWPLAN_XML` returns estimated plan XML and therefore cannot provide actual row counts. `STATISTICS IO`, `STATISTICS TIME`, Query Store and waits provide complementary evidence.

## Key concepts

- Actual versus estimated rows can expose estimation errors.
- Logical reads describe buffer-pool page access, not just storage I/O.
- CPU and elapsed time answer different questions, especially with parallelism or waits.
- Operator warnings and memory spills are facts to investigate, not automatic root causes.

## Common mistakes

- Treating graphical cost percentages as runtime measurements.
- Optimizing a single execution with unrepresentative parameters.
- Changing multiple settings and indexes simultaneously.
- Claiming an action succeeded without rerunning the workload.

## Diagnostic workflow

1. Record query text, parameters, duration, concurrency and environment.
2. Capture Actual Plan, IO and TIME when safe.
3. Find where row estimates diverge and where resources accumulate.
4. Correlate with Query Store history and wait evidence.
5. Form, test and measure a reversible hypothesis.

## Example

High elapsed time with modest CPU can indicate blocking or I/O waits. CPU greater than elapsed can be normal for a parallel plan because CPU time is accumulated across workers.
