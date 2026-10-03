"""Smoke-test helpers"""

from snowflake.connector import SnowflakeConnection

from steam_analytics.steam_client import SteamClient


def check_snowflake_session(conn: SnowflakeConnection) -> dict:
    """Return who/where this session is running as."""
    with conn.cursor() as cur:
        cur.execute(
            "select current_user(), current_role(), "
            "current_warehouse(), current_version()"
        )
        user, role, warehouse, version = cur.fetchone()
    return {"user": user, "role": role, "warehouse": warehouse, "version": version}


def write_snowflake_smoke_row(conn: SnowflakeConnection, source: str) -> int:
    """Insert one row tagged with `source`; return how many rows that source has."""
    with conn.cursor() as cur:
        cur.execute(
            "create table if not exists smoke_test "
            "(id integer, source string, loaded_at timestamp_ntz)"
        )
        cur.execute(
            "insert into smoke_test (id, source, loaded_at) "
            "select coalesce(max(id), 0) + 1, %s, current_timestamp() from smoke_test",
            (source,),
        )
        cur.execute("select count(*) from smoke_test where source = %s", (source,))
        return cur.fetchone()[0]

def check_steam_api(client: SteamClient) -> dict:
    # keyless: network + plumbing
    players = client.get_current_players(730)
    # keyed: proves the key is valid
    apps = client.get_app_list(max_results=1)
    if not apps:
        raise ValueError("GetAppList returned no apps")
    return {"cs2_players": players, "sample_app": apps[0]["name"]}