import os
from datetime import timedelta
from dotenv import load_dotenv

# --- 环境特定 .env 文件加载 ---
# 确定环境
env = os.getenv('SERVER_ENV', 'dev').lower()
print(f"----- 配置环境: {env} -----")

# 构造 .env 文件路径
base_dir = os.path.abspath(os.path.dirname(__file__))
project_dir = os.path.join(base_dir, '..')

# 根据环境选择 .env 文件
if env == 'prod':
    dotenv_path = os.path.join(project_dir, '.env_prod')
else:
    dotenv_path = os.path.join(project_dir, '.env')

# 加载环境变量
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, override=True)
    print(f"----- 已加载环境变量文件: {dotenv_path} -----")
else:
    print(f"----- 警告: 环境变量文件不存在: {dotenv_path} -----")
    # 尝试加载默认 .env
    default_path = os.path.join(project_dir, '.env')
    if os.path.exists(default_path) and dotenv_path != default_path:
        load_dotenv(default_path, override=True)
        print(f"----- 已加载默认环境变量文件: {default_path} -----")
# --- 环境特定 .env 文件加载结束 ---

class Config:
    """基础配置，包含所有环境都需要的通用配置项"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'a-hard-to-guess-jwt-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT', '3306')}/{os.environ.get('DB_NAME')}"
    
    # 数据库连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 290,
        'pool_timeout': 30,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True  # 添加预检选项
    }
    
    SERVER_NAME = None
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)  # Token 有效期7天
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 刷新Token 有效期30天
    JWT_HEADER_TYPE = 'Bearer'
    JWT_HEADER_NAME = 'Authorization'
    OSS_ACCESS_KEY = os.environ.get('OSS_ACCESS_KEY')
    OSS_SECRET_KEY = os.environ.get('OSS_SECRET_KEY')
    OSS_ENDPOINT = os.environ.get('OSS_ENDPOINT')
    OSS_BUCKET_NAME = os.environ.get('OSS_BUCKET_NAME')
    
    # 默认聊天供应商
    DEFAULT_CHAT_SOURCE = os.environ.get('DEFAULT_CHAT_SOURCE', 'openai')
    
    # OpenAI配置
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_API_BASE = os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
    OPENAI_API_PROXY = os.environ.get('OPENAI_API_PROXY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # DeepSeek配置
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
    DEEPSEEK_API_BASE = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
    DEEPSEEK_API_PROXY = os.environ.get('DEEPSEEK_API_PROXY')
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    
    # 阿里通义配置
    TONGYI_API_KEY = os.environ.get('TONGYI_API_KEY')
    TONGYI_API_BASE = os.environ.get('TONGYI_API_BASE', 'https://dashscope.aliyuncs.com/api/v1')
    TONGYI_API_PROXY = os.environ.get('TONGYI_API_PROXY')
    TONGYI_MODEL = os.environ.get('TONGYI_MODEL', 'qwen-plus')
    
    # Coze配置
    COZE_API_KEY = os.environ.get('COZE_API_KEY')
    COZE_API_BASE_URL = os.environ.get('COZE_API_BASE_URL', 'https://api.coze.cn/v1')
    COZE_WORKFLOW_ID = os.environ.get('COZE_WORKFLOW_ID')
    COZE_RUMOR_WORKFLOW_ID = os.environ.get('COZE_RUMOR_WORKFLOW_ID')
    COZE_APP_ID = os.environ.get('COZE_APP_ID')
    COZE_BOT_ID = os.environ.get('COZE_BOT_ID')
    COZE_USER_ID = os.environ.get('COZE_USER_ID', 'user123')
    
    # Dify配置
    DIFY_API_KEY = os.environ.get('DIFY_API_KEY')
    DIFY_API_BASE_URL = os.environ.get('DIFY_API_BASE_URL', 'http://localhost:8580/v1')
    DIFY_MODEL = os.environ.get('DIFY_MODEL', 'dify-workflow')
    
    # 聊天供应商配置
    CHAT_SOURCES = {
        'openai': {
            'name': 'OpenAI',
            'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
        },
        'deepseek': {
            'name': 'DeepSeek',
            'models': ['deepseek-chat', 'deepseek-coder'],
        },
        'tongyi': {
            'name': '通义千问',
            'models': ['qwen-plus', 'qwen-max', 'qwen-turbo'],
        },
        'coze': {
            'name': 'Coze',
            'models': ['coze-rumor-crusher'],
        },
        'dify': {
            'name': 'Dify',
            'models': ['dify-workflow'],
        }
    }

    @staticmethod
    def init_app(app):
        """额外的应用初始化"""
        pass

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 开发环境特定配置

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境特定配置 
    # 例如，可以覆盖某些配置项
    # SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URL') or Config.SQLALCHEMY_DATABASE_URI

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("TEST_DATABASE_URL")
        or "sqlite:///:memory:"
    )
    # 其他测试环境特定配置

# 映射环境名称到配置类
config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig
}

# 在这里添加函数以获取环境
def get_env():
    env = os.getenv('SERVER_ENV', 'dev').lower()
    print(f"----- 配置环境: {env} -----")
    return env 