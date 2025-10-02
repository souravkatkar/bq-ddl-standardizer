# BigQuery DDL Generator (Flask)

A simple **Flask** web application that:

* Accepts source-database details from a web form.
* Allows browsing of MySQL, PostgreSQL, and SQL Server databases, schemas, and tables.
* Extracts table schema from MySQL, PostgreSQL, and SQL Server sources.
* Generates the equivalent **BigQuery CREATE TABLE DDL**.
* Saves the generated SQL to a downloadable `.sql` file.

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
pip install flask google-cloud-bigquery sqlalchemy mysql-connector-python psycopg2 pyodbc

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
├── src/
│   ├── mysql_conn.py
│   ├── postgres_conn.py
│   ├── sqlserver_conn.py
│   ├── renderer.py
│   ├── mapping.py
│   └── __init__.py
├── templates/
│   └── index.html
├── Readme.md
```

---

## Features

- **Source System Support:**  
  - Connect to MySQL, PostgreSQL, or SQL Server (one at a time).
  - Browse databases, schemas, and tables.
  - Extract schema from JSON or source DDL.

- **BigQuery DDL Generation:**  
  - Preview and edit extracted schema.
  - Generate BigQuery DDL using extracted schema and user-provided project, dataset, and table name.
  - Downloadable BigQuery DDL preview.

- **User Experience:**  
  - Manual and Browse Source tabs.
  - AJAX-based schema extraction and DDL generation.
  - Only one source system connection is active at a time.
  - "Clear" button resets source connection and UI.

- **Accessibility:**  
  - ARIA labels for form controls.
  - Responsive Bootstrap UI.

---

## Future Scope

- **Support for Additional Source Systems:**
  - Oracle
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
