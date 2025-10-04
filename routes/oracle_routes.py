from flask import Blueprint, request, session, flash, redirect, url_for, jsonify
from src.oracle_conn import (
    test_oracle_connection,
    get_oracle_schemas,
    get_oracle_tables,
    get_oracle_table_schema
)

oracle_bp = Blueprint('oracle_bp', __name__)

@oracle_bp.route('/connect_oracle', methods=['POST'])
def connect_oracle():
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    service_name = request.form.get('service_name', '') or request.form.get('database', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    connection_success = False
    try:
        dbs = test_oracle_connection(host, port, username, password, service_name)
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
def get_oracle_schemas_route():
    conn_info = session.get('oracle_conn', {})
    schemas = []
    try:
        schemas = get_oracle_schemas(
            conn_info.get('host'),
            conn_info.get('port'),
            conn_info.get('user'),
            conn_info.get('password'),
            conn_info.get('service_name')
        )
    except Exception as e:
        print(f"Error in get_oracle_schemas: {e}")
        schemas = []
    return jsonify(schemas)

@oracle_bp.route('/get_oracle_tables')
def get_oracle_tables_route():
    owner = request.args.get('schema', '')
    conn_info = session.get('oracle_conn', {})
    tables = []
    try:
        tables = get_oracle_tables(
            conn_info.get('host'),
            conn_info.get('port'),
            conn_info.get('user'),
            conn_info.get('password'),
            conn_info.get('service_name'),
            owner
        )
    except Exception as e:
        print(f"Error in get_oracle_tables: {e}")
        tables = []
    return jsonify(tables)

@oracle_bp.route('/get_oracle_table_schema')
def get_oracle_table_schema_route():
    owner = request.args.get('schema', '')
    table = request.args.get('table', '')
    conn_info = session.get('oracle_conn', {})
    schema_json = {}
    try:
        schema_json = get_oracle_table_schema(
            conn_info.get('host'),
            conn_info.get('port'),
            conn_info.get('user'),
            conn_info.get('password'),
            conn_info.get('service_name'),
            owner,
            table
        )
    except Exception as e:
        print(f"Error in get_oracle_table_schema: {e}")
        schema_json = {}
    return jsonify({"schema": schema_json})