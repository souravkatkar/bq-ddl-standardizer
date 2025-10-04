from flask import Blueprint, request, session, flash, redirect, url_for, jsonify
from src.mysql_conn import test_mysql_connection, get_mysql_tables, get_mysql_table_schema

mysql_bp = Blueprint('mysql_bp', __name__)

@mysql_bp.route('/connect_mysql', methods=['POST'])
def connect_mysql():
    host = request.form.get('host', '')
    port = request.form.get('port', '')
    username = request.form.get('username', '')
    password = request.form.get('password', '')
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
        return redirect(url_for('home', db_system='mysql', host=host, port=port, username=username, active_tab='browse'))
    except Exception as e:
        flash(f"MySQL connection failed: {e}", "danger")
        return redirect(url_for('home', db_system='mysql', host=host, port=port, username=username, active_tab='manual'))

@mysql_bp.route('/get_mysql_tables', methods=['GET'])
def get_mysql_tables_route():
    database = request.args.get('database', '')
    conn_details = session.get('mysql_conn')
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
        except Exception:
            tables = []
    return jsonify(tables)

@mysql_bp.route('/get_mysql_schema', methods=['GET'])
def get_mysql_schema_route():
    database = request.args.get('database', '')
    table = request.args.get('table', '')
    conn_details = session.get('mysql_conn')
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
        except Exception:
            schema = {}
    return jsonify({"schema": schema})