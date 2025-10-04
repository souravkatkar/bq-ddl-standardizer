import psycopg2

def test_postgres_connection(host, port, user, password):
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database="postgres"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    dbs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return dbs

def get_postgres_schemas(host, port, user, password, database):
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()
    cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema');")
    schemas = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return schemas

def get_postgres_tables(host, port, user, password, database, schema):
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s;", (schema,))
    tables = [row[0] for row in cursor.fetchall()]
    print(tables)
    cursor.close()
    conn.close()
    return tables

def get_postgres_table_schema(host, port, user, password, database, schema, table):
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()
    # Get column details
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))
    columns = []
    for col in cursor.fetchall():
        columns.append({
            "name": col[0],
            "type": col[1],
            "nullable": col[2].upper() == "YES",
            "comment": ""  # Will be filled below
        })
    # Get column comments
    cursor.execute("""
        SELECT a.attname, d.description
        FROM pg_catalog.pg_attribute a
        LEFT JOIN pg_catalog.pg_description d
          ON d.objoid = a.attrelid AND d.objsubid = a.attnum
        WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped
    """, (f'"{schema}"."{table}"',))
    col_comments = {row[0]: row[1] for row in cursor.fetchall() if row[1]}
    for col in columns:
        col["comment"] = col_comments.get(col["name"], "")
    # Get table comment
    cursor.execute("""
        SELECT obj_description(%s::regclass)
    """, (f'"{schema}"."{table}"',))
    table_comment_row = cursor.fetchone()
    table_comment = table_comment_row[0] if table_comment_row else ""
    schema_dict = {
        "table_name": table,
        "columns": columns,
        "db": database,
        "schema": schema,
        "table_comment": table_comment
    }
    cursor.close()
    conn.close()
    return schema_dict