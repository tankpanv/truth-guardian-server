"""
文件上传路由模块
"""
import os
import uuid
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
from ..utils.decorators import token_required
from ..services.oss_service import FileService
from ..services.file_processing_service import FileProcessingService

# 创建蓝图
upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger(__name__)

# 允许的文件类型及其MIME类型
ALLOWED_EXTENSIONS = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'txt': 'text/plain',
    'zip': 'application/zip',
    'rar': 'application/x-rar-compressed',
    'mp4': 'video/mp4',
    'mp3': 'audio/mpeg'
}

def allowed_file(filename):
    """检查文件类型是否允许上传"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/api/upload/file', methods=['POST'])
@token_required
@swag_from({
    'tags': ['文件上传'],
    'summary': '上传文件',
    'description': '上传文件到服务器',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'JWT Token'
        },
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': '要上传的文件'
        },
        {
            'name': 'directory',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': '可选的子目录，用于组织文件'
        }
    ],
    'responses': {
        200: {
            'description': '上传成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'description': '是否成功'
                    },
                    'file_url': {
                        'type': 'string',
                        'description': '文件URL'
                    },
                    'file_name': {
                        'type': 'string',
                        'description': '文件名'
                    },
                    'file_size': {
                        'type': 'integer',
                        'description': '文件大小（字节）'
                    },
                    'content_type': {
                        'type': 'string',
                        'description': '文件MIME类型'
                    }
                }
            }
        },
        400: {
            'description': '请求错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'message': {
                        'type': 'string'
                    }
                }
            }
        },
        401: {
            'description': '未授权',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'message': {
                        'type': 'string',
                        'example': '未授权'
                    }
                }
            }
        },
        500: {
            'description': '服务器错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'message': {
                        'type': 'string'
                    }
                }
            }
        }
    }
})
def upload_file(current_user):
    """
    上传文件处理
    
    参数:
        current_user: 当前登录用户
        
    返回:
        JSON响应
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未找到文件'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择文件'
            }), 400
        
        # 检查文件类型是否允许
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': '文件类型不允许'
            }), 400
        
        # 获取可选的目录参数
        directory = request.form.get('directory', 'uploads')
        
        # 使用文件处理服务进行上传
        file_service = FileService()
        result = file_service.save_file(file, directory)
        
        if not result:
            return jsonify({
                'success': False,
                'message': '文件上传失败'
            }), 500
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'file_url': result['file_url'],
            'file_name': result['file_name'],
            'file_size': result['file_size'],
            'content_type': result['file_type']
        }), 200
        
    except Exception as e:
        logger.error(f"文件上传出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500

@upload_bp.route('/api/upload/file/<path:file_url>', methods=['DELETE'])
@token_required
@swag_from({
    'tags': ['文件上传'],
    'summary': '删除上传的文件',
    'description': '根据文件URL删除已上传的文件',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'JWT Token'
        },
        {
            'name': 'file_url',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': '要删除的文件URL'
        }
    ],
    'responses': {
        200: {
            'description': '删除成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': True
                    },
                    'message': {
                        'type': 'string',
                        'example': '文件已成功删除'
                    }
                }
            }
        },
        400: {
            'description': '请求错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'message': {
                        'type': 'string'
                    }
                }
            }
        },
        401: {
            'description': '未授权',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'message': {
                        'type': 'string',
                        'example': '未授权'
                    }
                }
            }
        },
        500: {
            'description': '服务器错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'message': {
                        'type': 'string'
                    }
                }
            }
        }
    }
})
def delete_uploaded_file(current_user, file_url):
    """
    删除上传的文件
    
    参数:
        current_user: 当前登录用户
        file_url: 文件URL路径
        
    返回:
        JSON响应
    """
    try:
        # 从URL中提取文件路径
        file_path = file_url.split('/')[-1] if '/' in file_url else file_url
        
        # 创建模拟的文件信息对象
        file_info = {
            'file_location': 'minio',
            'file_path': file_path
        }
        
        # 使用文件服务删除文件
        file_service = FileService()
        result = file_service.delete_file(file_info)
        
        if result:
            return jsonify({
                'success': True,
                'message': '文件已成功删除'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '文件删除失败'
            }), 500
            
    except Exception as e:
        logger.error(f"文件删除出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500

@upload_bp.route('/local', methods=['POST'])
@token_required
@swag_from({
    'tags': ['文件上传'],
    'summary': '上传文件到本地',
    'description': '上传文件到服务器本地目录',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'JWT Token'
        },
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': '要上传的文件'
        }
    ],
    'responses': {
        200: {
            'description': '上传成功',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'description': '是否成功'
                    },
                    'file_path': {
                        'type': 'string',
                        'description': '文件相对路径'
                    },
                    'file_name': {
                        'type': 'string',
                        'description': '文件名'
                    },
                    'file_size': {
                        'type': 'integer',
                        'description': '文件大小（字节）'
                    }
                }
            }
        },
        400: {
            'description': '请求错误',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {
                        'type': 'boolean',
                        'example': False
                    },
                    'message': {
                        'type': 'string'
                    }
                }
            }
        }
    }
})
def upload_local_file(current_user):
    """
    上传文件到本地目录
    
    参数:
        current_user: 当前登录用户
        
    返回:
        JSON响应，包含文件相对路径
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未找到文件'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择文件'
            }), 400
        
        # 检查文件类型是否允许
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': '文件类型不允许'
            }), 400
            
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 确保上传目录存在
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            
        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 生成相对路径 - 移除/static前缀
        relative_path = f"/uploads/{unique_filename}"
        
        return jsonify({
            'success': True,
            'file_path': relative_path,  # 前端使用时直接拼接: ${serverUrl}${file_path}
            'file_name': filename,
            'file_size': file_size
        }), 200
        
    except Exception as e:
        logger.error(f"本地文件上传出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500

def init_app(app):
    """初始化应用，注册蓝图"""
    app.register_blueprint(upload_bp) 