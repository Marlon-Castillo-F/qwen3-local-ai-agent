---
title: Deadlock graph analysis
topic: blocking-deadlocks
source: https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-deadlocks-guide
consulted: 2026-09-09
---

## Summary

A deadlock is a cycle in which sessions each hold a resource needed by another participant. SQL Server detects the cycle and selects a victim so the other work can proceed. This differs from ordinary blocking, which has no cycle and can persist until a holder releases its resource. Extended Events, including system_health in common installations, can capture deadlock XML.

## Key concepts

- The victim list identifies the transaction rolled back.
- Process nodes describe sessions, statements and execution context.
- Resource nodes show owners, waiters and lock modes.
- Consistent access order and shorter transactions can break recurring cycles.

## Common mistakes

- Treating deadlock timeout and command timeout as the same mechanism.
- Fixing only the victim statement without inspecting all participants.
- Assuming one index is always the correct remedy.
- Publishing deadlock XML without redacting application data.

## Diagnostic workflow

1. Preserve the complete XML from a trusted capture.
2. Identify victim, processes, resources, owners and waiters.
3. Reconstruct the access cycle and statement order.
4. Review indexes, transaction scope, isolation and access order.
5. Reproduce safely and confirm recurrence is eliminated.

## Example

Session A can own a key lock needed by B while B owns another key lock needed by A. Making both paths access resources in the same order can remove the cycle without weakening isolation.
