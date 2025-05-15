from flask import jsonify, current_app

def make_response(data=None, message="成功", code=0):
    """
    统一的响应格式
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 响应代码，0表示成功，其他值表示错误
        
    Returns:
        JSON响应
    """
    response = {
        "code": code,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
        
    # 确保中文正常显示
    return jsonify(response), 200, {'Content-Type': 'application/json;charset=utf-8'}

def make_error(message="操作失败", code=500, error=None):
    """
    统一的错误响应格式
    
    Args:
        message: 错误消息
        code: 错误代码
        error: 详细错误信息
        
    Returns:
        JSON响应
    """
    response = {
        "code": code,
        "message": message
    }
    
    if error:
        response["error"] = str(error)
        
    # 确保中文正常显示
    return jsonify(response), code, {'Content-Type': 'application/json;charset=utf-8'} 