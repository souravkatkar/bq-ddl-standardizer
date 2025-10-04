import os
from flask import Blueprint, jsonify

ai_util_bp = Blueprint('ai_util_bp', __name__)

@ai_util_bp.route('/list_models')
def list_models():
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    try:
        models = [f for f in os.listdir(models_dir) if f.endswith('.gguf')]
    except Exception:
        models = []
    return jsonify(models)