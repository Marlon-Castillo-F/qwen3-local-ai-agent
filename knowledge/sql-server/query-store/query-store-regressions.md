---
title: Query Store for regression analysis
topic: query-store
source: https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store
consulted: 2026-09-09
---

## Summary

Query Store persists query texts, plan history, aggregated runtime statistics and, in supported versions, wait statistics. It helps compare performance across time windows and plan changes. A new plan correlated with a regression is evidence to investigate, not automatic proof of causation. Plan forcing is an operational option with monitoring and rollback implications.

## Key concepts

- Runtime statistics are aggregated into intervals.
- One query can have multiple plans over time.
- Regressed-query views help prioritize changes in duration, CPU, I/O or executions.
- Capture mode, size limit and cleanup policy affect retained evidence.

## Common mistakes

- Assuming Query Store automatically chooses and forces the best plan.
- Comparing intervals with different workload volume or parameters.
- Forcing a plan without monitoring failures and changing data distributions.
- Ignoring Query Store state and storage limits.

## Diagnostic workflow

1. Confirm Query Store is collecting and not read-only unexpectedly.
2. Select the symptom interval and a comparable healthy interval.
3. Compare plans, runtime distributions, execution counts and waits.
4. Validate whether parameters, statistics or schema also changed.
5. Test remediation and monitor subsequent intervals.

## Example

If average duration doubled after a plan change, inspect execution count, CPU, I/O and parameter patterns. Forcing the earlier plan can be a controlled mitigation, but it is not a substitute for understanding the regression.
