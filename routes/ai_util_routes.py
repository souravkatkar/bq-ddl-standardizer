import os
from flask import Blueprint, request, jsonify
from src.ai_utils import add_comments_to_json_schema

ai_util_bp = Blueprint('ai_util_bp', __name__)

@ai_util_bp.route('/list_models')
def list_models():
    models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    try:
        models = [f for f in os.listdir(models_dir) if f.endswith('.gguf')]
    except Exception:
        models = []
    return jsonify(models)

@ai_util_bp.route('/ai_add_comment', methods=['POST'])
def ai_add_comment():
    data = request.get_json()
    json_schema = data.get('json_schema', '')
    model_name = data.get('model', '')
    updated_schema = add_comments_to_json_schema(json_schema, model_name)
    return jsonify({"schema": updated_schema})