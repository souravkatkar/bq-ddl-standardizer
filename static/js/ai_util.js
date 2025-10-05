function toggleAIOptions() {
    const aiGroup = document.getElementById('ai-model-group');
    aiGroup.style.display = document.getElementById('use_ai_toggle').checked ? '' : 'none';
    updateAIButtonsState();
}

function updateAIButtonsState() {
    const useAI = document.getElementById('use_ai_toggle').checked;
    const modelSelected = document.getElementById('ai_model_select').value;
    const btnIds = [
        'standardizeDDLBtn', 'addCommentsDDLBtn',
        'standardizeDDLBtnManual', 'addCommentsDDLBtnManual'
    ];
    btnIds.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = !(useAI && modelSelected);
    });
}

function sendSchemaToAI(jsonSchema, modelName, callback) {
    fetch('/ai_add_comment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ json_schema: jsonSchema, model: modelName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.schema) {
            showToast("AI comments added!", "success", 2000);
            callback(data.schema);
        } else {
            showToast("AI failed to add comments.", "danger", 4000);
        }
    })
    .catch(() => {
        showToast("Error communicating with AI service.", "danger", 4000);
    });
}

function sendDDLToAI(ddl, modelName) {
    fetch('/ai_add_comment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ddl: ddl, model: modelName })
    })
    .then(response => response.json())
    .then(data => {
        showToast("AI Response: " + (data.response || "No response"), "info", 5000);
        console.log("AI Response:", data.response);
    })
    .catch(() => {
        showToast("Error communicating with AI service.", "danger", 4000);
    });
}

function updateDownloadDDLBtn(ddl, btnId = "downloadDDLBtn") {
    const downloadBtn = document.getElementById(btnId);
    if (downloadBtn) {
        const blob = new Blob([ddl], { type: "text/sql" });
        const url = URL.createObjectURL(blob);
        downloadBtn.href = url;
        downloadBtn.download = "bigquery_ddl.sql";
        downloadBtn.style.display = "";
    }
}

function handleAddCommentsDDLBtn(id) {
    console.log("[AI] handleAddCommentsDDLBtn called with id:", id);
    let jsonSchema = null;
    const bq_project_id = document.getElementById('bq_project_id_browse').value;
    const bq_dataset_id = document.getElementById('bq_dataset_id_browse').value;
    const bq_table_name = document.getElementById('bq_table_name_browse').value;

    if (id === 'addCommentsDDLBtn') {
        jsonSchema = document.getElementById('browse_json_schema')?.textContent;
    } else {
        jsonSchema = document.getElementById('json_schema')?.value;
    }
    const modelName = document.getElementById('ai_model_select').value;

    if (jsonSchema && modelName) {
        showLoadingOverlay();
        sendSchemaToAI(jsonSchema, modelName, function(updatedSchema) {
            fetch('/generate_bq_ddl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    schema: JSON.stringify(updatedSchema),
                    bq_project_id: bq_project_id,
                    bq_dataset_id: bq_dataset_id,
                    bq_table_name: bq_table_name
                })
            })
            .then(response => response.json())
            .then(data => {
                if (id === 'addCommentsDDLBtn') {
                    document.querySelector('#bq_ddl_preview pre').textContent = data.ddl;
                    updateDownloadDDLBtn(data.ddl, "downloadDDLBtn");
                } else {
                    document.querySelector('#bq_ddl_preview_manual pre').textContent = data.ddl;
                    updateDownloadDDLBtn(data.ddl, "downloadDDLBtnManual");
                }
                hideLoadingOverlay();
                showToast("Preview updated with AI comments!", "success", 2000);
            })
            .catch(() => {
                hideLoadingOverlay();
                showToast("Error generating DDL.", "danger", 2000);
            });
        });
    } else {
        showToast("Missing schema or model.", "danger", 2000);
    }
}


// Fetch models from the backend and populate the select
window.addEventListener('DOMContentLoaded', function() {
    fetch('/list_models')
        .then(response => response.json())
        .then(models => {
            const select = document.getElementById('ai_model_select');
            select.innerHTML = models.length
                ? models.map(m => `<option value="${m}">${m}</option>`).join('')
                : '<option value="">No models found</option>';
            updateAIButtonsState();
        })
        .catch(() => {
            document.getElementById('ai_model_select').innerHTML = '<option value="">Error loading models</option>';
            updateAIButtonsState();
        });

    // Update button state on model change
    const modelSelect = document.getElementById('ai_model_select');
    if (modelSelect) {
        modelSelect.addEventListener('change', updateAIButtonsState);
    }
    // Also update on toggle change
    const aiToggle = document.getElementById('use_ai_toggle');
    if (aiToggle) {
        aiToggle.addEventListener('change', updateAIButtonsState);
    }

    // Add click handlers for all AI buttons
    ['standardizeDDLBtn', 'standardizeDDLBtnManual'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', function() {
                showToast("Processing Standardize DDL...", "info", 2000);
            });
        }
    });
    ['addCommentsDDLBtn', 'addCommentsDDLBtnManual'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener('click', function() {
                showToast("Processing Add Comments to DDL...", "info", 2000);
                handleAddCommentsDDLBtn(id);
            });
        }
    });

});

function showLoadingOverlay() {
    document.getElementById('gpt-loading-overlay').style.display = 'flex';
}
function hideLoadingOverlay() {
    document.getElementById('gpt-loading-overlay').style.display = 'none';
}