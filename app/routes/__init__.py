"""路由包

包含所有API路由和页面路由
"""

from .auth import auth_bp, authapi_bp
from .debunk import debunk_bp, debunk_view_bp
from .chat import chat_bp
from .upload import upload_bp
from .ai_assistant import ai_assistant_bp
from .visualization import visualization_bp
from .analysis import analysis_bp
__all__ = [
    'auth_bp',
    'authapi_bp',
    'debunk_bp',
    'analysis_bp',
    'debunk_view_bp',
    'chat_bp',
    'upload_bp',
    'ai_assistant_bp',
    'visualization_bp'
] 