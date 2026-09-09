---
title: SQL Server query processing foundations
topic: architecture
source: https://learn.microsoft.com/en-us/sql/relational-databases/query-processing-architecture-guide
consulted: 2026-09-09
---

## Summary

SQL Server parses and binds T-SQL, optimizes a logical request into a physical plan, and executes that plan through cooperating operators. The optimizer searches useful alternatives under a time and cost budget; its selected plan is the least expensive one it found, not a mathematical proof of the best possible plan. Estimates, available indexes, required ordering, memory grants and parallelism all influence the choice.

## Key concepts

- Compilation produces a plan using metadata, statistics and the cost model.
- Cardinality estimates feed operator selection, join order, memory grants and parallelism.
- The plan cache can reuse a compiled plan when the statement and context allow it.
- Runtime conditions can differ from compilation assumptions.

## Common mistakes

- Treating estimated cost percentages as measured elapsed time.
- Assuming one operator type is intrinsically good or bad.
- Changing indexes before confirming the workload and runtime evidence.

## Diagnostic workflow

1. Capture the exact statement, parameters and database context.
2. Obtain the actual plan when execution is safe.
3. Compare estimated and actual rows at important operators.
4. Correlate plan facts with logical reads, CPU, elapsed time and waits.
5. Test one hypothesis at a time and measure the effect.

## Example

A Nested Loops join can be efficient for a small outer input with a selective inner access path. The same shape can become expensive if an estimate of ten outer rows becomes one million at runtime.
