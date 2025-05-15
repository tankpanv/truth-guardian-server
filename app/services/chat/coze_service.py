import json
import logging
import requests
from typing import Dict, List, Optional
from .base import ChatService

logger = logging.getLogger(__name__)

class CozeService(ChatService):
    """Coze聊天服务实现"""
    
    DEFAULT_MODEL = "gpt-3.5"
    BASE_URL = "https://www.coze.com/api/v1"
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        初始化Coze服务
        
        Args:
            api_key: Coze API密钥
            base_url: 可选的API基础URL
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
    def _call_workflow(self, endpoint: str, data: Dict) -> Dict:
        """
        调用Coze API
        
        Args:
            endpoint: API端点
            data: 请求数据
            
        Returns:
            Dict: API响应
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.post(
                url,
                json=data,
                timeout=600,
                verify=False,
                proxies={'http': None, 'https': None}
            )
            
            if response.status_code != 200:
                logger.error(f"Coze API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'message': f'API error: {response.status_code}',
                    'data': None
                }
                
            result = response.json()
            if not result.get('success'):
                return {
                    'success': False,
                    'message': result.get('message', 'Unknown error'),
                    'data': None
                }
                
            return {
                'success': True,
                'message': 'Success',
                'data': result.get('data', {}).get('content')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {
                'success': False,
                'message': 'Invalid JSON response',
                'data': None
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }
            
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
            **kwargs: 其他参数传递给Coze API
            
        Returns:
            Dict: {
                'success': bool,
                'message': str,
                'data': Optional[str]
            }
        """
        data = {
            'model': model or self.DEFAULT_MODEL,
            'messages': messages,
            **kwargs
        }
        return self._call_workflow('chat/completions', data)
        
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
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=30,
                verify=False,
                proxies={'http': None, 'https': None}
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'API error: {response.status_code}',
                    'data': None
                }
                
            result = response.json()
            if not result.get('success'):
                return {
                    'success': False,
                    'message': result.get('message', 'Unknown error'),
                    'data': None
                }
                
            models = result.get('data', {}).get('models', [])
            if not models:
                return {
                    'success': False,
                    'message': 'No models available',
                    'data': None
                }
                
            return {
                'success': True,
                'message': 'Success',
                'data': models
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {
                'success': False,
                'message': 'Invalid JSON response',
                'data': None
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            } 