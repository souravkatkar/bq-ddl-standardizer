# src/mapping.py

TYPE_MAPPING = {
    "INTEGER": "INT64",
    "INT": "INT64",
    "BIGINT": "INT64",
    "SMALLINT": "INT64",
    "FLOAT": "FLOAT64",
    "DOUBLE": "FLOAT64",
    "NUMERIC": "NUMERIC",
    "DECIMAL": "NUMERIC",
    "VARCHAR": "STRING",
    "CHAR": "STRING",
    "TEXT": "STRING",
    "BOOLEAN": "BOOL",
    "BOOL": "BOOL",
    "DATE": "DATE",
    "TIMESTAMP": "TIMESTAMP",
    "DATETIME": "TIMESTAMP",
    "JSON": "JSON",
    "JSONB": "JSON",
    "BYTEA": "BYTES",
    "BLOB": "BYTES",
}

def map_type_to_bigquery(src_type):
    # Compare in uppercase
    return TYPE_MAPPING.get(str(src_type).upper(), "STRING")
