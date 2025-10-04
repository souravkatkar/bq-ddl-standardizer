from flask import Blueprint, request, session, flash, redirect, url_for, jsonify
import oracledb

oracle_bp = Blueprint('oracle_bp', __name__)

def get_oracle_conn():
    conn_info = session.get('oracle_conn', {})
    dsn = f"{conn_info.get('host')}:{conn_info.get('port')}/{conn_info.get('service_name')}"
    return oracledb.connect(
        user=conn_info.get('user'),
        password=conn_info.get('password'),
        dsn=dsn
    )

def test_oracle_connection(host, port, service_name, username, password):
    dsn = f"{host}:{port}/{service_name}"
    conn = oracledb.connect(user=username, password=password, dsn=dsn)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM v$database")
    db_name = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return [db_name]

@oracle_bp.route('/connect_oracle', methods=['POST'])
def connect_oracle():
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    service_name = request.form.get('service_name', '') or request.form.get('database', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    connection_success = False
    try:
        dbs = test_oracle_connection(host, port, service_name, username, password)
        flash("Oracle connection successful!", "success")
        session['oracle_connected'] = True
        session['oracle_dbs'] = dbs
        session['oracle_conn'] = {
            'host': host,
            'port': port,
            'service_name': service_name,
            'user': username,
            'password': password
        }
        connection_success = True
    except Exception as e:
        flash(f"Oracle connection failed: {e}", "danger")
    if connection_success:
        return redirect(url_for(
            'home',
            db_system="oracle",
            host=host,
            port=port,
            username=username,
            database=service_name,
            service_name=service_name,
            active_tab='browse'
        ))
    else:
        return redirect(url_for(
            'home',
            db_system="oracle",
            host=host,
            port=port,
            username=username,
            database=service_name,
            active_tab='manual'
        ))

@oracle_bp.route('/get_oracle_schemas')
def get_oracle_schemas():
    try:
        conn = get_oracle_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM all_users ORDER BY username")
        schemas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(schemas)
    except Exception as e:
        print(f"Error in get_oracle_schemas: {e}")
        return jsonify([])

@oracle_bp.route('/get_oracle_tables')
def get_oracle_tables():
    schema = request.args.get('schema', '')
    print(f"Received request for tables. Owner/Schema: {schema}")
    try:
        conn = get_oracle_conn()
        print("Oracle connection established for tables.")
        cursor = conn.cursor()
        print("Cursor created for tables.")
        query = "SELECT table_name FROM all_tables WHERE owner = :owner ORDER BY table_name"
        print(f"Executing query: {query} with owner={schema}")
        cursor.execute(query, {"owner": schema})
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Fetched {len(tables)} tables.")
        cursor.close()
        conn.close()
        print("Connection closed for tables. Returning tables.")
        return jsonify(tables)
    except Exception as e:
        print(f"Error in get_oracle_tables: {e}")
        return jsonify([])

@oracle_bp.route('/get_oracle_table_schema')
def get_oracle_table_schema():
    owner = request.args.get('schema', '')
    table = request.args.get('table', '')
    print(f"Received request for table schema. Owner: {owner}, Table: {table}")
    try:
        conn = get_oracle_conn()
        print("Oracle connection established.")
        cursor = conn.cursor()
        print("Cursor created.")
        # Get column details and comments
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
        print(f"Executing query: {query.strip()}")
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Fetched {len(rows)} columns.")
        columns = []
        for col_name, data_type, nullable, comment in rows:
            columns.append({
                "name": col_name,
                "type": data_type,
                "nullable": (nullable == "Y"),
                "comment": comment or ""
            })
        # Get table comment
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
        print("Connection closed. Returning schema.")
        return jsonify({"schema": schema_json})
    except Exception as e:
        print(f"Error in get_oracle_table_schema: {e}")
        return jsonify({"schema": {}})