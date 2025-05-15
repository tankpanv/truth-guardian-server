"""Flask扩展模块

初始化和配置所有Flask扩展
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger, LazyJSONEncoder

# 初始化SQLAlchemy，用于数据库操作
db = SQLAlchemy()

# 初始化Migrate，用于数据库迁移
migrate = Migrate()

# 初始化CORS，用于跨域资源共享
cors = CORS()

# 初始化JWT，用于身份认证
jwt = JWTManager()

# Swagger配置
swagger_config = {
    "headers": [],
    "specs": [{
        "endpoint": 'apispec',
        "route": '/apispec.json',
        "rule_filter": lambda rule: True,
        "model_filter": lambda tag: True,
    }],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Truth Guardian API",
        "description": "谣言监测与辟谣系统API",
        "version": "1.0.0"
    },
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        }
    }
}

# 初始化Swagger，用于API文档
swagger = Swagger(template=swagger_template, config=swagger_config)

def init_extensions(app):
    """初始化所有Flask扩展
    
    Args:
        app: Flask应用实例
    """
    # 配置JSON编码器
    app.json_encoder = LazyJSONEncoder
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化迁移
    migrate.init_app(app, db)
    
    # 初始化CORS
    cors.init_app(app)
    
    # 初始化JWT
    jwt.init_app(app)
    
    # 初始化Swagger
    swagger.init_app(app) 