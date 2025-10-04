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
            });
        }
    });

    attachAIButtonHoverHints();
});