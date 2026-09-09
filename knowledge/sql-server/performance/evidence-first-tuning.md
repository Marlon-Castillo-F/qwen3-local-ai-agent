---
title: Evidence-first query performance workflow
topic: performance
source: https://learn.microsoft.com/en-us/sql/relational-databases/performance/display-an-actual-execution-plan
consulted: 2026-09-09
---

## Summary

Performance tuning begins with a reproducible symptom and measured workload context. An Actual Execution Plan adds runtime counters because the statement executes; an Estimated Execution Plan describes the compiled shape without running it. `SET SHOWPLAN_XML ON` and Estimated Execution Plan in SSMS return an estimated plan without executing the statement. They cannot provide actual row counts and must never be presented as ways to capture an actual plan. Capture an actual plan with Include Actual Execution Plan in SSMS (`Ctrl+M`) or `SET STATISTICS XML ON`; `SET STATISTICS PROFILE ON` can provide a tabular runtime profile when appropriate. `STATISTICS IO`, `STATISTICS TIME`, Query Store and waits provide complementary evidence.

## Key concepts

- Actual versus estimated rows can expose estimation errors.
- Logical reads describe buffer-pool page access, not just storage I/O.
- `STATISTICS IO` scan count is an I/O statistic, not a physical-operator name. Do not paraphrase it as “a scan happened.” It cannot establish Table Scan, Index Scan, Index Seek or Key Lookup; only execution-plan evidence can identify those operators.
- CPU and elapsed time answer different questions, especially with parallelism or waits.
- Operator warnings and memory spills are facts to investigate, not automatic root causes.

## Common mistakes

- Treating graphical cost percentages as runtime measurements.
- Inferring a Scan, Seek or Lookup operator from `STATISTICS IO` alone.
- Calling `SHOWPLAN_XML` an actual-plan capture method.
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
