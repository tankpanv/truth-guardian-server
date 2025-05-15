import logging
from typing import Dict, List, Optional
from openai import OpenAI, APIError
from .base import ChatService

logger = logging.getLogger(__name__)

class OpenAIService(ChatService):
    """OpenAI聊天服务实现"""
    
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        初始化OpenAI服务
        
        Args:
            api_key: OpenAI API密钥
            base_url: 可选的API基础URL
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
    def chat_completion(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        执行聊天完成请求
        
        Args:
            messages: 消息列表
            model: 可选的模型名称，默认使用DEFAULT_MODEL
            **kwargs: 其他参数传递给OpenAI API
            
        Returns:
            Dict: {
                'success': bool,
                'message': str,
                'data': Optional[str]
            }
        """
        try:
            response = self.client.chat.completions.create(
                model=model or self.DEFAULT_MODEL,
                messages=messages,
                **kwargs
            )
            
            return {
                'success': True,
                'message': 'Success',
                'data': response.choices[0].message.content
            }
            
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }
            
    def list_models(self) -> Dict:
        """
        获取可用的模型列表
        
        Returns:
            Dict: {
                'success': bool,
                'message': str,
                'data': Optional[List[str]]
            }
        """
        try:
            models = self.client.models.list()
            chat_models = [
                model.id for model in models
                if model.id.startswith(('gpt-3.5', 'gpt-4'))
            ]
            
            if not chat_models:
                return {
                    'success': False,
                    'message': 'No chat models available',
                    'data': None
                }
                
            return {
                'success': True,
                'message': 'Success',
                'data': chat_models
            }
            
        except APIError as e:
            logger.error(f"Failed to list models: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            } 