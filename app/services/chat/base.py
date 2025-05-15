from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class ChatService(ABC):
    """聊天服务基类"""
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        聊天完成接口
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "消息内容"}, ...]
            model: 可选的模型名称
            **kwargs: 其他参数
            
        Returns:
            Dict: 响应数据，格式为:
            {
                "id": str,
                "object": "chat.completion",
                "created": int,
                "model": str,
                "choices": [{
                    "index": int,
                    "message": {
                        "role": str,
                        "content": str
                    },
                    "finish_reason": str
                }],
                "usage": {
                    "prompt_tokens": int,
                    "completion_tokens": int,
                    "total_tokens": int
                }
            }
            
            或错误响应:
            {
                "error": {
                    "message": str,
                    "type": str,
                    "code": str
                },
                "status_code": int
            }
        """
        pass
        
    @abstractmethod
    def list_models(self) -> List[Dict]:
        """
        获取可用模型列表
        
        Returns:
            List[Dict]: 模型列表，格式为:
            [{
                "id": str,
                "name": str,
                "created": int,
                "owned_by": str
            }]
        """
        pass 