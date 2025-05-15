from abc import ABC, abstractmethod
from flask import current_app
import json
import uuid
import time
import requests
import logging
from typing import Dict, Any, Optional, List
from .base import ChatService

# 创建模块级别的日志记录器并设置编码
logger = logging.getLogger('app.services.chat.dify')

class DifyService(ChatService):
    """Dify聊天服务"""
    
    def __init__(self):
        logger.info("正在初始化DifyService...")
        self.api_key = current_app.config.get('DIFY_API_KEY')
        self.api_base = current_app.config.get('DIFY_API_BASE_URL', 'http://localhost:8580')  # 默认本地地址
        self.api_proxy = current_app.config.get('DIFY_API_PROXY')
        self.default_model = current_app.config.get('DIFY_MODEL', 'dify-default')
        self.available_models = current_app.config.get('CHAT_SOURCES', {}).get('dify', {}).get('models', [])
        print(current_app.config.get('DIFY_API_KEY'))
        # 检查必要的配置
        if not self.api_key:
            logger.error("Dify API密钥未配置")
            raise ValueError("Dify API密钥未配置")
            
        # 确保API基础URL正确
        if not self.api_base:
            logger.error("Dify API基础URL未配置")
            raise ValueError("Dify API基础URL未配置")
        
        # 移除URL末尾的斜杠
        self.api_base = self.api_base.rstrip('/')
        
        # 如果URL末尾包含/api，去掉它
        if self.api_base.endswith('/api'):
            self.api_base = self.api_base[:-4]
            
        logger.info(f"初始化完成，使用API基础URL: {self.api_base}")
        self.print_config()
        
    def print_config(self):
        """打印服务配置信息"""
        logger.info("========== Dify服务配置信息 ==========")
        logger.info(f"API密钥: {self.api_key[:5]}..." if self.api_key else "API密钥: 未设置")
        logger.info(f"API基础URL: {self.api_base}")
        logger.info(f"API代理: {self.api_proxy}")
        logger.info(f"默认模型: {self.default_model}")
        logger.info(f"可用模型: {self.available_models}")
        logger.info("=====================================")

    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """
        执行聊天完成请求
        :param messages: 消息列表
        :param kwargs: 其他参数
        :return: 响应数据
        """
        try:
            logger.info("开始执行Dify请求")
            logger.info(f"接收到的消息: {json.dumps(messages, ensure_ascii=False)}")
            logger.info(f"接收到的参数: {json.dumps(kwargs, ensure_ascii=False)}")
            self.print_config()
            
            # 从kwargs中获取参数
            model = kwargs.pop('model', None) or self.default_model
            stream = kwargs.pop('stream', False)
            user = kwargs.pop('user', None)
            
            logger.info(f"处理后的参数 - model: {model}, stream: {stream}, user: {user}")
            
            # 从消息中提取用户最后一条消息内容
            user_message = None
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content')
                    break
            
            if not user_message:
                logger.warning("未找到用户消息")
                return {
                    'error': {
                        'message': "缺少用户消息",
                        'type': 'invalid_request_error',
                        'code': 'missing_user_message'
                    },
                    'status_code': 400
                }
            
            # 准备请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8"
            }
            
            # 构建请求数据
            data = {
                'query': user_message,
                'conversation_id': str(uuid.uuid4()),
                'user': user or 'default_user',
                'stream': stream,
                "response_mode": "blocking",
                'inputs': {
                    "query": user_message,
                }
            }
            
            # 如果有其他参数，添加到inputs中
            for key, value in kwargs.items():
                if key not in ['stream', 'user', 'model']:
                    data['inputs'][key] = value
            
            # 构建API URL
            api_url = f"{self.api_base.rstrip('/')}/workflows/run"
            
            logger.info(f"发送Dify API请求: {api_url}")
            logger.info(f"请求参数: {json.dumps(data, ensure_ascii=False)}")
            
            # 发送请求
            start_time = time.time()
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=data,
                    timeout=600,
                    stream=stream
                )
                logger.info(f"HTTP请求完成，状态码: {response.status_code}")
                logger.info(f"响应内容: {response.text[:200]}...")  # 只记录前200个字符
            except requests.exceptions.RequestException as e:
                logger.error(f"HTTP请求异常: {str(e)}")
                raise
            
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 3000)
            
            # 检查响应
            if response.status_code != 200:
                error_msg = f"Dify工作流API请求失败: 状态码={response.status_code}, 响应={response.text}"
                logger.error(error_msg)
                return {
                    'error': {
                        'message': error_msg,
                        'type': 'server_error',
                        'code': 'dify_api_error'
                    },
                    'status_code': response.status_code
                }
                
            # 解析响应
            try:
                # 处理流式响应
                if stream:
                    return {
                        "id": f"dify-wf-{str(uuid.uuid4())}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": response
                                },
                                "finish_reason": None
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0
                        },
                        "server_latency_ms": latency_ms,
                        "provider": "dify"
                    }
                
                # 处理普通响应
                result_data = response.json()
                logger.info(f"收到响应数据: {json.dumps(result_data, ensure_ascii=False)}")
                
                # 获取工作流结果
                workflow_result = result_data.get('data', {}).get('outputs', {}).get('data', '')
                content = workflow_result
                
                # 尝试解析内部JSON数据
                try:
                    if isinstance(workflow_result, str):
                        inner_data = json.loads(workflow_result)
                        content = inner_data
                except Exception as parse_error:
                    logger.warning(f"解析内部数据失败: {str(parse_error)}")
                    content = workflow_result
                
                # 转换为OpenAI兼容格式
                result = {
                    "id": f"dify-wf-{str(uuid.uuid4())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": result_data.get('data', {}).get('usage', {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }),
                    "server_latency_ms": latency_ms,
                    "provider": "dify"
                }
                
                return result
                
            except json.JSONDecodeError as e:
                error_msg = f"解析Dify API响应失败: {response.text}"
                logger.error(error_msg)
                return {
                    'error': {
                        'message': error_msg,
                        'type': 'server_error',
                        'code': 'dify_response_error'
                    },
                    'status_code': 500
                }
                
        except requests.RequestException as e:
            error_msg = f"Dify工作流API请求异常: {str(e)}"
            logger.error(error_msg)
            return {
                'error': {
                    'message': error_msg,
                    'type': 'server_error',
                    'code': 'dify_network_error'
                },
                'status_code': 500
            }
        except Exception as e:
            error_msg = f"Dify工作流执行失败: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return {
                'error': {
                    'message': error_msg,
                    'type': 'server_error',
                    'code': 'dify_execution_error'
                },
                'status_code': 500
            }
    
    def list_models(self) -> List[Dict]:
        """获取Dify可用模型列表"""
        models = []
        for model_id in self.available_models:
            models.append({
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "dify"
            })
        return models 