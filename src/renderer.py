# src/renderer.py

from src.mapping import map_type_to_bigquery

def generate_bq_ddl(table_name, columns, dataset, table_comment=None):
    """
    Generates BigQuery CREATE TABLE DDL.
    """
    # Apply type mapping to all columns
    for col in columns:
        original_type = col.get("type", "")
        col["type"] = map_type_to_bigquery(original_type)

    # Add backticks to table name
    full_table_name = f"`{dataset}.{table_name}`" if dataset else f"`{table_name}`"
    ddl_lines = [f"CREATE OR REPLACE TABLE {full_table_name} ("]
    for col in columns:
        col_line = f"  {col['name']} {col['type']}"
        if not col.get('nullable', True):
            col_line += " NOT NULL"
        if col.get('comment'):
            col_line += f" OPTIONS(description=\"{col['comment']}\")"
        ddl_lines.append(col_line + ",")
    # Remove last comma
    if len(ddl_lines) > 1:
        ddl_lines[-1] = ddl_lines[-1].rstrip(",")
    ddl_lines.append(")")
    if table_comment:
        ddl_lines.append(f"OPTIONS(description=\"{table_comment}\");")
    else:
        ddl_lines.append(";")
    return "\n".join(ddl_lines)
