---
title: Authentication, authorization, logins and database users
topic: security
source: https://learn.microsoft.com/en-us/sql/relational-databases/security/authentication-access/create-a-database-user
consulted: 2026-09-09
---

## Summary

Authentication establishes an identity; authorization determines what that principal may do. A login is commonly an instance-level principal. A database user is a database-level principal and can map to a login, certificate, asymmetric key or exist as a contained user depending on configuration. Roles group permissions and simplify least-privilege administration.

## Key concepts

- Server and database scopes have distinct principals and securables.
- A login can map to a different user in each database.
- Contained database users are an important exception to the login mapping pattern.
- `GRANT`, `DENY` and `REVOKE` have different semantics.
- Effective permissions include role memberships and ownership chains.

## Common mistakes

- Treating authentication and authorization as synonyms.
- Granting broad fixed roles instead of required permissions.
- Assuming every database user must have a login.
- Storing credentials or connection strings in source control.

## Diagnostic workflow

1. Identify the principal and authentication method.
2. Determine server and database mappings.
3. Enumerate role memberships and explicit permissions.
4. Test effective access with a controlled identity.
5. Remove excess grants incrementally and audit the result.

## Example

An application login may authenticate successfully but still receive a permission error because its mapped database user lacks authorization on the requested object.
