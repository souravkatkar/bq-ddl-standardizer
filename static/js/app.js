window.addEventListener('DOMContentLoaded', function() {
    var toastEl = document.getElementById('flashToast');
    if (toastEl) {
        var toast = new bootstrap.Toast(toastEl, { delay: 4000 });
        toast.show();
    }

    clearJsonSchema();
    var browseTable = document.getElementById('browse_table');
    var bqTableName = document.getElementById('bq_table_name_browse');
    if (browseTable && bqTableName) {
        browseTable.addEventListener('change', function() {
            bqTableName.value = browseTable.value;
        });
    }
    // Initial tab loading logic
    if (typeof active_tab !== 'undefined') {
        if (active_tab === 'browse' && typeof mysql_connected !== 'undefined' && mysql_connected && typeof database !== 'undefined' && database) {
            loadMysqlTables();
        } else if (active_tab === 'browse' && typeof postgresql_connected !== 'undefined' && postgresql_connected && typeof database !== 'undefined' && database) {
            loadPostgresSchemas();
        } else if (active_tab === 'browse' && typeof sqlserver_connected !== 'undefined' && sqlserver_connected && typeof database !== 'undefined' && database) {
            loadSqlServerSchemas();
        }
        if (active_tab === 'browse') {
            var browseTab = document.getElementById('browse-tab');
            if (browseTab) {
                var tab = new bootstrap.Tab(browseTab);
                tab.show();
            }
        }
    }

    document.getElementById('json_schema').addEventListener('input', updateBQTableNameFromJSON);
    document.getElementById('source_ddl').addEventListener('input', updateBQTableNameFromDDL);
    updateBQTableNameFromJSON();
    updateBQTableNameFromDDL();
});

function loadMysqlTables() {
    const db = document.getElementById('browse_database').value;
    if (!db) {
        document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
        clearJsonSchema();
        return;
    }
    document.getElementById('browse_table').innerHTML = '<option>Loading...</option>';
    fetch(`/get_mysql_tables?database=${encodeURIComponent(db)}`)
        .then(response => response.json())
        .then(data => {
            let options = '<option value="">Select table...</option>';
            for (const tbl of data) {
                options += `<option value="${tbl}">${tbl}</option>`;
            }
            document.getElementById('browse_table').innerHTML = options;
            clearJsonSchema();
        })
        .catch(() => {
            document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
            clearJsonSchema();
        });
}

function loadPostgresSchemas() {
    const db = document.getElementById('browse_database').value;
    if (!db) {
        document.getElementById('browse_schema').innerHTML = '<option value="">Select schema...</option>';
        document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
        clearJsonSchema();
        return;
    }
    fetch(`/get_postgres_schemas?database=${encodeURIComponent(db)}`)
        .then(response => response.json())
        .then(data => {
            let options = '<option value="">Select schema...</option>';
            for (const schema of data) {
                options += `<option value="${schema}">${schema}</option>`;
            }
            document.getElementById('browse_schema').innerHTML = options;
            document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
            clearJsonSchema();
        });
}

function loadPostgresTables() {
    const db = document.getElementById('browse_database').value;
    const schema = document.getElementById('browse_schema').value;
    if (!db || !schema) {
        document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
        clearJsonSchema();
        return;
    }
    fetch(`/get_postgres_tables?database=${encodeURIComponent(db)}&schema=${encodeURIComponent(schema)}`)
        .then(response => response.json())
        .then(data => {
            let options = '<option value="">Select table...</option>';
            for (const tbl of data) {
                options += `<option value="${tbl}">${tbl}</option>`;
            }
            document.getElementById('browse_table').innerHTML = options;
            clearJsonSchema();
        });
}

function loadSqlServerSchemas() {
    const db = document.getElementById('browse_database').value;
    if (!db) {
        document.getElementById('browse_schema').innerHTML = '<option value="">Select schema...</option>';
        document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
        clearJsonSchema();
        return;
    }
    fetch(`/get_sqlserver_schemas?database=${encodeURIComponent(db)}`)
        .then(response => response.json())
        .then(data => {
            let options = '<option value="">Select schema...</option>';
            for (const schema of data) {
                options += `<option value="${schema}">${schema}</option>`;
            }
            document.getElementById('browse_schema').innerHTML = options;
            document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
            clearJsonSchema();
        });
}

function loadSqlServerTables() {
    const db = document.getElementById('browse_database').value;
    const schema = document.getElementById('browse_schema').value;
    if (!db || !schema) {
        document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
        clearJsonSchema();
        return;
    }
    fetch(`/get_sqlserver_tables?database=${encodeURIComponent(db)}&schema=${encodeURIComponent(schema)}`)
        .then(response => response.json())
        .then(data => {
            let options = '<option value="">Select table...</option>';
            for (const tbl of data) {
                options += `<option value="${tbl}">${tbl}</option>`;
            }
            document.getElementById('browse_table').innerHTML = options;
            clearJsonSchema();
        });
}

function clearJsonSchema() {
    document.getElementById('browse_json_schema').textContent = "";
    document.getElementById('generateDDLBtn').disabled = true;
    document.getElementById('bq_ddl_preview').style.display = 'none';
    document.getElementById('bq_ddl_preview').querySelector('pre').textContent = "";
    document.getElementById('bq_table_name_browse').value = "";
}

function showToast(message, type="warning", timeout=4000) {
    // Remove any existing custom toast
    let oldToast = document.getElementById('customAlertToast');
    if (oldToast) oldToast.remove();

    // Find or create toast container (reuse the one in your template)
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = "toast-container position-fixed p-3";
        toastContainer.style.zIndex = "1080";
        toastContainer.style.top = "1rem";
        toastContainer.style.right = "1rem";
        toastContainer.style.left = "auto";
        toastContainer.style.transform = "none";
        document.body.appendChild(toastContainer);
    }

    // Use Bootstrap's color classes: success, danger, warning
    let colorClass = "warning";
    if (type === "success") colorClass = "success";
    else if (type === "danger" || type === "error") colorClass = "danger";

    // Create toast element
    let toast = document.createElement('div');
    toast.id = 'customAlertToast';
    toast.className = `toast align-items-center text-bg-${colorClass} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    toastContainer.appendChild(toast);

    // Show toast using Bootstrap
    var bsToast = new bootstrap.Toast(toast, { delay: timeout });
    bsToast.show();
}

function getSchemaFromBrowse() {
    const dbSystem = document.getElementById('db_system').value;
    const db = document.getElementById('browse_database').value;
    const tbl = document.getElementById('browse_table').value;
    if (dbSystem === "postgresql") {
        const schema = document.getElementById('browse_schema').value;
        if (!db || !schema || !tbl) {
            showToast("Please select database, schema, and table.", "warning", 4000);
            return;
        }
        fetch(`/get_postgres_schema?database=${encodeURIComponent(db)}&schema=${encodeURIComponent(schema)}&table=${encodeURIComponent(tbl)}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('browse_json_schema').textContent = JSON.stringify(data.schema, null, 4);
                document.getElementById('bq_table_name_browse').value = data.schema.table_name || '';
                document.getElementById('generateDDLBtn').disabled = false;
                document.getElementById('bq_ddl_preview').style.display = 'none';
            });
    } else if (dbSystem === "sqlserver") {
        const schema = document.getElementById('browse_schema').value;
        if (!db || !schema || !tbl) {
            showToast("Please select database, schema, and table.", "warning", 4000);
            return;
        }
        fetch(`/get_sqlserver_schema?database=${encodeURIComponent(db)}&schema=${encodeURIComponent(schema)}&table=${encodeURIComponent(tbl)}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('browse_json_schema').textContent = JSON.stringify(data.schema, null, 4);
                document.getElementById('bq_table_name_browse').value = data.schema.table_name || '';
                document.getElementById('generateDDLBtn').disabled = false;
                document.getElementById('bq_ddl_preview').style.display = 'none';
            });
    } else if (dbSystem === "mysql") {
        if (!db || !tbl) {
            showToast("Please select both database and table.", "warning", 4000);
            return;
        }
        fetch(`/get_mysql_schema?database=${encodeURIComponent(db)}&table=${encodeURIComponent(tbl)}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('browse_json_schema').textContent = JSON.stringify(data.schema, null, 4);
                document.getElementById('bq_table_name_browse').value = data.schema.table_name || '';
                document.getElementById('generateDDLBtn').disabled = false;
                document.getElementById('bq_ddl_preview').style.display = 'none';
            });
    } else {
        showToast("Please select a database system.", "warning", 4000);
    }
}

function generateDDLFromSchema() {
    const schemaText = document.getElementById('browse_json_schema').textContent;
    const bq_project_id = document.getElementById('bq_project_id_browse').value;
    const bq_dataset_id = document.getElementById('bq_dataset_id_browse').value;
    const bq_table_name = document.getElementById('bq_table_name_browse').value;
    fetch('/generate_bq_ddl', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            schema: schemaText,
            bq_project_id: bq_project_id,
            bq_dataset_id: bq_dataset_id,
            bq_table_name: bq_table_name
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('bq_ddl_preview').style.display = 'block';
        document.getElementById('bq_ddl_preview').querySelector('pre').textContent = data.ddl;
        // Optional: enable download
        let blob = new Blob([data.ddl], {type: "text/sql"});
        let url = URL.createObjectURL(blob);
        let downloadBtn = document.getElementById('downloadDDLBtn');
        downloadBtn.href = url;
        downloadBtn.style.display = 'inline-block';
    });
}

function updateBQTableNameFromJSON() {
    try {
        var jsonText = document.getElementById('json_schema').value;
        var jsonObj = JSON.parse(jsonText);
        if (jsonObj.table_name) {
            document.getElementById('bq_table_name').value = jsonObj.table_name;
        }
    } catch (e) {
        // Ignore parse errors
    }
}

function updateBQTableNameFromDDL() {
    var ddlText = document.getElementById('source_ddl').value;
    var match = ddlText.match(/CREATE\s+TABLE\s+[`"]?(\w+)[`"]?/i);
    if (match && match[1]) {
        document.getElementById('bq_table_name').value = match[1];
    }
}

function clearTextarea(id) {
    document.getElementById(id).value = "";
    if (id === "json_schema") {
        updateBQTableNameFromJSON();
    }
}

function onDatabaseChange() {
    const dbSystem = document.getElementById('db_system').value;
    const db = document.getElementById('browse_database').value;
    document.getElementById('browse_schema').innerHTML = '<option value="">Select schema...</option>';
    document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
    clearJsonSchema();
    if (!db) return;
    fetch(`/get_schemas?db_system=${encodeURIComponent(dbSystem)}&database=${encodeURIComponent(db)}`)
        .then(response => response.json())
        .then(data => {
            let options = '<option value="">Select schema...</option>';
            for (const schema of data.schemas) {
                options += `<option value="${schema}">${schema}</option>`;
            }
            document.getElementById('browse_schema').innerHTML = options;
        });
}

function onSchemaChange() {
    const dbSystem = document.getElementById('db_system').value;
    const db = document.getElementById('browse_database').value;
    const schema = document.getElementById('browse_schema').value;
    document.getElementById('browse_table').innerHTML = '<option value="">Select table...</option>';
    clearJsonSchema();
    if (!db || !schema) return;
    let url = "";
    if (dbSystem === "postgresql") {
        url = `/get_postgres_tables?database=${encodeURIComponent(db)}&schema=${encodeURIComponent(schema)}`;
    } else {
        url = `/get_tables?db_system=${encodeURIComponent(dbSystem)}&database=${encodeURIComponent(db)}&schema=${encodeURIComponent(schema)}`;
    }
    fetch(url)
        .then(response => response.json())
        .then(data => {
            let options = '<option value="">Select table...</option>';
            let tables = data.tables || data;
            for (const tbl of tables) {
                options += `<option value="${tbl}">${tbl}</option>`;
            }
            document.getElementById('browse_table').innerHTML = options;
        });
}

function clearConnectionForm() {
    document.getElementById('sourceConnectionForm').reset();
    fetch('/clear_connection', {method: 'POST'})
        .then(() => {
            var manualTab = document.getElementById('manual-tab');
            if (manualTab) {
                var tab = new bootstrap.Tab(manualTab);
                tab.show();
            }
            window.location.href = window.location.pathname + '?active_tab=manual';
        });
}

setTimeout(function() {
    var alert = document.querySelector('.alert');
    if (alert) {
        alert.classList.remove('show');
        alert.classList.add('hide');
    }
}, 4000);

function updateFormAction() {
    var dbSystem = document.getElementById('db_system').value;
    var form = document.getElementById('sourceConnectionForm');
    if (dbSystem === "mysql") {
        form.action = "/connect_mysql";
    } else if (dbSystem === "postgresql") {
        form.action = "/connect_postgres";
    } else if (dbSystem === "sqlserver") {
        form.action = "/connect_sqlserver";
    } else {
        form.action = "/connect";
    }
}