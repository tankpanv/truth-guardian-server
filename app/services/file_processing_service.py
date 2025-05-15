"""
文件处理服务模块
"""
import os
import logging
import hashlib
import mimetypes
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from app.services.oss_service import FileService

logger = logging.getLogger(__name__)

class FileProcessingService:
    """文件处理服务类"""
    
    def __init__(self, oss_service: FileService = None):
        self.oss_service = oss_service or FileService()
        
    def process_upload(self, file_data: bytes, file_name: str, 
                     content_type: str = None) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Args:
            file_data: 文件二进制数据
            file_name: 原始文件名
            content_type: 文件内容类型
            
        Returns:
            Dict: 包含处理结果的字典
        """
        try:
            # 生成文件哈希
            file_hash = self._generate_file_hash(file_data)
            
            # 获取或确定内容类型
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # 准备存储的文件名
            file_extension = os.path.splitext(file_name)[1].lower()
            if not file_extension and content_type:
                # 从内容类型猜测扩展名
                extension = mimetypes.guess_extension(content_type)
                if extension:
                    file_extension = extension
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_file_name = f"{timestamp}_{file_hash[:8]}{file_extension}"
            
            # 创建可用于 minio.put_object 的类似文件对象
            from io import BytesIO
            file_obj = BytesIO(file_data)
            file_obj.filename = unique_file_name
            file_obj.content_type = content_type
            
            # 上传到 OSS
            result = self.oss_service.save_file(file_obj)
            
            if not result or not result.get('file_url'):
                return {
                    "success": False,
                    "error": "文件上传失败"
                }
            
            # 返回处理结果
            return {
                "success": True,
                "file_name": unique_file_name,
                "original_name": file_name,
                "file_url": result['file_url'],
                "content_type": content_type,
                "file_size": len(file_data),
                "file_hash": file_hash
            }
            
        except Exception as e:
            logger.error(f"处理上传文件失败: {str(e)}")
            return {
                "success": False,
                "error": f"处理文件时出错: {str(e)}"
            }
    
    def delete_file(self, file_url: str) -> bool:
        """
        删除文件
        
        Args:
            file_url: 文件URL
            
        Returns:
            bool: 删除是否成功
        """
        if not file_url:
            return False
        
        try:
            # 创建一个模拟的文件信息对象
            file_info = {
                'file_location': 'minio',
                'file_path': file_url.split('/')[-1] if '/' in file_url else file_url
            }
            return self.oss_service.delete_file(file_info)
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False
    
    def _generate_file_hash(self, file_data: bytes) -> str:
        """生成文件的SHA-256哈希值"""
        return hashlib.sha256(file_data).hexdigest()
    
    def validate_file_type(self, file_data: bytes, file_name: str, 
                         allowed_types: list = None) -> Tuple[bool, str]:
        """
        验证文件类型
        
        Args:
            file_data: 文件二进制数据
            file_name: 文件名
            allowed_types: 允许的MIME类型列表
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        if not allowed_types:
            # 默认允许常见的图像、文档和音视频类型
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/plain', 'text/csv',
                'video/mp4', 'audio/mpeg'
            ]
        
        # 从文件名猜测MIME类型
        content_type, _ = mimetypes.guess_type(file_name)
        
        # 如果无法从文件名判断类型，尝试从文件头判断
        if not content_type:
            # 这里可以扩展实现更复杂的文件魔术字节检测
            # 简单起见，目前仅依赖于文件扩展名
            content_type = "application/octet-stream"
        
        # 检查是否在允许的类型列表中
        if content_type not in allowed_types:
            return False, f"不支持的文件类型: {content_type}"
        
        return True, "" 