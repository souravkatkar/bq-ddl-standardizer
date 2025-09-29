from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, session
import json
from src.renderer import generate_bq_ddl
from src.mysql_conn import test_mysql_connection, get_mysql_tables, get_mysql_table_schema
from src.postgres_conn import (
    test_postgres_connection,
    get_postgres_schemas,
    get_postgres_tables,
    get_postgres_table_schema
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
    db_system = request.args.get('db_system', '')
    host = request.args.get('host', '')
    port = request.args.get('port', '')
    username = request.args.get('username', '')
    database = request.args.get('database', '')
    mysql_connected = session.get('mysql_connected', False)
    mysql_dbs = session.get('mysql_dbs', [])
    postgresql_connected = session.get('postgresql_connected', False)
    postgresql_dbs = session.get('postgresql_dbs', [])
    active_tab = request.args.get('active_tab', 'manual')
    return render_template(
        'index.html',
        ddl=None,
        filename=None,
        json_schema_text=DEFAULT_JSON_SCHEMA,
        bq_table_name="employees",
        source_ddl_text=DEFAULT_SOURCE_DDL,
        db_system=db_system,
        host=host,
        port=port,
        username=username,
        database=database,
        mysql_connected=mysql_connected,
        mysql_dbs=mysql_dbs,
        postgresql_connected=postgresql_connected,
        postgresql_dbs=postgresql_dbs,
        active_tab=active_tab
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

    if db_system == "mysql":
        try:
            from src.mysql_conn import test_mysql_connection
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
        except Exception as e:
            flash(f"MySQL connection failed: {e}", "danger")
    elif db_system == "postgresql":
        try:
            from src.postgres_conn import test_postgres_connection
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
        except Exception as e:
            flash(f"PostgreSQL connection failed: {e}", "danger")
    else:
        flash("Only MySQL and PostgreSQL connections are implemented in this demo.", "warning")

    return redirect(url_for(
        'home',
        db_system=db_system,
        host=host,
        port=port,
        username=username,
        database=database,
        active_tab='browse'
    ))

# --- PostgreSQL AJAX endpoints ---

@app.route('/get_postgres_schemas', methods=['GET'])
def get_postgres_schemas_route():
    database = request.args.get('database', '')
    conn_details = session.get('postgresql_conn')
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
        except Exception:
            schemas = []
    return jsonify(schemas)

@app.route('/get_postgres_tables', methods=['GET'])
def get_postgres_tables_route():
    database = request.args.get('database', '')
    schema = request.args.get('schema', '')
    conn_details = session.get('postgresql_conn')
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
        except Exception:
            tables = []
    return jsonify(tables)

@app.route('/get_postgres_schema')
def get_postgres_schema_route():
    database = request.args.get('database')
    schema = request.args.get('schema')
    table = request.args.get('table')
    conn_details = session.get('postgresql_conn')
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
        except Exception as e:
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
    database = request.args.get('database', '')
    conn_details = session.get('mysql_conn')
    tables = []
    if conn_details and database:
        try:
            from src.mysql_conn import get_mysql_tables
            tables = get_mysql_tables(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database
            )
        except Exception:
            tables = []
    return jsonify(tables)

@app.route('/get_mysql_schema')
def get_mysql_schema_route():
    database = request.args.get('database')
    table = request.args.get('table')
    conn_details = session.get('mysql_conn')
    schema = {}
    if conn_details and database and table:
        try:
            from src.mysql_conn import get_mysql_table_schema
            schema = get_mysql_table_schema(
                conn_details['host'],
                conn_details['port'],
                conn_details['user'],
                conn_details['password'],
                database,
                table
            )
        except Exception as e:
            schema = {"error": str(e)}
    return jsonify({"schema": schema})

if __name__ == '__main__':
    app.run(debug=True)