---
title: Reading execution plans as evidence
topic: execution-plans
source: https://learn.microsoft.com/en-us/sql/relational-databases/performance/execution-plans
consulted: 2026-09-09
---

## Summary

An execution plan is a tree of physical operators selected to implement a query. Read data flow and operator properties, not only icons. Important facts include predicates, estimated and actual rows, executions, ordered properties, memory grant, warnings, object and index names, and runtime counters when present. Only the plan can identify physical operators such as Table Scan, Index Scan, Index Seek and Key Lookup; `STATISTICS IO` scan count cannot.

## Key concepts

- Nested Loops favors a small outer input and efficient repeated inner access.
- Hash Match can suit larger unsorted inputs but needs an adequate memory grant.
- Merge Join can exploit compatible ordering and may avoid hashing.
- Spills show that an operation used tempdb; investigate estimates, memory and row width.
- Missing-index suggestions omit important workload-wide trade-offs.
- `SET SHOWPLAN_XML ON` and Estimated Execution Plan in SSMS do not execute the query and produce an estimated plan.
- Include Actual Execution Plan in SSMS (`Ctrl+M`) and `SET STATISTICS XML ON` execute the query and return runtime plan information. `SET STATISTICS PROFILE ON` is a tabular alternative when appropriate.

## Common mistakes

- Declaring a Hash Match, Scan or Sort inherently bad.
- Treating an Estimated Plan as proof of runtime behavior.
- Focusing only on the highest estimated percentage.
- Assuming one plan captured once represents every parameter pattern.

## Diagnostic workflow

1. Confirm whether the plan is actual or estimated.
2. Follow the main data flow and compare row estimates with runtime rows.
3. Inspect warnings, spills, predicates and repeated executions.
4. Correlate with IO, TIME, waits and Query Store history.
5. Test changes with representative parameters and concurrency.

## Example

A Hash Match spill is evidence that temporary storage was used. Possible contributors include underestimated rows, wide rows or limited grant, but the plan and runtime metrics must distinguish them.
