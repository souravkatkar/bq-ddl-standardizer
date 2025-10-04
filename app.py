import json
from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, session
from src.renderer import generate_bq_ddl
from routes.mysql_routes import mysql_bp
from routes.postgres_routes import postgres_bp
from routes.sqlserver_routes import sqlserver_bp

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
app.register_blueprint(mysql_bp)
app.register_blueprint(postgres_bp)
app.register_blueprint(sqlserver_bp)

import re

def debug_log(message):
    print(f"[DEBUG] {message}")

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
    debug_log("GET / route called")
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
    debug_log("POST /generate route called")
    json_schema_text = request.form.get('json_schema', '').strip()
    source_ddl_text = request.form.get('source_ddl', '').strip()
    bq_project_id = request.form.get('bq_project_id', '')
    bq_dataset_id = request.form.get('bq_dataset_id', '')
    bq_table_name = request.form.get('bq_table_name', '')
    ddl = None

    debug_log(f"Received form data: json_schema_text={bool(json_schema_text)}, source_ddl_text={bool(source_ddl_text)}")

    # If JSON schema is provided, use it
    if json_schema_text:
        try:
            schema = json.loads(json_schema_text)
            columns = schema.get('columns', [])
            table_comment = schema.get('table_comment', '')
            table_name = bq_table_name or schema.get('table_name', '')
            dataset = f"{bq_project_id}.{bq_dataset_id}" if bq_project_id and bq_dataset_id else bq_dataset_id
            debug_log(f"Calling generate_bq_ddl with table_name={table_name}, columns={columns}, dataset={dataset}")
            ddl = generate_bq_ddl(table_name, columns, dataset, table_comment)
        except Exception as e:
            debug_log(f"Error in generate_bq_ddl: {e}")
            ddl = f"-- Error: {e}"
    # If only source DDL is provided, extract schema and show it, but do not generate DDL yet
    elif source_ddl_text:
        try:
            debug_log("Extracting JSON schema from source DDL")
            schema = extract_json_schema_from_ddl(source_ddl_text)
            json_schema_text = json.dumps(schema, indent=4)
        except Exception as e:
            debug_log(f"Error extracting schema from DDL: {e}")
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
    debug_log("POST /connect route called")
    db_system = request.form.get('db_system', '')
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    database = request.form.get('database', '')

    debug_log(f"Trying to connect to {db_system} with host={host}, port={port}, username={username}")

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

    # Only handle SQL Server here; MySQL and PostgreSQL are handled in their blueprints
    connection_success = False

    if db_system == "sqlserver":
        try:
            from src.sqlserver_conn import test_sqlserver_connection
            dbs = test_sqlserver_connection(host, port, username, password)
            debug_log("SQL Server connection successful")
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
            debug_log(f"SQL Server connection failed: {e}")
            flash(f"SQL Server connection failed: {e}", "danger")

    if connection_success:
        debug_log("Redirecting to browse tab after successful connection")
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
        debug_log("Redirecting to manual tab after failed connection")
        return redirect(url_for(
            'home',
            db_system=db_system,
            host=host,
            port=port,
            username=username,
            database=database,
            active_tab='manual'
        ))

@app.route('/clear_connection', methods=['POST'])
def clear_connection():
    debug_log("POST /clear_connection route called")
    session.pop('mysql_connected', None)
    session.pop('mysql_dbs', None)
    session.pop('mysql_conn', None)
    session.pop('postgresql_connected', None)
    session.pop('postgresql_dbs', None)
    session.pop('postgresql_conn', None)
    session.pop('sqlserver_connected', None)
    session.pop('sqlserver_dbs', None)
    session.pop('sqlserver_conn', None)
    debug_log("Cleared all connection sessions")
    return ('', 204)

@app.route('/generate_bq_ddl', methods=['POST'])
def generate_bq_ddl_route():
    debug_log("POST /generate_bq_ddl route called")
    data = request.get_json()
    schema = json.loads(data.get('schema'))
    bq_project_id = data.get('bq_project_id')
    bq_dataset_id = data.get('bq_dataset_id')
    bq_table_name = data.get('bq_table_name') or schema.get('table_name', 'my_table')
    dataset = f"{bq_project_id}.{bq_dataset_id}" if bq_project_id and bq_dataset_id else bq_dataset_id or schema.get("schema")
    ddl = generate_bq_ddl(bq_table_name, schema.get('columns', []), dataset, schema.get('table_comment'))
    return jsonify({"ddl": ddl})

if __name__ == '__main__':
    debug_log("Starting Flask app")
    app.run(debug=True)