---
title: Index design without seek and scan absolutes
topic: indexing
source: https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide
consulted: 2026-09-09
---

## Summary

A clustered index stores table rows at its leaf level; a nonclustered index has its own keys and row locator, plus included columns when defined. Index design is a workload decision. A Seek narrows a key range but can still process many rows or drive repeated lookups. A Scan can be efficient when a large portion of compact pages is needed or when no selective access path exists.

## Key concepts

- Selectivity and predicate shape affect useful key order.
- Included columns can cover a query without enlarging every search key.
- On a clustered table, nonclustered row locators include the clustered key.
- Every index consumes storage and adds write and maintenance work.
- A Key Lookup is reasonable for a small qualifying set and costly when repeated at scale.

## Common mistakes

- Calling every Scan bad or every Seek good.
- Removing every Key Lookup without measuring frequency and I/O.
- Copying a missing-index suggestion directly into production.
- Ignoring INSERT, UPDATE, DELETE and maintenance cost.

## Diagnostic workflow

1. Measure query frequency, latency, reads and writes.
2. Inspect predicates, joins, projections and ordering.
3. Compare estimated and actual cardinalities.
4. Estimate overlap with existing indexes and write impact.
5. Test representative alternatives and observe Query Store over time.

## Example

A Seek returning 500,000 keys followed by 500,000 lookups can read more pages than a Scan. A covering index might help, but only after weighing its width, write rate, storage and overlap with existing indexes.
