from flask import Blueprint, jsonify, request, current_app
import requests
import os
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
import time
import uuid
import logging
from app.services.chat.factory import ChatServiceFactory

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')
logger = logging.getLogger('app.chat')

def get_chat_provider(provider_name=None):
    """
    获取指定聊天提供商的配置
    如果未指定提供商，则返回默认提供商（OpenAI）
    """
    providers = {
        'openai': {
            'api_key': current_app.config.get('OPENAI_API_KEY'),
            'api_base': current_app.config.get('OPENAI_API_BASE', 'https://api.openai.com/v1'),
            'api_proxy': current_app.config.get('OPENAI_API_PROXY'),
            'default_model': current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'available_models': current_app.config.get('OPENAI_AVAILABLE_MODELS', [
                'gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'
            ])
        },
        'deepseek': {
            'api_key': current_app.config.get('DEEPSEEK_API_KEY'),
            'api_base': current_app.config.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1'),
            'api_proxy': current_app.config.get('DEEPSEEK_API_PROXY'),
            'default_model': current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat'),
            'available_models': current_app.config.get('DEEPSEEK_AVAILABLE_MODELS', [
                'deepseek-chat', 'deepseek-coder'
            ])
        },
        'tongyi': {
            'api_key': current_app.config.get('TONGYI_API_KEY'),
            'api_base': current_app.config.get('TONGYI_API_BASE', 'https://api.tongyi.aliyun.com/v1'),
            'api_proxy': current_app.config.get('TONGYI_API_PROXY'),
            'default_model': current_app.config.get('TONGYI_MODEL', 'qwen-max'),
            'available_models': current_app.config.get('TONGYI_AVAILABLE_MODELS', [
                'qwen-max', 'qwen-plus', 'qwen-turbo'
            ])
        }
    }
    
    if provider_name and provider_name in providers:
        return provider_name, providers[provider_name]
    
    # 如果未指定有效的提供商，尝试找到第一个有API密钥的提供商
    for name, config in providers.items():
        if config['api_key']:
            return name, config
            
    # 默认返回OpenAI（即使它可能没有API密钥）
    return 'openai', providers['openai']

@chat_bp.route('/completions', methods=['POST'])
@jwt_required()
def chat_completions():
    """聊天完成API"""
    try:
        # 获取用户身份
        user_id = get_jwt_identity()
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({
                "error": {
                    "message": "无效的请求数据",
                    "type": "invalid_request_error",
                    "code": "invalid_request"
                }
            }), 400
            
        # 获取提供商
        provider = data.pop('provider', 'openai')
        
        # 获取聊天服务
        service = ChatServiceFactory.get_service(provider)
        if not service:
            return jsonify({
                "error": {
                    "message": f"不支持的服务提供商: {provider}",
                    "type": "invalid_request_error",
                    "code": "unsupported_provider"
                }
            }), 400
            
        # 从data中提取messages和model
        messages = data.pop('messages')
        model = data.pop('model', None)
            
        # 调用聊天服务
        result = service.chat_completion(
            messages=messages,
            model=model,
            **data  # 其他参数
        )
        
        # 检查错误
        if 'error' in result:
            return jsonify(result['error']), result.get('status_code', 500)
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"聊天API错误: {str(e)}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_server_error"
            }
        }), 500

@chat_bp.route('/providers', methods=['GET'])
def list_providers():
    """获取支持的服务提供商列表"""
    try:
        providers = ChatServiceFactory.list_providers()
        return jsonify({
            "success": True,
            "providers": providers
        })
    except Exception as e:
        logger.error(f"获取提供商列表失败: {str(e)}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_server_error"
            }
        }), 500

@chat_bp.route('/models', methods=['GET'])
def list_models():
    """获取指定提供商的可用模型列表"""
    try:
        provider = request.args.get('provider', 'openai')
        service = ChatServiceFactory.get_service(provider)
        
        if not service:
            return jsonify({
                "error": {
                    "message": f"不支持的服务提供商: {provider}",
                    "type": "invalid_request_error",
                    "code": "unsupported_provider"
                }
            }), 400
            
        models = service.list_models()
        return jsonify({
            "success": True,
            "models": models
        })
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return jsonify({
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_server_error"
            }
        }), 500 