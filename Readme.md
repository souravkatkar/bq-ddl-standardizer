# BigQuery DDL Generator (Flask)

A simple **Flask** web application that:

* Accepts source-database details from a web form.
* Allows browsing of MySQL, PostgreSQL, SQL Server, and Oracle databases, schemas, and tables.
* Extracts table schema from MySQL, PostgreSQL, SQL Server, and Oracle sources.
* **Extracts column and table comments for all supported databases.**
* **Integrates AI (GPT4All) to automatically generate meaningful comments for columns and tables.**
* **Maps source column types to BigQuery types before DDL generation.**
* Generates the equivalent **BigQuery CREATE OR REPLACE TABLE DDL** (with backticks and comments).
* Saves the generated SQL to a downloadable `.sql` file (always the latest version with comments).
* Themed loading UI shows when AI is processing in the background.

---

## Prerequisites

* **Python 3.9+** installed
* **Git** installed

---

## Setup & Run (Development)

Open a terminal **inside the project folder** and run these commands step by step:

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # (Windows PowerShell)

# 2. Install dependencies
pip install flask google-cloud-bigquery sqlalchemy mysql-connector-python psycopg2 pyodbc oracledb gpt4all

# 3. Set the Flask app name (only needed once per terminal)
set FLASK_APP=app.py
set FLASK_ENV=development   # enables debug mode

# 4. Start the development server
flask run

# Now visit http://127.0.0.1:5000/ in your browser.
```

---

## Project Structure

```
bq-ddl-standardizer/
│
├── app.py
├── models/
│   ├── Phi-3-mini-4k-instruct-q4.gguf
│   ├── <other-models>.gguf
│   └── ... (add your GPT4All .gguf model files here)
├── src/
│   ├── mysql_conn.py
│   ├── postgres_conn.py
│   ├── sqlserver_conn.py
│   ├── oracle_conn.py
│   ├── renderer.py
│   ├── mapping.py
│   ├── ai_utils.py
│   └── __init__.py
├── routes/
│   ├── mysql_routes.py
│   ├── postgres_routes.py
│   ├── sqlserver_routes.py
│   ├── oracle_routes.py
│   ├── ai_util_routes.py
│   └── __pycache__/
├── static/
│   └── js/
│       ├── app.js
│       └── ai_util.js
├── templates/
│   └── index.html
├── Readme.md
```
- **models/**: Directory for GPT4All model files (`*.gguf`).  
  Add your downloaded models here (e.g., `Phi-3-mini-4k-instruct-q4.gguf`).

---

## Features

- **Source System Support:**  
  - Connect to MySQL, PostgreSQL, SQL Server, or Oracle (one at a time).
  - Browse databases, schemas, and tables.
  - Extract schema from JSON or source DDL.

- **Schema Extraction:**  
  - Extracts column and table comments for all supported databases (MySQL, PostgreSQL, SQL Server, Oracle).
  - **AI-powered comment generation for columns and tables using GPT4All.**

- **Type Mapping:**  
  - Source column types are mapped to BigQuery types before DDL generation (case-insensitive).

- **BigQuery DDL Generation:**  
  - Preview and edit extracted schema.
  - Generate BigQuery DDL using extracted schema and user-provided project, dataset, and table name.
  - DDL uses `CREATE OR REPLACE TABLE \`project.dataset.table\`` syntax with comments in `OPTIONS(description="...")`.
  - Downloadable BigQuery DDL preview (always the latest version with comments).

- **User Experience:**  
  - Manual and Browse Source tabs.
  - AJAX-based schema extraction and DDL generation.
  - Only one source system connection is active at a time.
  - "Clear" button resets source connection and UI.
  - Modularized codebase with separate route files for each database system.
  - **All JavaScript code is now refactored into `static/js/app.js` and `static/js/ai_util.js` for maintainability and a cleaner HTML template.**
  - Toast notifications for alerts and feedback, positioned at the top-right for improved UX.
  - **Themed loading UI overlay appears when AI is processing in the background.**

- **Accessibility:**  
  - ARIA labels for form controls.
  - Responsive Bootstrap UI.

---

## AI Integration

- Toggle "Use AI" in the sidebar to enable AI-powered comment generation.
- Select a model from the `models` directory.
- When "Add Comments to DDL" is clicked, each column and the table name are sent to GPT4All for comment generation.
- Comments are cleaned and inserted into the schema.
- Type mapping is applied before DDL generation.
- The latest DDL (with comments) is previewed and available for download.

---

## Future Scope

- **Support for Additional Source Systems:**
  - Snowflake
  - Other popular RDBMS and cloud data warehouses

- **Enhanced Schema Extraction:**
  - Improved DDL parsing for more complex source DDLs.
  - Support for extracting constraints, indexes, and relationships.

- **BigQuery Features:**
  - Support for partitioned and clustered tables.
  - Advanced type mapping and custom transformations.

- **User Experience:**
  - Save and manage connection profiles.
  - Schema comparison and migration suggestions.
  - API endpoints for automation and integration.

---

## Contributing

Contributions and suggestions are welcome!  
Feel free to open issues or submit pull requests.

---

## License

MIT License
