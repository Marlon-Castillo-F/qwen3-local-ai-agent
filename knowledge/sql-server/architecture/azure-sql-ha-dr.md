---
title: High availability, disaster recovery and Azure SQL boundaries
topic: architecture
source: https://learn.microsoft.com/en-us/azure/azure-sql/database/business-continuity-high-availability-disaster-recover-hadr-overview
consulted: 2026-09-09
---

## Summary

High availability addresses local component or zone failures and aims to keep a service available. Disaster recovery addresses wider failures and restores service in another location or from backups. RTO describes acceptable recovery time; RPO describes acceptable data-loss exposure. Azure SQL Database is a managed PaaS service, while SQL Server on a VM leaves more operating-system, instance, storage, backup and HA responsibility with the customer.

## Key concepts

- HA and DR solve related but different failure scopes.
- Backups protect against corruption or accidental changes; replicas are not a replacement for backups.
- Zone redundancy, geo-replication, failover groups and geo-restore have different trade-offs.
- Actual RTO/RPO must come from requirements, architecture and tested procedures.

## Common mistakes

- Inventing an SLA without checking the selected service tier and configuration.
- Assuming HA eliminates backup, restore testing or DR planning.
- Saying Azure SQL requires no administration; logical design, security, performance and cost remain responsibilities.

## Diagnostic workflow

1. Define failure scenarios and business RTO/RPO.
2. Inventory service tier, redundancy, backup retention and replica topology.
3. Map each scenario to an HA or DR mechanism.
4. Test failover and restore procedures, including application reconnection.
5. Record measured recovery behavior rather than relying on assumptions.

## Example

A zone-redundant database can address a zonal failure, while a regional outage may require a configured cross-region strategy. The appropriate choice depends on required RPO, RTO, cost and operational complexity.
