---
title: Backup types, log chain and point-in-time restore
topic: backup-restore
source: https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/restore-a-sql-server-database-to-a-point-in-time-full-recovery-model
consulted: 2026-09-09
---

## Summary

A full backup supplies a restore base. A differential contains extents changed since its differential base, normally the latest conventional full backup. A transaction log backup preserves log records in sequence and enables point-in-time recovery under an appropriate recovery model and intact log chain. A restore commonly applies full, optional latest suitable differential, then every required log backup in order.

## Key concepts

- `NORECOVERY` keeps the database restoring so more backups can be applied.
- `RECOVERY` completes recovery and normally ends that restore sequence.
- `STOPAT` targets a point contained in the log restore sequence.
- A tail-log backup can preserve log records not yet backed up before a restore after failure.

## Common mistakes

- Saying a differential contains changes since the previous differential.
- Recovering an intermediate restore and then expecting to continue the log chain.
- Assuming a full backup truncates the transaction log.
- Designing a backup schedule without testing restores.

## Diagnostic workflow

1. Confirm recovery model and backup history.
2. Identify a full backup before the target time.
3. Select a compatible differential when useful.
4. Validate every required log backup and its order.
5. Restore in a nonproduction location and verify the target time and application consistency.

## Example

For a target at 10:37, restore a suitable full with `NORECOVERY`, an optional differential with `NORECOVERY`, and successive log backups. Apply `STOPAT` to the relevant log restore and finish with `RECOVERY` only after the target is reached.
