import json
from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, session
from src.renderer import generate_bq_ddl
from src.mysql_conn import test_mysql_connection, get_mysql_tables, get_mysql_table_schema
from src.postgres_conn import (
    test_postgres_connection,
    get_postgres_schemas,
    get_postgres_tables,
    get_postgres_table_schema
)
from src.sqlserver_conn import (
    test_sqlserver_connection,
    get_sqlserver_schemas,
    get_sqlserver_tables,
    get_sqlserver_table_schema
)

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for flash messages

import re

def extract_json_schema_from_ddl(source_ddl):
    """
    Extracts table name, database, schema, and columns from source DDL.
    Supports:
      CREATE TABLE ...
      CREATE OR REPLACE TABLE ...
      Formats: db.schema.table, schema.table, table
    Returns a dictionary with table_name, db, schema, columns, table_comment.
    """
    # Normalize whitespace and remove extra line breaks
    ddl_clean = " ".join(source_ddl.strip().split())

    # Regex to extract CREATE TABLE or CREATE OR REPLACE TABLE
    table_match = re.search(
        r'CREATE\s+(OR\s+REPLACE\s+)?TABLE\s+((?P<db>\w+)\.)?(?P<schema>\w+)\.(?P<table>\w+)|CREATE\s+(OR\s+REPLACE\s+)?TABLE\s+(?P<table2>\w+)',
        ddl_clean,
        re.IGNORECASE
    )

    db = None
    schema_name = None
    table_name = None

    if table_match:
        if table_match.group('db') and table_match.group('schema') and table_match.group('table'):
            db = table_match.group('db')
            schema_name = table_match.group('schema')
            table_name = table_match.group('table')
        elif table_match.group('schema') and table_match.group('table'):
            schema_name = table_match.group('schema')
            table_name = table_match.group('table')
        elif table_match.group('table2'):
            table_name = table_match.group('table2')
    else:
        # fallback
        match_simple = re.search(r'CREATE\s+(OR\s+REPLACE\s+)?TABLE\s+([^\s(]+)', ddl_clean, re.IGNORECASE)
        table_name = match_simple.group(2) if match_simple else "extracted_table"

    # Parse column definitions inside parentheses
    columns = []
    col_block_match = re.search(r'\((.*)\)', ddl_clean)
    if col_block_match:
        col_block = col_block_match.group(1)
        # Split by commas not inside parentheses
        col_defs = re.split(r',\s*(?![^()]*\))', col_block)
        for col_def in col_defs:
            col_def = col_def.strip()
            if not col_def:
                continue
            # Pattern: name type [NULL|NOT NULL] [COMMENT '...']
            col_match = re.match(
                r'`?(?P<name>\w+)`?\s+(?P<type>\w+(\([^)]+\))?)\s*(?P<nullable>NOT NULL|NULL)?\s*(COMMENT\s+[\'"](?P<comment>[^\'"]+)[\'"])?',
                col_def,
                re.IGNORECASE
            )
            if col_match:
                col_name = col_match.group('name')
                col_type = col_match.group('type')
                nullable = True if not col_match.group('nullable') or col_match.group('nullable').upper() != "NOT NULL" else False
                comment = col_match.group('comment') or ""
                columns.append({
                    "name": col_name,
                    "type": col_type,
                    "nullable": nullable,
                    "comment": comment
                })

    # If no columns parsed, indicate failure
    if not columns:
        msg = "Failed to parse columns"
    else:
        msg = "Columns parsed successfully"

    return {
        "table_name": table_name,
        "columns": columns,
        "db": db or "sourcedb",
        "schema": schema_name or "sourceschema",
        "table_comment": "Extracted from DDL",
        "msg": msg
    }


DEFAULT_JSON_SCHEMA = '''{
    "table_name": "employees",
    "columns": [
        {"name": "id", "type": "int", "nullable": false, "comment": "Employee ID"},
        {"name": "name", "type": "varchar", "nullable": true, "comment": "Employee Name"},
        {"name": "hire_date", "type": "date", "nullable": true, "comment": "Hire Date"}
    ],
    "db": "hrdb",
    "schema": "hr",
    "table_comment": "Employee master table"
}'''

DEFAULT_SOURCE_DDL = '''CREATE TABLE employees (
    id INT NOT NULL,
    name VARCHAR(100),
    hire_date DATE
);'''

@app.route('/', methods=['GET'])
def home():
    return render_template(
        'index.html',
        db_system=request.args.get('db_system', ''),
        host=request.args.get('host', ''),
        port=request.args.get('port', ''),
        username=request.args.get('username', ''),
        database=request.args.get('database', ''),
        mysql_connected=session.get('mysql_connected', False),
        mysql_dbs=session.get('mysql_dbs', []),
        postgresql_connected=session.get('postgresql_connected', False),
        postgresql_dbs=session.get('postgresql_dbs', []),
        sqlserver_connected=session.get('sqlserver_connected', False),
        sqlserver_dbs=session.get('sqlserver_dbs', []),
        active_tab=request.args.get('active_tab', 'manual'),
        json_schema_text=request.args.get('json_schema_text', DEFAULT_JSON_SCHEMA),
        source_ddl_text=request.args.get('source_ddl_text', DEFAULT_SOURCE_DDL),
        bq_table_name=request.args.get('bq_table_name', '')
    )

@app.route('/generate', methods=['POST'])
def generate():
    json_schema_text = request.form.get('json_schema', '').strip()
    source_ddl_text = request.form.get('source_ddl', '').strip()
    bq_project_id = request.form.get('bq_project_id', '')
    bq_dataset_id = request.form.get('bq_dataset_id', '')
    bq_table_name = request.form.get('bq_table_name', '')
    ddl = None

    # If JSON schema is provided, use it
    if json_schema_text:
        try:
            schema = json.loads(json_schema_text)
            columns = schema.get('columns', [])
            table_comment = schema.get('table_comment', '')
            table_name = bq_table_name or schema.get('table_name', '')
            dataset = f"{bq_project_id}.{bq_dataset_id}" if bq_project_id and bq_dataset_id else bq_dataset_id
            ddl = generate_bq_ddl(table_name, columns, dataset, table_comment)
        except Exception as e:
            ddl = f"-- Error: {e}"
    # If only source DDL is provided, extract schema and show it, but do not generate DDL yet
    elif source_ddl_text:
        try:
            schema = extract_json_schema_from_ddl(source_ddl_text)
            json_schema_text = json.dumps(schema, indent=4)
            # Do not generate DDL yet, just show the extracted schema
        except Exception as e:
            json_schema_text = f"-- Error extracting schema: {e}"

    return render_template(
        'index.html',
        ddl=ddl,
        filename="bigquery_ddl.sql",
        json_schema_text=json_schema_text,
        bq_table_name=bq_table_name,
        source_ddl_text=source_ddl_text,
        db_system=request.form.get('db_system', ''),
        host=request.form.get('host', ''),
        port=request.form.get('port', ''),
        username=request.form.get('username', ''),
        database=request.form.get('database', ''),
        mysql_connected=session.get('mysql_connected', False),
        mysql_dbs=session.get('mysql_dbs', []),
        active_tab='manual'
    )

@app.route('/connect', methods=['POST'])
def connect():
    db_system = request.form.get('db_system', '')
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    database = request.form.get('database', '')

    # Disconnect all source systems before connecting a new one
    session.pop('mysql_connected', None)
    session.pop('mysql_dbs', None)
    session.pop('mysql_conn', None)
    session.pop('postgresql_connected', None)
    session.pop('postgresql_dbs', None)
    session.pop('postgresql_conn', None)
    session.pop('sqlserver_connected', None)
    session.pop('sqlserver_dbs', None)
    session.pop('sqlserver_conn', None)

    connection_success = False

    if db_system == "mysql":
        try:
            dbs = test_mysql_connection(host, port, username, password)
            flash("MySQL connection successful!", "success")
            session['mysql_connected'] = True
            session['mysql_dbs'] = dbs
            session['mysql_conn'] = {
                'host': host,
                'port': port,
                'user': username,
                'password': password
            }
            connection_success = True
        except Exception as e:
            flash(f"MySQL connection failed: {e}", "danger")
    elif db_system == "postgresql":
        try:
            dbs = test_postgres_connection(host, port, username, password)
            flash("PostgreSQL connection successful!", "success")
            session['postgresql_connected'] = True
            session['postgresql_dbs'] = dbs
            session['postgresql_conn'] = {
                'host': host,
                'port': port,
                'user': username,
                'password': password
            }
            connection_success = True
        except Exception as e:
            flash(f"PostgreSQL connection failed: {e}", "danger")
    elif db_system == "sqlserver":
        try:
            dbs = test_sqlserver_connection(host, port, username, password)
            flash("SQL Server connection successful!", "success")
            session['sqlserver_connected'] = True
            session['sqlserver_dbs'] = dbs
            session['sqlserver_conn'] = {
                'host': host,
                'port': port,
                'user': username,
                'password': password
            }
            connection_success = True
        except Exception as e:
            flash(f"SQL Server connection failed: {e}", "danger")

    # Redirect to Manual tab on failure, Browse tab on success
    if connection_success:
        return redirect(url_for(
            'home',
            db_system=db_system,
            host=host,
            port=port,
            username=username,
            database=database,
            active_tab='browse'
        ))
    else:
        # Pass all fields except password
        return redirect(url_for(
            'home',
            db_system=db_system,
            host=host,
            port=port,
            username=username,
            database=database,
            active_tab='manual'
        ))

# --- PostgreSQL AJAX endpoints ---

@app.route('/get_postgres_schemas', methods=['GET'])
def get_postgres_schemas_route():
    print("Fetching PostgreSQL schemas...")
    database = request.args.get('database', '')
    print(f"Requested database: {database}")
    conn_details = session.get('postgresql_conn')
    print(f"PostgreSQL connection details from session: {conn_details}")
    schemas = []
    if conn_details and database:
        try:
            schemas = get_postgres_schemas(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database
            )
            print(f"Schemas found: {schemas}")
        except Exception as e:
            print(f"Error fetching PostgreSQL schemas: {e}")
            schemas = []
    return jsonify(schemas)

@app.route('/get_postgres_tables', methods=['GET'])
def get_postgres_tables_route():
    print("Fetching PostgreSQL tables...")
    database = request.args.get('database', '')
    schema = request.args.get('schema', '')
    print(f"Database: {database}, Schema: {schema}")
    conn_details = session.get('postgresql_conn')
    print(f"PostgreSQL connection details from session: {conn_details}")
    tables = []
    if conn_details and database and schema:
        try:
            tables = get_postgres_tables(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database,
                schema
            )
            print(f"Tables found: {tables}")
        except Exception as e:
            print(f"Error fetching PostgreSQL tables: {e}")
            tables = []
    return jsonify(tables)

@app.route('/get_postgres_schema')
def get_postgres_schema_route():
    print("Fetching PostgreSQL table schema...")
    database = request.args.get('database')
    schema = request.args.get('schema')
    table = request.args.get('table')
    print(f"Database: {database}, Schema: {schema}, Table: {table}")
    conn_details = session.get('postgresql_conn')
    print(f"PostgreSQL connection details from session: {conn_details}")
    schema_dict = {}
    if conn_details and database and schema and table:
        try:
            schema_dict = get_postgres_table_schema(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database,
                schema,
                table
            )
            print(f"Schema found: {schema_dict}")
        except Exception as e:
            print(f"Error fetching PostgreSQL schema: {e}")
            schema_dict = {"error": str(e)}
    return jsonify({"schema": schema_dict})

@app.route('/generate_bq_ddl_from_schema', methods=['POST'])
def generate_bq_ddl_from_schema():
    data = request.get_json()
    schema = json.loads(data.get('schema'))
    bq_project_id = data.get('bq_project_id')
    bq_dataset_id = data.get('bq_dataset_id')
    bq_table_name = data.get('bq_table_name') or schema.get('table_name', 'my_table')
    dataset = f"{bq_project_id}.{bq_dataset_id}" if bq_project_id and bq_dataset_id else bq_dataset_id or schema.get("schema")
    ddl = generate_bq_ddl(bq_table_name, schema.get('columns', []), dataset, schema.get('table_comment'))
    return jsonify({"ddl": ddl})

@app.route('/get_schemas')
def get_schemas():
    db_system = request.args.get('db_system')
    database = request.args.get('database')
    schemas = []
    if db_system == "postgresql":
        from src.postgres_conn import get_postgres_schemas
        conn_details = session.get('postgresql_conn')
        if conn_details and database:
            try:
                schemas = get_postgres_schemas(
                    conn_details['host'],
                    conn_details['port'],
                    conn_details['user'],
                    conn_details['password'],
                    database
                )
            except Exception as e:
                print("Error fetching schemas:", e)
    # ...handle mysql if needed...
    return jsonify({"schemas": schemas})

@app.route('/get_mysql_tables', methods=['GET'])
def get_mysql_tables_route():
    print("Fetching MySQL tables...")
    database = request.args.get('database', '')
    print(f"Requested database: {database}")
    conn_details = session.get('mysql_conn')
    print(f"MySQL connection details from session: {conn_details}")
    tables = []
    if conn_details and database:
        try:
            tables = get_mysql_tables(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database
            )
            print(f"Tables found: {tables}")
        except Exception as e:
            print(f"Error fetching MySQL tables: {e}")
            tables = []
    return jsonify(tables)

@app.route('/get_mysql_schema')
def get_mysql_schema_route():
    print("Fetching MySQL table schema...")
    database = request.args.get('database')
    table = request.args.get('table')
    print(f"Database: {database}, Table: {table}")
    conn_details = session.get('mysql_conn')
    print(f"MySQL connection details from session: {conn_details}")
    schema = {}
    if conn_details and database and table:
        try:
            schema = get_mysql_table_schema(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database,
                table
            )
            print(f"Schema found: {schema}")
        except Exception as e:
            print(f"Error fetching MySQL schema: {e}")
            schema = {"error": str(e)}
    return jsonify({"schema": schema})

@app.route('/get_sqlserver_schemas', methods=['GET'])
def get_sqlserver_schemas_route():
    print("Fetching SQL Server schemas...")
    database = request.args.get('database', '')
    print(f"Requested database: {database}")
    conn_details = session.get('sqlserver_conn')
    print(f"SQL Server connection details from session: {conn_details}")
    schemas = []
    if conn_details and database:
        try:
            schemas = get_sqlserver_schemas(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database
            )
            print(f"Schemas found: {schemas}")
        except Exception as e:
            print(f"Error fetching SQL Server schemas: {e}")
            schemas = []
    return jsonify(schemas)

@app.route('/get_sqlserver_tables', methods=['GET'])
def get_sqlserver_tables_route():
    print("Fetching SQL Server tables...")
    database = request.args.get('database', '')
    schema = request.args.get('schema', '')
    print(f"Database: {database}, Schema: {schema}")
    conn_details = session.get('sqlserver_conn')
    print(f"SQL Server connection details from session: {conn_details}")
    tables = []
    if conn_details and database and schema:
        try:
            tables = get_sqlserver_tables(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database,
                schema
            )
            print(f"Tables found: {tables}")
        except Exception as e:
            print(f"Error fetching SQL Server tables: {e}")
            tables = []
    return jsonify(tables)

@app.route('/get_sqlserver_schema')
def get_sqlserver_schema_route():
    print("Fetching SQL Server table schema...")
    database = request.args.get('database')
    schema = request.args.get('schema')
    table = request.args.get('table')
    print(f"Database: {database}, Schema: {schema}, Table: {table}")
    conn_details = session.get('sqlserver_conn')
    print(f"SQL Server connection details from session: {conn_details}")
    schema_dict = {}
    if conn_details and database and schema and table:
        try:
            schema_dict = get_sqlserver_table_schema(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database,
                schema,
                table
            )
            print(f"Schema found: {schema_dict}")
        except Exception as e:
            print(f"Error fetching SQL Server schema: {e}")
            schema_dict = {"error": str(e)}
    return jsonify({"schema": schema_dict})

@app.route('/clear_connection', methods=['POST'])
def clear_connection():
    print("Clearing all source connections from session.")
    session.pop('mysql_connected', None)
    session.pop('mysql_dbs', None)
    session.pop('mysql_conn', None)
    session.pop('postgresql_connected', None)
    session.pop('postgresql_dbs', None)
    session.pop('postgresql_conn', None)
    session.pop('sqlserver_connected', None)
    session.pop('sqlserver_dbs', None)
    session.pop('sqlserver_conn', None)
    return ('', 204)

if __name__ == '__main__':
    app.run(debug=True)