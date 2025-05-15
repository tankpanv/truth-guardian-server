from minio import Minio
from minio.error import S3Error
import os
import traceback
import logging
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import uuid
from urllib.parse import urljoin

class FileService:
    def __init__(self):
        # 从环境变量获取MinIO配置
        self.access_key = os.getenv('MINIO_ACCESS_KEY')
        self.secret_key = os.getenv('MINIO_SECRET_KEY')
        self.endpoint = os.getenv('MINIO_ENDPOINT')
        self.bucket_name = os.getenv('MINIO_BUCKET_NAME')
        
        # 记录配置信息
        logging.info(f"初始化MinIO服务 - Endpoint: {self.endpoint}, Bucket: {self.bucket_name}")
        
        # 验证配置完整性
        if not all([self.access_key, self.secret_key, self.endpoint, self.bucket_name]):
            missing = []
            if not self.access_key: missing.append('MINIO_ACCESS_KEY')
            if not self.secret_key: missing.append('MINIO_SECRET_KEY')
            if not self.endpoint: missing.append('MINIO_ENDPOINT')
            if not self.bucket_name: missing.append('MINIO_BUCKET_NAME')
            
            error_msg = f"MinIO配置不完整，缺少以下环境变量: {', '.join(missing)}"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # 初始化MinIO客户端
        try:
            # 移除URL中的协议部分
            endpoint = self.endpoint.replace('http://', '').replace('https://', '')
            secure = self.endpoint.startswith('https://')
            
            self.client = Minio(
                endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=secure
            )
            
            # 确保bucket存在
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logging.info(f"创建Bucket: {self.bucket_name}")
            
            logging.info(f"MinIO连接成功 - Bucket: {self.bucket_name}")
        except Exception as e:
            error_msg = f"MinIO初始化失败: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            raise RuntimeError(error_msg)

    def get_file_size(self, file):
        """获取文件大小"""
        try:
            current_pos = file.tell()
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(current_pos)
            return size
        except Exception as e:
            logging.error(f"获取文件大小失败: {str(e)}")
            return 0

    def get_full_url(self, relative_url):
        """将相对路径转换为完整URL"""
        if relative_url.startswith('http://') or relative_url.startswith('https://'):
            return relative_url
        return urljoin(self.endpoint, f"{self.bucket_name}/{relative_url}")

    def save_file(self, file, directory='uploads'):
        """
        保存文件到指定目录
        
        Args:
            file: FileStorage对象
            directory: 保存目录，默认为'uploads'
            
        Returns:
            dict: 包含文件信息的字典
        """
        try:
            # 生成文件名
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"{uuid.uuid4()}{file_ext}"
            
            # 构建MinIO路径
            minio_path = f"{directory}/{new_filename}"
            
            # 获取文件大小和类型
            file_size = self.get_file_size(file)
            content_type = file.content_type or 'application/octet-stream'
            
            # 上传到MinIO
            file.seek(0)  # 确保从文件开始处读取
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=minio_path,
                data=file,
                length=file_size,
                content_type=content_type
            )
            
            # 使用公共URL代替预签名URL
            file_url = self.get_public_url(minio_path)
            
            return {
                'file_name': filename,
                'file_path': minio_path,
                'file_url': file_url,  # 使用公共URL
                'file_size': file_size,
                'file_type': content_type,
                'file_location': 'oss'
            }
            
        except Exception as e:
            logging.error(f"文件上传失败: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def _multipart_upload(self, file_obj, minio_path, file_size, part_size=10*1024*1024):
        """执行分片上传"""
        try:
            # MinIO的Python SDK会自动处理分片上传
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=minio_path,
                data=file_obj,
                length=file_size
            )
            return True
        except Exception as e:
            logging.error(f"分片上传失败: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    def delete_file(self, file_info):
        """删除MinIO文件"""
        if not file_info or file_info.get('file_location') != 'minio':
            return False
        
        try:
            minio_path = file_info.get('file_path')
            if not minio_path:
                return False
            
            self.client.remove_object(self.bucket_name, minio_path)
            return True
            
        except Exception as e:
            logging.error(f"删除MinIO文件失败: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    def get_presigned_url(self, object_name, expires=timedelta(days=1)):
        """获取文件的预签名URL"""
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except Exception as e:
            logging.error(f"生成预签名URL失败: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def get_file_url(self, file_info):
        """获取文件的访问URL"""
        if not file_info:
            return None
        
        try:
            if file_info.get('file_location') == 'minio':
                minio_path = file_info.get('file_path')
                if not minio_path:
                    return None
                
                return self.get_presigned_url(minio_path)
            else:
                return file_info.get('file_url')
                
        except Exception as e:
            logging.error(f"获取文件URL失败: {str(e)}")
            logging.error(traceback.format_exc())
            return None

    def get_public_url(self, object_name):
        """
        生成文件的公共访问URL（不带签名）
        
        Args:
            object_name (str): 对象存储中的文件路径
            
        Returns:
            str: 完整的公共访问URL
        """
        try:
            # 从环境变量获取公共访问域名
            public_domain = os.getenv('MINIO_ENDPOINT', '')
            
            # 构建完整的URL
            public_url = f"{public_domain}/{self.bucket_name}/{object_name}"
            
            logging.info(f"生成公共访问URL: {public_url}")
            return public_url
            
        except Exception as e:
            logging.error(f"生成公共访问URL失败: {str(e)}")
            logging.error(traceback.format_exc())
            return None 