# 0001. Use Airflow, Snowflake, dbt and Tableau as the data stack

- **Status:** Accepted
- **Date:** 2026-10-05

## Context
This is a portfolio project aimed at data analyst and entry-level data science roles. The stack should be one that hiring teams recognize and use in production, and each tool should do real work rather than being included for show. Budget is close to zero, so free tiers and trials matter.

## Options considered
1. **Airflow + Snowflake + dbt + Tableau.** Widely used in industry; each tool has a clear job. Snowflake's trial credits are limited, so compute must be kept small.
2. **Local only (Python scripts + DuckDB + a notebook).** Free and simple, but shows less about working with production tools.
3. **Managed ELT tool (e.g. Fivetran) instead of Airflow.** Less code to maintain, but no connectors exist for these job board endpoints, and it hides the orchestration work this project is meant to show.

## Decision
Option 1. Airflow orchestrates daily collection, Snowflake stores raw and modeled data, dbt handles transformations and data tests, Python handles statistical analysis, and Tableau Public presents the results.

## Consequences
- Daily collection gives Airflow a genuine job: scheduling, retries and alerting.
- Snowflake costs must be watched: smallest warehouse size, aggressive auto-suspend.
- If Snowflake credits run out, DuckDB is the fallback; dbt models should avoid Snowflake-only SQL where a portable version exists.
