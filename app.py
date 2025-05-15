import json
import traceback
import uuid
from flask import Flask, jsonify, request
from hashlib import pbkdf2_hmac
import os
import binascii
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, timedelta
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    create_refresh_token
)
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from flask_migrate import Migrate
from flasgger import Swagger, swag_from
from enum import Enum
from functools import wraps
import oss2
import qrcode
from io import BytesIO
from urllib.parse import quote
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image  # 确保可以导入
# 加载 .env 文件（默认加载项目根目录下的 .env）
load_dotenv()  # 如果 .env 在其他路径，使用 load_dotenv('path/to/.env')

# ========== 初始化应用 ==========
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://truetuardian:truetuardian123456@192.168.1.114/truetuardian'
# 修改后的数据库引擎配置
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 290,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True  # 添加预检选项
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-super-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['SWAGGER'] = {
    'openapi': '3.0.3',
    'components': {
        'schemas': {
          
            'ErrorResponse': {
                'type': 'object',
                'properties': {
                    'code': {'type': 'integer'},
                    'message': {'type': 'string'}
                }
            }
        },
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT'
            }
        }
    }
}

CORS(app, resources={r"/api/*": {"origins": "*"}})

# 初始化扩展
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

# ========== Swagger配置 ==========
template = {
  "info": {
    "title": "图书管理系统API",
    "description": "支持图书资源批量上传管理",
    "version": "1.0.0"
  },
  "components": {
    "schemas": {
      "Book": {
        "type": "object",
        "properties": {
          "id": {"type": "string", "example": "550e8400-e29b-41d4-a716-446655440000"},
          "title": {"type": "string", "example": "深入浅出Python"},
          "type": {"type": "string", "enum": ["book", "audio", "video"]},
          "qrcode_url": {"type": "string", "format": "url"},
          "created_at": {"type": "string", "format": "date-time"}
        }
      },
      "UploadTask": {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "example": "550e8400-e29b-41d4-a716-446655440000"},
            "task_name": {"type": "string", "example": "2023年度图书上传"},
            "status": {"type": "string", "enum": ["processing", "success", "failed"]},
            "created_at": {"type": "string", "format": "date-time"}
        }
      },
      "UploadTaskDetail": {
        "allOf": [
            {"$ref": "#/components/schemas/UploadTask"},
            {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "book_id": {"type": "string"}
                            }
                        }
                    }
                }
            }
        ]
      },
      "ErrorResponse": {
        "type": "object",
        "properties": {
            "code": {"type": "integer", "example": 404},
            "message": {"type": "string", "example": "Resource not found"}
        }
      }
    }
  }
}
swagger = Swagger(app, template=template)

# ========== 枚举定义 ==========
class BookType(Enum):
    BOOK = 'book'
    AUDIO = 'audio'
    VIDEO = 'video'

class UploadStatus(Enum):
    PROCESSING = 'processing'
    SUCCESS = 'success'
    FAILED = 'failed'

# ========== 数据模型层 ==========
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    user_name = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        salt = os.urandom(16)
        key = pbkdf2_hmac(
            hash_name='sha256',
            password=password.encode('utf-8'),
            salt=salt,
            iterations=100000,
            dklen=32
        )
        self.password_hash = f"{binascii.hexlify(salt).decode()}:{binascii.hexlify(key).decode()}"

    def check_password(self, password):
        salt, stored_key = self.password_hash.split(':')
        salt = binascii.unhexlify(salt.encode())
        stored_key = binascii.unhexlify(stored_key.encode())
        new_key = pbkdf2_hmac(
            hash_name='sha256',
            password=password.encode('utf-8'),
            salt=salt,
            iterations=100000,
            dklen=32
        )
        return new_key == stored_key

class UploadTask(db.Model):
    __tablename__ = 'upload_tasks'
    task_id = db.Column(db.String(36), primary_key=True)
    task_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(UploadStatus), default=UploadStatus.PROCESSING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    files = db.relationship('TaskFile', backref='task', lazy=True)

    def to_dict(self, with_files=False):
        data = {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat()
        }
        if with_files:
            data['files'] = [f.to_dict() for f in self.files]
        return data

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum(BookType), nullable=False)
    oss_path = db.Column(db.String(512), nullable=False)
    qrcode_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "oss_path": self.oss_path,
            "qrcode_url": self.qrcode_url,
            "created_at": self.created_at.isoformat()
        }

class TaskFile(db.Model):
    __tablename__ = 'task_files'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36), db.ForeignKey('upload_tasks.task_id'))
    book_id = db.Column(db.String(36), db.ForeignKey('books.id'))

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "book_id": self.book_id
        }

# ========== JWT 回调函数 ==========
@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.id)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return db.session.get(User, int(identity))  # 使用 db.session.get

# ========== 权限装饰器 ==========
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = db.session.get(User, int(get_jwt_identity()))  # 修改这里
        if current_user.role != 'admin':
            return jsonify({"code": 403, "message": "权限不足"}), 403
        return fn(*args, **kwargs)
    return wrapper

# ========== 认证接口 ==========
@app.route('/api/register', methods=['POST'])
@swag_from({
    'tags': ['用户管理'],
    'summary': '用户注册',
    'requestBody': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'user_name': {'type': 'string'},
                        'password': {'type': 'string'},
                        'name': {'type': 'string'},
                        'phone': {'type': 'string'}
                    },
                    'required': ['user_name', 'password', 'name']
                }
            }
        }
    },
    'responses': {
        201: {
            'description': '注册成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'msg': {'type': 'string'},
                            'user_id': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
})
def register():
    data = request.get_json()
    required_fields = ['user_name', 'password', 'name']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "message": "缺少必填字段"}), 400

    if User.query.filter_by(user_name=data['user_name']).first():
        return jsonify({"code": 409, "message": "用户名已存在"}), 409

    try:
        new_user = User(
            user_name=data['user_name'],
            name=data['name'],
            phone=data.get('phone')
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "用户注册成功", "user_id": new_user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
@swag_from({
    'tags': ['用户认证'],
    'summary': '用户登录',
    'requestBody': {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'user_name': {'type': 'string'},
                        'password': {'type': 'string'}
                    },
                    'required': ['user_name', 'password']
                }
            }
        }
    },
    'responses': {
        200: {
            'description': '登录成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'access_token': {'type': 'string'},
                            'refresh_token': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def login():
    data = request.get_json()
    username = data.get('user_name')
    password = data.get('password')

    if not username or not password:
        return jsonify({"code": 400, "message": "需要用户名和密码"}), 400

    user = User.query.filter_by(user_name=username).first()
    if not user or not user.check_password(password):
        return jsonify({"code": 401, "message": "用户名或密码错误"}), 401

    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    return jsonify(access_token=access_token, refresh_token=refresh_token), 200

@app.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
@swag_from({
    'tags': ['用户认证'],
    'summary': '刷新访问令牌',
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {
            'description': '令牌刷新成功',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'access_token': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
})
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_token), 200
def sanitize_filename(filename):
    # 移除路径分隔符并编码特殊字符
    return quote(filename.replace('/', '_').replace('\\', '_'))
# ========== 受保护接口 ==========
class OSSService:
    def __init__(self):
                # 从环境变量获取配置并校验
        self.access_key = os.getenv('OSS_ACCESS_KEY')
        self.secret_key = os.getenv('OSS_SECRET_KEY')
        self.endpoint = os.getenv('OSS_ENDPOINT')
        self.bucket_name = os.getenv('OSS_BUCKET_NAME')
        print('self.access_key',self.access_key,self.bucket_name,self.secret_key,self.endpoint)

        
        if not all([self.access_key, self.secret_key, self.endpoint, self.bucket_name]):
            raise ValueError("阿里云 OSS 配置不完整，请检查环境变量")
        self.auth = oss2.Auth(os.getenv('OSS_ACCESS_KEY'), os.getenv('OSS_SECRET_KEY'))
        
        self.auth = oss2.Auth(self.access_key, self.secret_key)
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
       
    
    def generate_presigned_url(self, object_key, expiration=3600*24*365*10):
        return self.bucket.sign_url('GET', object_key, expiration)

@app.route('/api/books/upload', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['图书管理'],
    'description': '上传书籍文件',
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'qrcode_url': {'type': 'string'}
                }
            }
        }
    }
})
def upload_book():
    try:
        # ===== 1. 校验基本字段 =====
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400
        file = request.files['file']
        
        title = request.form.get('title', '').strip()
        book_id = request.form.get('book_id', '').strip()
        if not title or not book_id:
            return jsonify({'error': '标题和书籍ID不能为空'}), 400

        # ===== 2. 处理文件名 =====
        filename = sanitize_filename(file.filename)
        if not filename:
            return jsonify({'error': '无效文件名'}), 400

        # ===== 3. 校验文件类型 =====
        file_type = _get_file_type(filename)
        if not file_type:
            return jsonify({'error': '不支持的文件类型'}), 400

        # # ===== 4. 检查书籍ID唯一性 =====
        # existing_book = db.session.get(Book, book_id)
        # if existing_book:
        #     return jsonify({'error': '书籍ID已存在'}), 409

        # ===== 5. 上传到OSS =====
        oss_service = OSSService()
        oss_path = f"books/{book_id}/{filename}"
        
        try:
            oss_service.bucket.put_object(oss_path, file)
        except oss2.exceptions.OssError as e:
            return jsonify({'error': f'文件上传失败: {str(e)}'}), 500

        # ===== 6. 生成下载链接 =====
        download_url = oss_service.generate_presigned_url(oss_path)
        if not download_url:
            return jsonify({'error': '生成下载链接失败'}), 500
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(download_url)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # 将二维码图像保存到缓冲区
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)  # 重置指针位置
        # ===== 7. 生成二维码并上传 =====
       
        
        qr_path = f"qrcodes/{book_id}.png"
        try:
            oss_service.bucket.put_object(qr_path, qr_buffer.getvalue())
        except oss2.exceptions.OssError as e:
            return jsonify({'error': f'二维码上传失败: {str(e)}'}), 500

        # ===== 8. 生成二维码链接 =====
        qrcode_url = oss_service.generate_presigned_url(qr_path)
        if not qrcode_url:
            return jsonify({'error': '生成二维码链接失败'}), 500

        # ===== 9. 写入数据库 =====
        new_book = Book(
            id=book_id,
            title=title,
            type=file_type.value,
            oss_path=oss_path,
            qrcode_url=qrcode_url
        )
        db.session.add(new_book)
        db.session.commit()

        return jsonify(message='上传成功', qrcode_url=qrcode_url)

    except Exception as e:
        db.session.rollback()
        print(f"严重错误: {traceback.format_exc()}")  # 打印完整堆栈
        return jsonify(error="服务器内部错误"), 500

@app.route('/api/books/batch-upload', methods=['POST'])
@jwt_required()
@admin_required
@swag_from({
    'tags': ['图书管理'],
    'description': '批量上传书籍',
    'security': [{'BearerAuth': []}],
    'responses': {
        202: {
            'schema': {
                'type': 'object',
                'properties': {
                    'task_id': {'type': 'string'},
                    'status_url': {'type': 'string'}
                }
            }
        }
    }
})
def batch_upload():
    try:
        excel_file = request.files['file']
        task_id = str(uuid.uuid4())
        
        new_task = UploadTask(
            task_id=task_id,
            task_name=f"Batch Upload {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            status=UploadStatus.PROCESSING
        )
        db.session.add(new_task)
        db.session.commit()
        
        # 异步处理逻辑需自行实现
        # process_excel.delay(excel_file.read(), task_id)
        
        return jsonify(task_id=task_id, status_url=f'/api/upload-tasks/{task_id}'), 202
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@app.route('/api/upload-tasks', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['上传任务'],
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {
            'schema': {
                'type': 'object',
                'properties': {
                    'tasks': {
                        'type': 'array',
                        'items': {'$ref': '#/components/schemas/UploadTask'}
                    },
                    'pagination': {
                        'type': 'object',
                        'properties': {
                            'total': {'type': 'integer'},
                            'page': {'type': 'integer'},
                            'per_page': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
})
def get_upload_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = UploadTask.query.paginate(page=page, per_page=per_page)
    return jsonify({
        'tasks': [task.to_dict() for task in pagination.items],
        'pagination': {
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page
        }
    })

@app.route('/api/upload-tasks/<string:task_id>', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['上传任务'],
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {'$ref': '#/components/schemas/UploadTaskDetail'},
        404: {'$ref': '#/components/schemas/ErrorResponse'}
    }
})
def get_upload_task(task_id):
    task = UploadTask.query.get_or_404(task_id)
    return jsonify(task.to_dict(with_files=True))

@app.route('/api/upload-tasks/<string:task_id>', methods=['PUT'])
@jwt_required()
@admin_required
@swag_from({
    'tags': ['上传任务'],
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {'$ref': '#/components/schemas/UploadTask'},
        404: {'$ref': '#/components/schemas/ErrorResponse'}
    }
})
def update_upload_task(task_id):
    task = UploadTask.query.get_or_404(task_id)
    data = request.get_json()
    
    if 'task_name' in data:
        task.task_name = data['task_name']
    if 'status' in data:
        task.status = UploadStatus(data['status'])
    
    db.session.commit()
    return jsonify(task.to_dict())

@app.route('/api/upload-tasks/<string:task_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@swag_from({
    'tags': ['上传任务'],
    'security': [{'BearerAuth': []}],
    'responses': {
        204: {'description': '删除成功'},
        404: {'$ref': '#/components/schemas/ErrorResponse'}
    }
})
def delete_upload_task(task_id):
    task = UploadTask.query.get_or_404(task_id)
    TaskFile.query.filter_by(task_id=task_id).delete()
    db.session.delete(task)
    db.session.commit()
    return '', 204

@app.route('/api/books', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['图书管理'],
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/components/schemas/Book'}
            }
        }
    }
})
def get_books():
    query = Book.query
    if book_type := request.args.get('type'):
        query = query.filter(Book.type == book_type)
    if search := request.args.get('q'):
        query = query.filter(Book.title.ilike(f'%{search}%'))
    books = query.order_by(Book.created_at.desc()).all()
    return jsonify([book.to_dict() for book in books])

@app.route('/api/books/<string:book_id>', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['图书管理'],
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {'$ref': '#/components/schemas/Book'},
        404: {'$ref': '#/components/schemas/ErrorResponse'}
    }
})
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify(book.to_dict())

@app.route('/api/books/<string:book_id>', methods=['PUT'])
@jwt_required()
@admin_required
@swag_from({
    'tags': ['图书管理'],
    'security': [{'BearerAuth': []}],
    'responses': {
        200: {'$ref': '#/components/schemas/Book'},
        404: {'$ref': '#/components/schemas/ErrorResponse'}
    }
})
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()
    
    if 'title' in data:
        book.title = data['title']
    
    db.session.commit()
    return jsonify(book.to_dict())

@app.route('/api/books/<string:book_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@swag_from({
    'tags': ['图书管理'],
    'security': [{'BearerAuth': []}],
    'responses': {
        204: {'description': '删除成功'},
        404: {'$ref': '#/components/schemas/ErrorResponse'}
    }
})
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    oss_service = OSSService()
    
    try:
        oss_service.bucket.delete_object(book.oss_path)
        oss_service.bucket.delete_object(book.qrcode_url.split('/')[-1])
        db.session.delete(book)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

def _get_file_type(filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['pdf', 'epub', 'txt']:
        return BookType.BOOK
    elif ext in ['mp3', 'wav']:
        return BookType.AUDIO
    elif ext in ['mp4', 'mov']:
        return BookType.VIDEO
    return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002)