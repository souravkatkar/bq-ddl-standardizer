from flask import Blueprint, request, session, flash, redirect, url_for, jsonify
from src.postgres_conn import (
    test_postgres_connection,
    get_postgres_schemas,
    get_postgres_tables,
    get_postgres_table_schema
)

postgres_bp = Blueprint('postgres_bp', __name__)

@postgres_bp.route('/connect_postgres', methods=['POST'])
def connect_postgres():
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    database = request.form.get('database', '')
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
        return redirect(url_for('home', db_system='postgresql', host=host, port=port, username=username, database=database, active_tab='browse'))
    except Exception as e:
        flash(f"PostgreSQL connection failed: {e}", "danger")
        return redirect(url_for('home', db_system='postgresql', host=host, port=port, username=username, database=database, active_tab='manual'))

@postgres_bp.route('/get_postgres_schemas', methods=['GET'])
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

@postgres_bp.route('/get_postgres_tables', methods=['GET'])
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

@postgres_bp.route('/get_postgres_schema', methods=['GET'])
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
        except Exception:
            schema_dict = {"error": "Failed to fetch schema"}
    return jsonify({"schema": schema_dict})