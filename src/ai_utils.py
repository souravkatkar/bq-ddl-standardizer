import json
import re
from gpt4all import GPT4All

def clean_ai_comment(raw_comment: str) -> str:
    print("Cleaning AI comment...")
    patterns_to_remove = [
        r"Description[:\-]*",
        r"Solution[:\d]*",
        r"- answer:",
        r"answer: ",
        r"- Tutor:",
        r"Output[:\-]*",
        r"\*\*response:\*\*",
        r"- response[:\-]*",
        r"<\|end\|>",
        r"<\|assistant\|>",
        r"\*{2,}",
        r"\[response\]:",
        r"###.*",
        r"---",
        r"^\s*\"|\s*\"$",
        r"^\s*'|\s*'$",
    ]
    cleaned = raw_comment
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    # Remove all double quotes
    cleaned = cleaned.replace('"', "")
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        print("No valid lines found after cleaning.")
        return ""
    result = max(lines, key=len)
    print(f"Cleaned comment: {result}")
    return result

def get_column_comment(model, col_name, col_type):
    print(f"Preparing prompt for column: {col_name}, type: {col_type}")
    prompt = f"""
    You are a database expert.
    Write a single-line, human-readable description for the column below.
    - Output ONLY the description.
    - Do NOT add 'Solution:', 'Output:', 'Response:', examples, JSON, markdown, assistant, end, explanation or any commentary.
    - Keep it concise, one line.

    Column: {col_name}
    Type: {col_type}
    """
    print("Sending prompt to AI model...")
    response = model.generate(prompt, max_tokens=64).strip()
    print(f"Raw AI response for '{col_name}': {response}")
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    if response.startswith("'") and response.endswith("'"):
        response = response[1:-1]
    cleaned_comment = clean_ai_comment(response)
    print(f"Final cleaned comment for '{col_name}': {cleaned_comment}")
    return cleaned_comment

def get_table_comment(model, table_name):
    prompt = f"""
Table: {table_name}
Task: Write a short, meaningful comment describing this table for a database schema.
Return ONLY the comment as a string.
"""
    print(f"Prompting for table comment for '{table_name}'...")
    response = model.generate(prompt, max_tokens=64).strip()
    return clean_ai_comment(response)

def add_comments_to_json_schema(json_schema, model_name):
    try:
        print("Starting add_comments_to_json_schema function.")
        model_path = "models/"
        model = GPT4All(model_name, model_path=model_path)
        print("Model initialized.")
        schema_obj = json.loads(json_schema)
        print("Loaded JSON schema.")
        columns = schema_obj.get("columns", [])
        print(f"Found {len(columns)} columns to process.")
        for idx, col in enumerate(columns):
            print(f"Processing column {idx+1}/{len(columns)}: {col.get('name')}")
            col_name = col.get("name")
            col_type = col.get("type")
            comment = get_column_comment(model, col_name, col_type)
            col["comment"] = comment
            print(f"Comment added for column '{col_name}'.")
        # Generate table comment using table name
        table_name = schema_obj.get("table_name", "")
        table_comment = get_table_comment(model, table_name)
        schema_obj["table_comment"] = table_comment
        print("Table comment generated.")
        print("All column comments generated.")
        return schema_obj
    except Exception as e:
        print(f"Error in add_comments_to_json_schema: {e}")
        return None

def add_comments_to_ddl(ddl, model_name):
    response_text = ""
    try:
        model_path = "models/"
        model = GPT4All(model_name, model_path=model_path)
        prompt = (
            """Add helpful comments to each column and the table in this BigQuery DDL using 
            "OPTIONS(description=\"...\") for both columns and the table. 
            Return only the modified DDL.\n"""
            f"{ddl}"
        )
        response_text = model.generate(prompt, max_tokens=256)
        print("AI Response:", response_text)
    except Exception as e:
        response_text = f"Error: {e}"
        print(response_text)
    return response_text

