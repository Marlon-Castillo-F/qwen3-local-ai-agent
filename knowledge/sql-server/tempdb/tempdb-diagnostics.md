---
title: tempdb purpose and evidence-based troubleshooting
topic: tempdb
source: https://learn.microsoft.com/en-us/sql/relational-databases/databases/tempdb-database
consulted: 2026-09-09
---

## Summary

`tempdb` supports temporary objects, worktables, sorts, hashes, spills, row-version stores and other engine operations. It is recreated when SQL Server starts, so it is not a durable user-data store. File sizing and count should respond to measured allocation contention, capacity and workload rather than a universal CPU-based formula.

## Key concepts

- Unexpected growth can come from spills, version stores, temporary objects or large transactions.
- Allocation latch contention differs from storage latency and capacity pressure.
- Equal-sized data files with consistent growth settings can help when multiple files are justified.
- Pre-sizing avoids repeated autogrowth during normal workload peaks.

## Common mistakes

- Creating one data file per CPU without measuring contention.
- Treating every spill as a tempdb configuration problem.
- Shrinking files routinely.
- Ignoring version-store consumers and long-running transactions.

## Diagnostic workflow

1. Determine whether the symptom is space, I/O latency or latch contention.
2. Measure file use, growth events and consumers over time.
3. Correlate spills with plans and memory grants.
4. Check version-store and transaction age.
5. Change sizing or file layout only for an evidenced bottleneck and remeasure.

## Example

Rapid growth during a reporting query plus a plan spill can indicate an underestimated memory grant. Adding tempdb files would not correct that estimation issue.
