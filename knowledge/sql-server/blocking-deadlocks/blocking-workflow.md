---
title: Blocking diagnosis before session termination
topic: blocking-deadlocks
source: https://learn.microsoft.com/en-us/troubleshoot/sql/database-engine/performance/understand-resolve-blocking
consulted: 2026-09-09
---

## Summary

Blocking occurs when one session holds a lock incompatible with another request. Short blocking is normal for lock-based concurrency; prolonged blocking can reduce throughput and cause timeouts. Diagnosis follows the blocking chain to the head blocker and examines its statement, transaction, waits, application behavior and isolation context before intervention.

## Key concepts

- `blocking_session_id` helps link waiting requests to blockers.
- Open transactions can retain locks after the visible statement finishes.
- `sys.dm_exec_requests`, `sys.dm_exec_sessions`, waiting-task and lock DMVs provide complementary facts.
- Killing a session triggers rollback and can extend impact.

## Common mistakes

- Killing the head blocker as the first diagnostic step.
- Confusing a runnable, CPU-heavy query with a lock wait.
- Ignoring sleeping sessions with open transactions.
- Applying `NOLOCK` universally despite inconsistent-read risks.

## Diagnostic workflow

1. Capture blocked and blocking session IDs over time.
2. Identify the head blocker and open transaction age.
3. Collect exact SQL, wait resource, lock modes and application context.
4. Decide whether the condition is transient, pathological or rollback.
5. Prefer transaction and query correction; terminate only with understood impact.

## Example

A sleeping session with an uncommitted transaction can block writers even when it has no active request. The durable fix is correct transaction handling, not repeated manual kills.
