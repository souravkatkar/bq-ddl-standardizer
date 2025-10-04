from flask import Blueprint, request, session, flash, redirect, url_for, jsonify
from src.sqlserver_conn import (
    test_sqlserver_connection,
    get_sqlserver_schemas,
    get_sqlserver_tables,
    get_sqlserver_table_schema
)

sqlserver_bp = Blueprint('sqlserver_bp', __name__)

@sqlserver_bp.route('/connect_sqlserver', methods=['POST'])
def connect_sqlserver():
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    database = request.form.get('database', '')
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
        return redirect(url_for('home', db_system='sqlserver', host=host, port=port, username=username, database=database, active_tab='browse'))
    except Exception as e:
        flash(f"SQL Server connection failed: {e}", "danger")
        return redirect(url_for('home', db_system='sqlserver', host=host, port=port, username=username, database=database, active_tab='manual'))

@sqlserver_bp.route('/get_sqlserver_schemas', methods=['GET'])
def get_sqlserver_schemas_route():
    database = request.args.get('database', '')
    conn_details = session.get('sqlserver_conn')
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
        except Exception:
            schemas = []
    return jsonify(schemas)

@sqlserver_bp.route('/get_sqlserver_tables', methods=['GET'])
def get_sqlserver_tables_route():
    database = request.args.get('database', '')
    schema = request.args.get('schema', '')
    conn_details = session.get('sqlserver_conn')
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
        except Exception:
            tables = []
    return jsonify(tables)

@sqlserver_bp.route('/get_sqlserver_schema', methods=['GET'])
def get_sqlserver_schema_route():
    database = request.args.get('database')
    schema = request.args.get('schema')
    table = request.args.get('table')
    conn_details = session.get('sqlserver_conn')
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
        except Exception:
            schema_dict = {"error": "Failed to fetch schema"}
    return jsonify({"schema": schema_dict})