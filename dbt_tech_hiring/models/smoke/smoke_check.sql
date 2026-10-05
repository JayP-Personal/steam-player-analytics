select
    count(*)        as row_count,
    max(loaded_at)  as latest_load,
    current_role()  as dbt_role,
    current_version()   as snowflake_version
from {{ source('raw', 'smoke_test') }}