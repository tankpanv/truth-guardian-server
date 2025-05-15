from abc import ABC, abstractmethod
from flask import current_app
import json
import uuid
import time
import requests
import logging
from typing import Dict, Any, Optional, List, Type
from .base import ChatService
from .coze_service import CozeService
from .dify import DifyService

logger = logging.getLogger('app.chat.factory')

class OpenAIService(ChatService):
    """OpenAI聊天服务"""
    
    def __init__(self):
        self.api_key = current_app.config.get('OPENAI_API_KEY')
        self.api_base = current_app.config.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.api_proxy = current_app.config.get('OPENAI_API_PROXY')
        self.default_model = current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.available_models = current_app.config.get('CHAT_SOURCES', {}).get('openai', {}).get('models', [])
        
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> Dict:
        """处理OpenAI聊天完成请求"""
        # 准备参数
        model = model or self.default_model
        data = kwargs.copy()
        data['messages'] = messages
        data['model'] = model
        
        # 准备请求头
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 准备代理
        proxies = None
        if self.api_proxy:
            proxies = {
                'http': self.api_proxy,
                'https': self.api_proxy
            }
        
        # 构建API URL
        api_url = f"{self.api_base}/chat/completions"
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=120
        )
        end_time = time.time()
        
        # 计算延迟
        latency_ms = int((end_time - start_time) * 1000)
        
        # 检查响应
        if response.status_code != 200:
            # 尝试解析错误
            try:
                error_data = response.json()
                return {'error': error_data, 'status_code': response.status_code}
            except:
                return {
                    'error': {
                        'message': f"OpenAI API调用失败: {response.text}",
                        'type': 'server_error',
                        'code': 'openai_api_error'
                    },
                    'status_code': response.status_code
                }
        
        # 获取API的响应数据
        result = response.json()
        
        # 添加额外信息
        result["server_latency_ms"] = latency_ms
        result["provider"] = "openai"
        if "id" not in result:
            result["id"] = f"chatcmpl-{str(uuid.uuid4())}"
            
        return result
    
    def list_models(self) -> List[Dict]:
        """获取OpenAI可用模型列表"""
        models = []
        for model_id in self.available_models:
            models.append({
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "openai"
            })
        return models

class ChatServiceFactory:
    """聊天服务工厂类"""
    
    _services: Dict[str, Type[ChatService]] = {}
    _instances: Dict[str, ChatService] = {}
    
    @classmethod
    def register(cls, name: str, service_class: Type[ChatService]) -> None:
        """
        注册聊天服务
        
        Args:
            name: 服务名称
            service_class: 服务类
        """
        cls._services[name] = service_class
        
    @classmethod
    def get_service(cls, name: str, api_key: str = None, **kwargs) -> Optional[ChatService]:
        """
        获取聊天服务实例
        
        Args:
            name: 服务名称
            api_key: API密钥（可选，某些服务从配置文件获取）
            **kwargs: 其他参数传递给服务构造函数
            
        Returns:
            Optional[ChatService]: 服务实例，如果服务不存在则返回None
        """
        if name not in cls._services:
            return None
            
        if name not in cls._instances:
            service_class = cls._services[name]
            if api_key:
                cls._instances[name] = service_class(api_key, **kwargs)
            else:
                cls._instances[name] = service_class()
            
        return cls._instances[name]
        
    @classmethod
    def list_providers(cls) -> Dict[str, Type[ChatService]]:
        """
        获取所有已注册的服务提供商
        
        Returns:
            Dict[str, Type[ChatService]]: 服务名称到服务类的映射
        """
        return cls._services.copy()

# 注册服务
ChatServiceFactory.register('openai', OpenAIService)
ChatServiceFactory.register('coze', CozeService)
ChatServiceFactory.register('dify', DifyService)

class DeepSeekService(ChatService):
    """DeepSeek聊天服务"""
    
    def __init__(self):
        self.api_key = current_app.config.get('DEEPSEEK_API_KEY')
        self.api_base = current_app.config.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
        self.api_proxy = current_app.config.get('DEEPSEEK_API_PROXY')
        self.default_model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat')
        self.available_models = current_app.config.get('CHAT_SOURCES', {}).get('deepseek', {}).get('models', [])
        
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> Dict:
        """处理DeepSeek聊天完成请求"""
        # 准备参数
        model = model or self.default_model
        data = kwargs.copy()
        data['messages'] = messages
        data['model'] = model
        
        # 准备请求头
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 准备代理
        proxies = None
        if self.api_proxy:
            proxies = {
                'http': self.api_proxy,
                'https': self.api_proxy
            }
        
        # 构建API URL
        api_url = f"{self.api_base}/chat/completions"
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=120
        )
        end_time = time.time()
        
        # 计算延迟
        latency_ms = int((end_time - start_time) * 1000)
        
        # 检查响应
        if response.status_code != 200:
            # 尝试解析错误
            try:
                error_data = response.json()
                return {'error': error_data, 'status_code': response.status_code}
            except:
                return {
                    'error': {
                        'message': f"DeepSeek API调用失败: {response.text}",
                        'type': 'server_error',
                        'code': 'deepseek_api_error'
                    },
                    'status_code': response.status_code
                }
        
        # 获取API的响应数据
        result = response.json()
        
        # 添加额外信息
        result["server_latency_ms"] = latency_ms
        result["provider"] = "deepseek"
        if "id" not in result:
            result["id"] = f"chatcmpl-{str(uuid.uuid4())}"
            
        return result
    
    def list_models(self) -> List[Dict]:
        """获取DeepSeek可用模型列表"""
        models = []
        for model_id in self.available_models:
            models.append({
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "deepseek"
            })
        return models


class TongyiService(ChatService):
    """通义千问聊天服务"""
    
    def __init__(self):
        self.api_key = current_app.config.get('TONGYI_API_KEY')
        self.api_base = current_app.config.get('TONGYI_API_BASE', 'https://api.tongyi.aliyun.com/v1')
        self.api_proxy = current_app.config.get('TONGYI_API_PROXY')
        self.default_model = current_app.config.get('TONGYI_MODEL', 'qwen-max')
        self.available_models = current_app.config.get('CHAT_SOURCES', {}).get('tongyi', {}).get('models', [])
        
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> Dict:
        """处理通义千问聊天完成请求"""
        # 准备参数
        model = model or self.default_model
        
        # 转换请求格式
        request_data = {
            "model": model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": kwargs.get('temperature', 0.7),
                "top_p": kwargs.get('top_p', 0.9),
                "max_tokens": kwargs.get('max_tokens', 2000)
            }
        }
        
        # 准备请求头
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 准备代理
        proxies = None
        if self.api_proxy:
            proxies = {
                'http': self.api_proxy,
                'https': self.api_proxy
            }
        
        # 构建API URL
        api_url = f"{self.api_base}/generations"
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            api_url,
            headers=headers,
            json=request_data,
            proxies=proxies,
            timeout=120
        )
        end_time = time.time()
        
        # 计算延迟
        latency_ms = int((end_time - start_time) * 1000)
        
        # 检查响应
        if response.status_code != 200:
            # 尝试解析错误
            try:
                error_data = response.json()
                return {'error': error_data, 'status_code': response.status_code}
            except:
                return {
                    'error': {
                        'message': f"通义千问 API调用失败: {response.text}",
                        'type': 'server_error',
                        'code': 'tongyi_api_error'
                    },
                    'status_code': response.status_code
                }
        
        # 获取API的响应数据
        original_result = response.json()
        
        # 将通义千问响应转换为OpenAI兼容格式
        try:
            result = {
                "id": original_result.get("request_id", f"chatcmpl-{str(uuid.uuid4())}"),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": original_result["output"]["text"]
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": original_result.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": original_result.get("usage", {}).get("output_tokens", 0),
                    "total_tokens": original_result.get("usage", {}).get("total_tokens", 0)
                }
            }
        except Exception as e:
            current_app.logger.error(f"通义千问响应格式转换失败: {str(e)}")
            current_app.logger.error(f"原始响应: {original_result}")
            return {
                'error': {
                    'message': f"通义千问响应格式转换失败: {str(e)}",
                    'type': 'server_error',
                    'code': 'tongyi_format_error'
                },
                'status_code': 500
            }
        
        # 添加额外信息
        result["server_latency_ms"] = latency_ms
        result["provider"] = "tongyi"
        
        return result
    
    def list_models(self) -> List[Dict]:
        """获取通义千问可用模型列表"""
        models = []
        for model_id in self.available_models:
            models.append({
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "tongyi"
            })
        return models


class CozeService(ChatService):
    """Coze聊天服务"""
    
    def __init__(self):
        self.api_key = current_app.config.get('COZE_API_KEY')
        self.api_base = current_app.config.get('COZE_API_BASE_URL', 'https://api.coze.cn/v1')
        self.workflow_id = current_app.config.get('COZE_WORKFLOW_ID')
        self.rumor_workflow_id = current_app.config.get('COZE_RUMOR_WORKFLOW_ID')
        self.app_id = current_app.config.get('COZE_APP_ID')
        self.bot_id = current_app.config.get('COZE_BOT_ID')
        self.user_id = current_app.config.get('COZE_USER_ID', 'user123')
        
    def chat_completion(self, messages: List[Dict], model: str = None, **kwargs) -> Dict:
        """处理Coze聊天完成请求"""
        # 确定使用哪种模式
        mode = kwargs.get('mode', 'default')
        
        # 处理谣言粉碎机模式
        if mode == 'rumor_crusher' or model == 'coze-rumor-crusher':
            return self._call_rumor_crusher_workflow(messages, **kwargs)
        # 如果调用的是Bot API
        elif kwargs.get('use_bot', False) or not self.workflow_id:
            return self._chat_with_bot(messages, **kwargs)
        else:
            # 默认使用Workflow API
            return self._call_workflow(messages, **kwargs)
    
    def _call_rumor_crusher_workflow(self, messages: List[Dict], **kwargs) -> Dict:
        """调用Coze谣言粉碎机工作流API处理消息"""
        try:
            logging.info(f"开始执行Coze谣言粉碎机工作流: workflow_id={self.rumor_workflow_id}")
            
            # 从消息中提取用户最后一条消息内容
            user_message = None
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content')
                    break
            
            if not user_message:
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
                "Content-Type": "application/json"
            }
            
            # 构建API请求数据
            payload = {
                "workflow_id": self.rumor_workflow_id or self.workflow_id,
                "user_id": self.user_id,
                "app_id": self.app_id,
                "parameters": {
                    "query": user_message
                }
            }
            
            # 如果没有app_id，从参数中获取
            if not self.app_id and kwargs.get('app_id'):
                payload["app_id"] = kwargs.get('app_id')
                
            # 如果有额外的工作流参数，添加到parameters中
            if kwargs.get('workflow_params'):
                payload["parameters"].update(kwargs.get('workflow_params'))
            
            api_url = f"{self.api_base.rstrip('/')}/workflow/run"
            logging.info(f"发送谣言粉碎机工作流请求: {api_url}")
            logging.info(f"请求参数: {payload}")
            
            # 发送请求
            start_time = time.time()
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=600,
                verify=False,  # 临时禁用 SSL 验证
                proxies={
                    'http': None,
                    'https': None
                }
            )
            end_time = time.time()
            
            # 计算延迟
            latency_ms = int((end_time - start_time) * 1000)
            
            # 检查响应
            if response.status_code != 200:
                return {
                    'error': {
                        'message': f"Coze谣言粉碎机工作流API请求失败: 状态码={response.status_code}, 响应={response.text}",
                        'type': 'server_error',
                        'code': 'coze_api_error'
                    },
                    'status_code': response.status_code
                }
                
            # 解析响应
            try:
                result_data = response.json()
                logging.info(f"谣言粉碎机工作流执行完成，状态码: {result_data.get('code')}")
                
                # 检查API响应是否成功
                if result_data.get('code') != 0:  # Coze API成功代码是0
                    return {
                        'error': {
                            'message': f"Coze谣言粉碎机工作流API错误: code={result_data.get('code')}, msg={result_data.get('msg', '未知错误')}",
                            'type': 'server_error',
                            'code': 'coze_workflow_error'
                        },
                        'status_code': 500
                    }
                
                # 获取工作流结果
                workflow_result = result_data.get('data', {})
                content = workflow_result
                
                # 尝试解析内部JSON数据
                try:
                    if isinstance(workflow_result, str):
                        inner_data = json.loads(workflow_result)
                        content = inner_data
                except Exception as parse_error:
                    logging.warning(f"解析内部数据失败: {str(parse_error)}")
                    content = workflow_result
                
                # 转换为OpenAI兼容格式
                result = {
                    "id": f"coze-rumor-{str(uuid.uuid4())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "coze-rumor-crusher",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(content, ensure_ascii=False) if isinstance(content, dict) else str(content)
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    },
                    "server_latency_ms": latency_ms,
                    "provider": "coze",
                    "debug_url": result_data.get('debug_url', '')
                }
                
                return result
                
            except json.JSONDecodeError:
                return {
                    'error': {
                        'message': f"解析Coze谣言粉碎机API响应失败: {response.text}",
                        'type': 'server_error',
                        'code': 'coze_response_error'
                    },
                    'status_code': 500
                }
                
        except requests.RequestException as e:
            return {
                'error': {
                    'message': f"Coze谣言粉碎机工作流API请求异常: {str(e)}",
                    'type': 'server_error',
                    'code': 'coze_network_error'
                },
                'status_code': 500
            }
        except Exception as e:
            logging.error(f"Coze谣言粉碎机工作流执行失败: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return {
                'error': {
                    'message': f"Coze谣言粉碎机工作流执行失败: {str(e)}",
                    'type': 'server_error',
                    'code': 'coze_execution_error'
                },
                'status_code': 500
            }
    
    def _call_workflow(self, messages: List[Dict], **kwargs) -> Dict:
        """调用Coze工作流API处理消息"""
        try:
            logging.info(f"开始执行Coze工作流: workflow_id={self.workflow_id}")
            
            # 从消息中提取用户最后一条消息内容
            user_message = None
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content')
                    break
            
            if not user_message:
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
                "Content-Type": "application/json"
            }
            
            # 构建API请求数据
            payload = {
                "workflow_id": self.workflow_id,
                "user_id": self.user_id,
                "parameters": {
                    "query": user_message
                }
            }
            
            # 添加app_id如果有的话
            if kwargs.get('app_id'):
                payload["app_id"] = kwargs.get('app_id')
                
            # 如果有额外的工作流参数，添加到parameters中
            if kwargs.get('workflow_params'):
                payload["parameters"].update(kwargs.get('workflow_params'))
            
            api_url = f"{self.api_base.rstrip('/')}/workflow/run"
            logging.info(f"发送工作流请求: {api_url}")
            
            # 发送请求
            start_time = time.time()
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=600,
                verify=False,  # 临时禁用 SSL 验证
                proxies={
                    'http': None,
                    'https': None
                }
            )
            end_time = time.time()
            
            # 计算延迟
            latency_ms = int((end_time - start_time) * 1000)
            
            # 检查响应
            if response.status_code != 200:
                return {
                    'error': {
                        'message': f"Coze工作流API请求失败: 状态码={response.status_code}, 响应={response.text}",
                        'type': 'server_error',
                        'code': 'coze_api_error'
                    },
                    'status_code': response.status_code
                }
                
            # 解析响应
            try:
                result_data = response.json()
                logging.info(f"工作流执行完成，状态码: {result_data.get('code')}")
                
                # 检查API响应是否成功
                if result_data.get('code') != 0:  # Coze API成功代码是0
                    return {
                        'error': {
                            'message': f"Coze工作流API错误: code={result_data.get('code')}, msg={result_data.get('msg', '未知错误')}",
                            'type': 'server_error',
                            'code': 'coze_workflow_error'
                        },
                        'status_code': 500
                    }
                
                # 获取工作流结果
                workflow_result = result_data.get('data', {})
                content = workflow_result
                
                # 尝试解析内部JSON数据
                try:
                    if isinstance(workflow_result, str):
                        inner_data = json.loads(workflow_result)
                        content = inner_data
                except Exception as parse_error:
                    logging.warning(f"解析内部数据失败: {str(parse_error)}")
                    content = workflow_result
                
                # 转换为OpenAI兼容格式
                result = {
                    "id": f"coze-wf-{str(uuid.uuid4())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "coze-rumor-crusher",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(content, ensure_ascii=False) if isinstance(content, dict) else str(content)
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    },
                    "server_latency_ms": latency_ms,
                    "provider": "coze",
                    "debug_url": result_data.get('debug_url', '')
                }
                
                return result
                
            except json.JSONDecodeError:
                return {
                    'error': {
                        'message': f"解析Coze API响应失败: {response.text}",
                        'type': 'server_error',
                        'code': 'coze_response_error'
                    },
                    'status_code': 500
                }
                
        except requests.RequestException as e:
            return {
                'error': {
                    'message': f"Coze工作流API请求异常: {str(e)}",
                    'type': 'server_error',
                    'code': 'coze_network_error'
                },
                'status_code': 500
            }
        except Exception as e:
            logging.error(f"Coze工作流执行失败: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return {
                'error': {
                    'message': f"Coze工作流执行失败: {str(e)}",
                    'type': 'server_error',
                    'code': 'coze_execution_error'
                },
                'status_code': 500
            }
    
    def _chat_with_bot(self, messages: List[Dict], **kwargs) -> Dict:
        """调用Coze Bot API处理消息"""
        try:
            if not self.bot_id:
                return {
                    'error': {
                        'message': "缺少Coze配置: COZE_BOT_ID",
                        'type': 'server_error',
                        'code': 'missing_bot_id'
                    },
                    'status_code': 500
                }
                
            logging.info(f"开始Coze Bot聊天: bot_id={self.bot_id}")
            
            # 转换消息格式
            coze_messages = []
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content')
                
                # Coze的角色格式与OpenAI兼容，但使用content_type
                coze_messages.append({
                    "role": role,
                    "content": content,
                    "content_type": "text"
                })
            
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建请求体
            payload = {
                "bot_id": self.bot_id,
                "user_id": self.user_id,
                "stream": False,
                "auto_save_history": True,
                "additional_messages": coze_messages
            }
            
            # 如果有会话ID，则使用
            api_url = "https://api.coze.cn/v3/chat"
            conversation_id = kwargs.get('conversation_id')
            if conversation_id:
                api_url = f"{api_url}?conversation_id={conversation_id}"
            
            # 如果有自定义变量，加入请求
            if kwargs.get('custom_variables'):
                payload["custom_variables"] = kwargs.get('custom_variables')
            
            logging.info(f"发送Coze Bot聊天请求: {api_url}")
            
            # 发送请求
            start_time = time.time()
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            end_time = time.time()
            
            # 计算延迟
            latency_ms = int((end_time - start_time) * 1000)
            
            # 检查响应
            if response.status_code != 200:
                return {
                    'error': {
                        'message': f"Coze Bot API请求失败: 状态码={response.status_code}, 响应={response.text}",
                        'type': 'server_error',
                        'code': 'coze_api_error'
                    },
                    'status_code': response.status_code
                }
            
            result_data = response.json()
            
            # 检查API响应状态
            if result_data.get('code') != 0:
                return {
                    'error': {
                        'message': f"Coze Bot API错误: code={result_data.get('code')}, msg={result_data.get('msg', '未知错误')}",
                        'type': 'server_error',
                        'code': 'coze_bot_error'
                    },
                    'status_code': 500
                }
            
            # 获取回复内容
            chat_data = result_data.get('data', {})
            
            # 获取最新回复文本
            reply = ""
            try:
                if 'content' in chat_data:
                    content_obj = chat_data.get('content', {})
                    if isinstance(content_obj, dict) and 'text' in content_obj:
                        reply = content_obj.get('text', '')
            except Exception as e:
                logging.warning(f"提取回复文本失败: {str(e)}")
                reply = "无法获取回复内容"
            
            # 构建OpenAI兼容的响应格式
            result = {
                "id": chat_data.get('id', f"coze-chat-{str(uuid.uuid4())}"),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "coze-bot",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": reply
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": chat_data.get('usage', {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }),
                "server_latency_ms": latency_ms,
                "provider": "coze",
                "conversation_id": chat_data.get('conversation_id'),
                "chat_status": chat_data.get('status')
            }
            
            return result
            
        except requests.RequestException as e:
            return {
                'error': {
                    'message': f"Coze Bot API请求失败: {str(e)}",
                    'type': 'server_error',
                    'code': 'coze_network_error'
                },
                'status_code': 500
            }
        except Exception as e:
            logging.error(f"Coze Bot聊天失败: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return {
                'error': {
                    'message': f"Coze Bot聊天失败: {str(e)}",
                    'type': 'server_error',
                    'code': 'coze_chat_error'
                },
                'status_code': 500
            }
    
    def list_models(self) -> List[Dict]:
        """获取Coze可用模型列表"""
        models = []
        model_ids = current_app.config.get('CHAT_SOURCES', {}).get('coze', {}).get('models', ['coze-rumor-crusher'])
        
        for model_id in model_ids:
            models.append({
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "coze"
            })
        return models 