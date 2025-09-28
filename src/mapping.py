# src/mapping.py

TYPE_MAPPING = {
    "integer": "INT64",
    "int": "INT64",
    "bigint": "INT64",
    "smallint": "INT64",
    "float": "FLOAT64",
    "double": "FLOAT64",
    "numeric": "NUMERIC",
    "decimal": "NUMERIC",
    "varchar": "STRING",
    "char": "STRING",
    "text": "STRING",
    "boolean": "BOOL",
    "bool": "BOOL",
    "date": "DATE",
    "timestamp": "TIMESTAMP",
    "datetime": "TIMESTAMP",
    "json": "JSON",
    "jsonb": "JSON",
    "bytea": "BYTES",
    "blob": "BYTES",
}
