"""应用工厂模块

创建并配置 Flask 应用
"""

import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from flasgger import LazyJSONEncoder
from dotenv import load_dotenv
import json
import logging
import subprocess
from flask_caching import Cache
from flask import Blueprint
from flask_mail import Mail
from app.extensions import db, migrate, cors, jwt, swagger, init_extensions
from app.config import config_by_name, get_env
from app.routes.auth import auth_bp
from app.routes.im import im_bp
from app.websockets import init_websocket

# 从config模块获取环境
env = get_env()
print(f"----- 当前运行环境: {env} -----")

# 创建缓存对象
cache = Cache(config={
    'CACHE_TYPE': 'simple'  # 使用简单的内存缓存
})

# 从extensions模块导入扩展
from app.extensions import db, migrate, cors, jwt, init_extensions

def create_app(config_name=None):
    """创建 Flask 应用
    
    Args:
        config_name: 配置名称
        
    Returns:
        Flask 应用实例
    """
    if not config_name:
        config_name = env
        
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config_by_name[config_name])
    config_by_name[config_name].init_app(app)
    
    # 初始化所有扩展
    init_extensions(app)
    
    # 初始化 WebSocket
    init_websocket(app)
    
    # 注册前端页面蓝图
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 确保这些设置正确
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_MIMETYPE'] = "application/json;charset=utf-8"
    app.json.ensure_ascii = False
    
    # 初始化缓存
    cache.init_app(app)

    # 用户身份加载器
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """确保返回的identity是字符串类型"""
        try:
            # 如果是用户对象，将其转换为字典再序列化为字符串
            if hasattr(user, 'id'):
                return json.dumps({"type": "admin", "id": user.id})
            # 如果已经是字典，也序列化为字符串
            if isinstance(user, dict):
                return json.dumps(user)
            # 如果是其他类型，确保转换为字符串
            return str(user)
        except Exception as e:
            # 出现任何错误，提供一个默认的字符串
            print(f"用户身份序列化错误: {str(e)}")
            return "anonymous"

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """从JWT数据中解析identity还原用户信息"""
        from app.models.user import User
        from app.models.wx_user import WxUser
        
        identity = jwt_data["sub"]
        # 如果identity已经是字典(旧格式的JWT)，直接使用
        if isinstance(identity, dict):
            user_type = identity.get('type', 'admin')  # 默认为admin类型
            user_id = identity.get('id')
            
            if user_id:
                if user_type == 'wx_user':
                    return WxUser.query.get(user_id)
                else:
                    return User.query.get(user_id)
                
        # 尝试解析JSON字符串
        elif isinstance(identity, str):
            try:
                # 处理可能被二次转义的JSON字符串
                if identity.startswith('"') and identity.endswith('"'):
                    identity = identity[1:-1]
                
                # 解析identity字符串
                user_info = json.loads(identity.replace('\\', ''))
                
                if isinstance(user_info, dict):
                    user_id = user_info.get('id')
                    user_type = user_info.get('type', 'admin')  # 默认为admin类型
                    
                    if user_id:
                        if user_type == 'wx_user':
                            return WxUser.query.get(user_id)
                        else:
                            return User.query.get(user_id)
            except Exception as e:
                app.logger.error(f"JSON解析错误: {str(e)}, identity: {identity}")
                # 如果identity是单个数字ID，可能是老版本的token
                try:
                    user_id = int(identity)
                    return User.query.get(user_id)
                except (ValueError, TypeError):
                    pass
            
        app.logger.error(f"用户查找失败, identity: {identity}")
        return None
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        """处理无效Token的情况，包括解码错误"""
        return jsonify({
            'message': 'Token无效',
            'error': str(error_string),
            'code': 401
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """处理Token过期的情况"""
        return jsonify({
            'message': 'Token已过期',
            'error': '请重新登录或刷新Token',
            'code': 401
        }), 401

    # 添加JWT通用错误处理
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        """处理缺少Token的情况"""
        return jsonify({
            'message': '缺少认证Token',
            'error': str(error_string),
            'code': 401
        }), 401
    
    # 注册蓝图
    with app.app_context():
        # 注册测试路由（仅用于确认部署环境）
        if app.config.get('SERVER_ENV') == 'dev':
            from app.routes.test import test_bp
            app.register_blueprint(test_bp)
        
        # 注册认证相关蓝图
        from app.routes.auth import authapi_bp
        app.register_blueprint(authapi_bp)  # 不需要指定 url_prefix，因为已经在蓝图定义时指定了
        
        # 注册IM消息蓝图
        app.register_blueprint(im_bp, url_prefix='/api/im')
        
        # 注册辟谣相关蓝图
        from app.routes.debunk import debunk_bp, debunk_view_bp
        app.register_blueprint(debunk_bp, url_prefix='/api/debunk')
        app.register_blueprint(debunk_view_bp)
        
        # 注册聊天API蓝图
        from app.routes.chat import chat_bp
        app.register_blueprint(chat_bp)  # 移除url_prefix，因为已经在蓝图定义中指定了
        
        # 注册文件上传API蓝图
        from app.routes.upload import upload_bp
        app.register_blueprint(upload_bp, url_prefix='/api/upload')
        
        # 注册AI助手蓝图
        from app.routes.ai_assistant import ai_assistant_bp
        app.register_blueprint(ai_assistant_bp)

        # 注册可视化蓝图
        from app.routes.visualization import visualization_bp
        app.register_blueprint(visualization_bp, url_prefix='/api')
        
        from app.routes.migration import migration_bp
        app.register_blueprint(migration_bp, url_prefix='/api/migration')        
        

        # 注册爬虫数据蓝图
        from app.routes.spider_data import spider_bp
        app.register_blueprint(spider_bp)  # 不需要指定url_prefix，因为已经在蓝图定义时指定了
        
        from app.routes.analysis import analysis_bp
        app.register_blueprint(analysis_bp)
        
        # 导入所有模型
        from app.models.user import User
        from app.models.debunk import DebunkArticle, RumorReport, ClarificationReport
        from app.models.message import Message  # 添加消息模型导入

        # 注释掉或删除 db.create_all() 调用
        # db.create_all()  # 删除或注释这行
        
        # 首页路由
        @app.route('/')
        def index():
            return render_template('index.html')
            
        # 添加 favicon.ico 路由，避免 404 错误
        @app.route('/favicon.ico')
        def favicon():
            return '', 204  # 返回空响应，状态码 204 No Content
        
        # 修改全局错误处理
        @app.errorhandler(Exception)
        def handle_exception(e):
            """全局异常处理"""
            # 记录异常详情
            app.logger.error(f"未捕获异常: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc())
            
            # 返回统一的错误响应
            return jsonify({
                "code": 500,
                "message": "服务器内部错误",
                "error": str(e)
            }), 500, {'Content-Type': 'application/json;charset=utf-8'}

        # 打印注册的路由
        print("已注册的路由：")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint}: {rule.rule}")

        # 在 create_app 函数中添加
        @app.after_request
        def after_request(response):
            if response.mimetype == 'application/json':
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response

        # 管理员认证系统页面
        @app.route('/admin')
        def admin():
            return render_template('admin/index.html')
        
        # 辟谣文章管理系统页面
        @app.route('/debunk')
        def debunk_page():
            return render_template('debunk/index.html')
        
        # 辟谣文章列表页面
        @app.route('/debunk/articles')
        def debunk_articles():
            return render_template('debunk/article_list.html')
        
        # 辟谣文章详情页面
        @app.route('/debunk/articles/<int:article_id>')
        def debunk_article_detail(article_id):
            return render_template('debunk/article_detail.html')
        
        # 辟谣文章创建页面
        @app.route('/debunk/create')
        def debunk_create():
            return render_template('debunk/article_create.html')
        
        # 辟谣文章编辑页面
        @app.route('/debunk/edit/<int:article_id>')
        def debunk_edit(article_id):
            return render_template('debunk/article_edit.html')

        # 添加WebSocket测试页面路由
        @app.route('/websocket-test')
        def websocket_test():
            return render_template('websocket_test.html')

        # 添加静态文件访问路由
        @app.route('/uploads/<path:filename>')
        def uploaded_file(filename):
            return send_from_directory(os.path.join(app.root_path, 'static', 'uploads'), filename)

    return app 