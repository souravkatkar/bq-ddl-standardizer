import oracledb

def get_oracle_py_conn(host, port, user, password, service_name):
    dsn = f"{host}:{port}/{service_name}"
    return oracledb.connect(user=user, password=password, dsn=dsn)

def test_oracle_connection(host, port, user, password, service_name):
    conn = get_oracle_py_conn(host, port, user, password, service_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM v$database")
    db_name = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return [db_name]

def get_oracle_schemas(host, port, user, password, service_name):
    conn = get_oracle_py_conn(host, port, user, password, service_name)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM all_users ORDER BY username")
    schemas = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return schemas

def get_oracle_tables(host, port, user, password, service_name, owner):
    conn = get_oracle_py_conn(host, port, user, password, service_name)
    cursor = conn.cursor()
    query = f"SELECT table_name FROM all_tables WHERE owner = '{owner}' ORDER BY table_name"
    cursor.execute(query)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def get_oracle_table_schema(host, port, user, password, service_name, owner, table):
    conn = get_oracle_py_conn(host, port, user, password, service_name)
    cursor = conn.cursor()
    query = f"""
        SELECT 
            col.column_name, 
            col.data_type, 
            col.nullable,
            comm.comments
        FROM all_tab_columns col
        LEFT JOIN all_col_comments comm
            ON col.owner = comm.owner AND col.table_name = comm.table_name AND col.column_name = comm.column_name
        WHERE col.owner = '{owner}' AND col.table_name = '{table}'
        ORDER BY col.column_id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = []
    for col_name, data_type, nullable, comment in rows:
        columns.append({
            "name": col_name,
            "type": data_type,
            "nullable": (nullable == "Y"),
            "comment": comment or ""
        })
    table_comment_query = f"""
        SELECT comments FROM all_tab_comments
        WHERE owner = '{owner}' AND table_name = '{table}'
    """
    cursor.execute(table_comment_query)
    table_comment_row = cursor.fetchone()
    table_comment = table_comment_row[0] if table_comment_row else ""
    schema_json = {
        "table_name": table,
        "columns": columns,
        "db": "",
        "schema": owner,
        "table_comment": table_comment or ""
    }
    cursor.close()
    conn.close()
    return schema_json