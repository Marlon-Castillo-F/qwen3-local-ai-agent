---
title: Statistics and cardinality estimation
topic: statistics
source: https://learn.microsoft.com/en-us/sql/relational-databases/statistics/statistics
consulted: 2026-09-09
---

## Summary

Optimizer statistics summarize data distribution. A histogram represents values for the first statistics key, while density information helps estimate combinations. SQL Server combines these summaries with assumptions, constraints and query structure to estimate rows. Estimates influence joins, access methods, memory grants and parallelism.

## Key concepts

- Estimated Rows is a compile-time prediction; Actual Rows requires runtime profiling.
- Stale, sampled or insufficiently correlated statistics can contribute to errors.
- Parameter sensitivity, non-sargable expressions and correlated predicates also matter.
- Updating statistics can help but does not guarantee a good plan.

## Common mistakes

- Believing a histogram contains every distinct value.
- Creating an index as a universal cardinality fix.
- Looking only at the root estimate instead of the first important divergence.
- Ignoring parameter values and compilation context.

## Diagnostic workflow

1. Compare estimated and actual rows through the plan.
2. Find the earliest material divergence.
3. Inspect predicates, parameter values and statistics metadata.
4. Test representative executions and appropriate statistics changes.
5. Recheck plan shape, memory grant and measured resource use.

## Example

An estimate of 100 rows versus two million can cause a Nested Loops plan and undersized memory grant. The mismatch identifies a hypothesis area; it does not by itself prove stale statistics.
