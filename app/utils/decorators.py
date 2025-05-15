from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import json
import traceback

def token_required(fn):
    """验证JWT令牌的装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            # 记录当前用户身份信息，便于调试
            current_app.logger.debug(f"Current user identity: {current_user} (Type: {type(current_user)})")
            
            # 将 current_user 传递给被装饰的函数
            return fn(current_user=current_user, *args, **kwargs)
            
        except Exception as e:
            # 捕获所有异常，包括JWT验证过程中的异常
            error_traceback = traceback.format_exc()
            current_app.logger.error(f"Token验证过程中出错: {str(e)}\n{error_traceback}")
            return jsonify({"success": False, "message": "认证失败，请重新登录", "error": str(e)}), 401
            
    return wrapper

def admin_required(fn):
    """确保用户有管理员权限的装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            
            # 记录当前用户身份信息，便于调试
            current_app.logger.debug(f"Current user identity: {current_user} (Type: {type(current_user)})")
            
            # 处理不同格式的 JWT identity
            try:
                # 如果 identity 是字符串，尝试解析 JSON
                if isinstance(current_user, str):
                    try:
                        user_info = json.loads(current_user)
                        if isinstance(user_info, dict) and user_info.get('type') == 'admin':
                            return fn(*args, **kwargs)
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # 如果 identity 直接是字典 (旧格式的JWT)
                elif isinstance(current_user, dict) and current_user.get('type') == 'admin':
                    return fn(*args, **kwargs)
            except Exception as e:
                error_traceback = traceback.format_exc()
                current_app.logger.error(f"验证管理员权限出错: {str(e)}\n{error_traceback}")
                return jsonify({"msg": f"认证失败: {str(e)}", "code": 403}), 403
                
            return jsonify({"msg": "需要管理员权限", "code": 403}), 403
            
        except Exception as e:
            # 捕获所有异常，包括JWT验证过程中的异常
            error_traceback = traceback.format_exc()
            current_app.logger.error(f"认证过程中出错: {str(e)}\n{error_traceback}")
            return jsonify({"msg": "认证过程中出错，请重新登录", "code": 401, "error": str(e)}), 401
            
    return wrapper 