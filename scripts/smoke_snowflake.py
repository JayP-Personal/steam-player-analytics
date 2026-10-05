from hiring_pipeline.db_conn import get_snowflake_conn


def main() -> None:
    with get_snowflake_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "create table if not exists smoke_test ("
            "id integer, source string, loaded_at timestamp_ntz)"
        )
        cur.execute("insert into smoke_test values (1, 'python', current_timestamp())")
        cur.execute("select * from smoke_test order by loaded_at desc limit 5")
        for row in cur.fetchall():
            print(row)


if __name__ == "__main__":
    main()
