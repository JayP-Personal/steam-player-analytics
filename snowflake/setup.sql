-- snowflake/setup.sql
-- Account setup for steam-player-analytics. Safe to re-run.
-- Public keys are NOT stored here: set them with ALTER USER ... SET RSA_PUBLIC_KEY.
--
-- Runs entirely as ACCOUNTADMIN for simplicity on a solo trial account.
-- In production you'd split this across SYSADMIN (objects), USERADMIN
-- (users/roles) and SECURITYADMIN (grants).

use role accountadmin;

-- 1. Cost guardrail -------------------------------------------------------
create resource monitor if not exists steam_monthly_monitor
  with credit_quota = 10
  frequency = monthly
  start_timestamp = immediately
  triggers
    on 75 percent do notify
    on 100 percent do suspend
    on 110 percent do suspend_immediate;

-- 2. Warehouse -------------------------------------------------------------
create warehouse if not exists steam_wh
  warehouse_size = xsmall
  auto_suspend = 60
  auto_resume = true
  initially_suspended = true;

alter warehouse steam_wh set resource_monitor = steam_monthly_monitor;

-- 3. Database and RAW schema (dbt creates its own schemas) ----------------
create database if not exists steam_db;
create schema if not exists steam_db.raw;

-- 4. Roles ------------------------------------------------------------------
create role if not exists loader      comment = 'Writes RAW';
create role if not exists transformer comment = 'Reads RAW, builds dbt models';
create role if not exists reporter    comment = 'Reads marts';

-- Attach custom roles under SYSADMIN so admins can use them
grant role loader      to role sysadmin;
grant role transformer to role sysadmin;
grant role reporter    to role sysadmin;

-- 5. Grants -----------------------------------------------------------------
-- Everyone needs the warehouse and the database
grant usage on warehouse steam_wh to role loader;
grant usage on warehouse steam_wh to role transformer;
grant usage on warehouse steam_wh to role reporter;
grant usage on database steam_db to role loader;
grant usage on database steam_db to role transformer;
grant usage on database steam_db to role reporter;

-- LOADER: create and write tables in RAW
grant usage, create table on schema steam_db.raw to role loader;
grant select, insert, update, delete, truncate on all tables    in schema steam_db.raw to role loader;
grant select, insert, update, delete, truncate on future tables in schema steam_db.raw to role loader;

-- TRANSFORMER: read RAW, create its own schemas for models
grant usage on schema steam_db.raw to role transformer;
grant select on all tables    in schema steam_db.raw to role transformer;
grant select on future tables in schema steam_db.raw to role transformer;
grant create schema on database steam_db to role transformer;

-- REPORTER: marts don't exist yet. Grant later via dbt's +grants config.

-- 6. Service users (keys registered separately) ----------------------------
create user if not exists airflow_svc
  type = service
  default_role = loader
  default_warehouse = steam_wh
  default_namespace = steam_db.raw
  comment = 'Airflow ingestion';

create user if not exists dbt_svc
  type = service
  default_role = transformer
  default_warehouse = steam_wh
  default_namespace = steam_db
  comment = 'dbt transformations';

grant role loader      to user airflow_svc;
grant role transformer to user dbt_svc;