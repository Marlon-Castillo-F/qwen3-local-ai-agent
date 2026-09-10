---
title: Wait statistics as workload evidence
topic: performance
source: https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-os-wait-stats-transact-sql
consulted: 2026-09-09
---

## Summary

Wait statistics classify time workers could not proceed because they waited for a resource or coordination event. Instance-level totals are cumulative and require context: uptime, collection interval, workload and benign wait types. Query Store and execution DMVs can provide query-level evidence in supported versions and configurations.

## Key concepts

- A wait type suggests where to investigate; it does not prove a root cause by itself.
- Deltas over a representative interval are more useful than unbounded lifetime totals.
- Resource waits, queue waits and external waits require different interpretations.
- CPU pressure can appear as runnable scheduler time rather than one simple wait counter.

## Common mistakes

- Applying a generic top-waits checklist without workload context.
- Clearing statistics in production merely to simplify a report.
- Optimizing harmless background waits.
- Ignoring concurrency and query-level correlation.

## Diagnostic workflow

1. Record server start time and measurement interval.
2. Capture wait deltas and workload throughput together.
3. Exclude documented benign/background waits deliberately.
4. Correlate dominant waits with active requests, plans and resource metrics.
5. Validate improvement with the same interval and workload.

## Example

Lock waits combined with a blocking chain and an open transaction support a blocking hypothesis. Lock waits alone do not justify killing a session.
