# BigQuery DDL Generator (Flask)

A simple **Flask** web application that:

* Accepts source-database details from a web form.
* Generates the equivalent **BigQuery CREATE TABLE DDL**.
* Saves the generated SQL to a downloadable `.sql` file.

This project is meant as a beginner-friendly demo and can be showcased on GitHub.

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
pip install flask google-cloud-bigquery sqlalchemy

# 3. Set the Flask app name (only needed once per terminal)
set FLASK_APP=app.py
set FLASK_ENV=development   # enables debug mode

# 4. Start the development server
flask run

Now visit http://127.0.0.1:5000/ in your browser.
```

---

## Current Progress

- **MySQL Source Support:**  
  - Users can connect to a MySQL database, browse databases and tables, and extract table schema.
  - The app can extract schema from both JSON schema and MySQL DDL.
  - Users can preview and edit the extracted schema before generating BigQuery DDL.
  - BigQuery DDL is generated using the extracted schema and user-provided project, dataset, and table name.
  - UI supports both manual schema/DDL input and interactive browsing of MySQL sources.

- **User Experience:**  
  - Clean separation between Manual and Browse Source tabs.
  - AJAX-based schema extraction and DDL generation for a smooth workflow.
  - Downloadable BigQuery DDL preview.

---

## Future Scope

- **Support for Additional Source Systems:**
  - PostgreSQL
  - SQL Server
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

*Contributions and suggestions are welcome!*
