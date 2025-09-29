import mysql.connector

def test_mysql_connection(host, port, user, password):
    conn = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password
    )
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    dbs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return dbs

def get_mysql_tables(host, port, user, password, database):
    conn = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables

def get_mysql_table_schema(host, port, user, password, database, table):
    conn = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE,
               COLUMN_DEFAULT, COLUMN_KEY, EXTRA, COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """, (database, table))
    columns = []
    for col in cursor.fetchall():
        columns.append({
            "name": col[0],
            "type": col[1],
            "nullable": col[3].upper() == "YES",
            "comment": col[7] or ""
        })
    cursor.execute("SHOW TABLE STATUS WHERE Name = %s", (table,))
    table_status = cursor.fetchone()
    table_comment = table_status[17] if table_status else ""
    schema = {
        "table_name": table,
        "columns": columns,
        "db": database,
        "schema": database,
        "table_comment": table_comment
    }
    cursor.close()
    conn.close()
    return schema