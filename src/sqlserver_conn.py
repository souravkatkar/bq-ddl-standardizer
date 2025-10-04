import pyodbc

def test_sqlserver_connection(host, port, user, password):
    if port:
        server = f"{host},{port}"
    else:
        server = host
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"UID={user};"
        f"PWD={password};"
        f"Trusted_Connection=no;"
    )
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.databases")
    dbs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return dbs

def get_sqlserver_schemas(host, port, user, password, database):
    if port:
        server = f"{host},{port}"
    else:
        server = host
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Trusted_Connection=no;"
    )
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sys.schemas")
    schemas = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return schemas

def get_sqlserver_tables(host, port, user, password, database, schema):
    if port:
        server = f"{host},{port}"
    else:
        server = host
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Trusted_Connection=no;"
    )
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = ?
    """, (schema,))
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def get_sqlserver_table_schema(host, port, user, password, database, schema, table):
    if port:
        server = f"{host},{port}"
    else:
        server = host
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        f"Trusted_Connection=no;"
    )
    conn = pyodbc.connect(conn_str, autocommit=True)
    cursor = conn.cursor()
    # Get column details
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
    """, (schema, table))
    columns = []
    for col in cursor.fetchall():
        columns.append({
            "name": col[0],
            "type": col[1],
            "nullable": col[2].upper() == "YES",
            "comment": ""  # Will be filled below
        })
    # Get column comments (extended properties)
    cursor.execute(f"""
        SELECT c.name, ep.value
        FROM sys.columns c
        LEFT JOIN sys.extended_properties ep
          ON ep.major_id = OBJECT_ID('{schema}.{table}')
          AND ep.minor_id = c.column_id
          AND ep.name = 'MS_Description'
        WHERE c.object_id = OBJECT_ID('{schema}.{table}')
    """)
    col_comments = {row[0]: row[1] for row in cursor.fetchall() if row[1]}
    for col in columns:
        col["comment"] = col_comments.get(col["name"], "")
    # Get table comment (extended property)
    cursor.execute(f"""
        SELECT ep.value
        FROM sys.extended_properties ep
        WHERE ep.major_id = OBJECT_ID('{schema}.{table}')
          AND ep.minor_id = 0
          AND ep.name = 'MS_Description'
    """)
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