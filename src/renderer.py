# src/renderer.py

from .mapping import TYPE_MAPPING

def generate_bq_ddl(table_name, columns, dataset=None, table_comment=None):
    """
    Generate BigQuery CREATE TABLE DDL from JSON schema.
    
    Args:
        table_name (str): Name of the table.
        columns (list): List of columns as dictionaries:
                        [{"name":..., "type":..., "nullable":..., "comment":...}, ...]
        dataset (str, optional): Dataset prefix.
        table_comment (str, optional): Table-level comment.
    Returns:
        str: BigQuery CREATE TABLE statement.
    """
    dataset_prefix = f"{dataset}." if dataset else ""
    ddl_lines = [f"CREATE TABLE {dataset_prefix}{table_name} ("]
    
    col_lines = []
    for col in columns:
        name = col['name'].lower()
        src_type = col['type'].lower()
        bq_type = TYPE_MAPPING.get(src_type.split("(")[0], "STRING")
        nullable = "" if col.get("nullable", True) else "NOT NULL"
        comment = f'OPTIONS(description="{col["comment"]}")' if col.get("comment") else ""
        col_lines.append(f"  {name} {bq_type} {nullable} {comment}".strip())
    
    ddl_lines.append(",\n".join(col_lines))
    ddl_lines.append(")")
    
    if table_comment:
        ddl_lines[-1] += f' OPTIONS(description="{table_comment}");'
    else:
        ddl_lines[-1] += ";"
    
    return "\n".join(ddl_lines)
