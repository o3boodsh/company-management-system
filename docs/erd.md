# CompanyOS current and target ERDs

Status: Phase 0 design draft, 2026-10-11. Based on the complete [schema export](../database/company_schema.sql); not a live-database inspection. USD salary currency is approved and monthly is the agreed design assumption for new approved MVP data. Target DDL changes remain proposed. No SQL was executed.

## Current exported schema

```mermaid
erDiagram
    departments o|--o{ employees : "department_id"
    employees ||--o{ employee_projects : "employee_id"
    projects ||--o{ employee_projects : "project_id"

    departments {
        int department_id PK "NOT NULL; AUTO_INCREMENT"
        varchar(100) department_name UK "NOT NULL"
    }
    employees {
        int employee_id PK "NOT NULL; AUTO_INCREMENT"
        varchar(100) full_name "NOT NULL"
        decimal(10,0) salary "NOT NULL; >= 0; legacy currency unknown"
        int department_id FK "NULL; default NULL"
        varchar(150) email UK "NULL; default NULL"
        varchar(20) employee_status "NOT NULL; default Active"
        date hire_date "NULL; default curdate()"
    }
    projects {
        int project_id PK "NOT NULL; AUTO_INCREMENT"
        varchar(150) project_name UK "NOT NULL"
        date start_date "NOT NULL"
        decimal(12,2) budget "NULL; default NULL; >= 0"
    }
    employee_projects {
        int employee_id PK, FK "NOT NULL; composite PK part 1"
        int project_id PK, FK "NOT NULL; composite PK part 2"
        varchar(50) role "NOT NULL"
    }
```

## Proposed target MVP schema

Only salary precision and hire-date default differ physically. All other columns, keys, relationships, and indexes are retained. This diagram does not approve or execute a migration.

```mermaid
erDiagram
    departments o|--o{ employees : "department_id"
    employees ||--o{ employee_projects : "employee_id"
    projects ||--o{ employee_projects : "project_id"

    departments {
        int department_id PK "NOT NULL; AUTO_INCREMENT"
        varchar(100) department_name UK "NOT NULL"
    }
    employees {
        int employee_id PK "NOT NULL; AUTO_INCREMENT"
        varchar(100) full_name "NOT NULL"
        decimal(12,2) salary "PROPOSED; NOT NULL; >= 0"
        int department_id FK "NULL; default NULL"
        varchar(150) email UK "NULL; default NULL"
        varchar(20) employee_status "NOT NULL; default Active"
        date hire_date "PROPOSED: NULL; no current-date default"
    }
    projects {
        int project_id PK "NOT NULL; AUTO_INCREMENT"
        varchar(150) project_name UK "NOT NULL"
        date start_date "NOT NULL"
        decimal(12,2) budget "NULL; default NULL; >= 0"
    }
    employee_projects {
        int employee_id PK, FK "NOT NULL; composite PK part 1"
        int project_id PK, FK "NOT NULL; composite PK part 2"
        varchar(50) role "NOT NULL"
    }
```

## Interpretation and limits

- An employee has zero or one department; a department has zero or many employees. Null department means unassigned.
- Each assignment requires exactly one employee and one project. Each parent can have zero or many assignments.
- Employees and projects form a many-to-many relationship. The ordered composite PK `(employee_id, project_id)` permits one role-bearing row per pair. The role is assignment data, not an authorization role.
- All three foreign keys retain restrictive delete/update behavior; there are no cascades or automatic NULL assignments. No direct project-to-department relationship exists.
- PK means primary-key membership; UK means a unique key, not necessarily mandatory data. Email is nullable. No surrogate assignment ID is proposed.
- Status values remain Active, Inactive, and On Leave under the existing CHECK. Deactivation changes status in a future approved workflow, not relationships or IDs.
- USD/monthly applies to new approved MVP salary data only. The same numeric schema cannot establish training-record provenance. No currency column/table is added. New approved MVP project budgets are explicitly USD; no legacy budget currency is inferred.
- Removing the hire-date expression default means omission yields NULL in the target nullable column; there is no client-side substitute of today's date.

Mermaid diagrams summarize columns and cardinalities. Exact defaults, named constraints, indexes, normalization, and ORM mapping are specified in [database-design.md](database-design.md). Adoption and recovery are specified in [database-migration-plan.md](database-migration-plan.md).
