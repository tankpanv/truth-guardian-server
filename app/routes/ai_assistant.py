"""
AI助手路由模块
"""
from flask import Blueprint, render_template, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

# 创建蓝图
ai_assistant_bp = Blueprint('ai_assistant', __name__)

@ai_assistant_bp.route('/ai-chat')
def ai_chat_view():
    """AI聊天页面"""
    return render_template('ai_chat.html')

def init_app(app):
    """初始化应用，注册蓝图"""
    app.register_blueprint(ai_assistant_bp) 