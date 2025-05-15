import os
from dotenv import load_dotenv

# 加载基础 .env 文件 (可选，可以放一些通用设置或默认值)
base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, '..', '.env')) # 加载项目根目录的.env

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'a_default_jwt_secret'
    # 其他通用配置...

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://dev_user:dev_password@localhost/dev_db'
    # 开发特定的OSS Key等...
    OSS_ACCESS_KEY = os.environ.get('DEV_OSS_ACCESS_KEY')
    OSS_SECRET_KEY = os.environ.get('DEV_OSS_SECRET_KEY')
    # ...

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://prod_user:prod_password@prod_db_host/prod_db'
    # 生产特定的OSS Key等...
    OSS_ACCESS_KEY = os.environ.get('OSS_ACCESS_KEY')
    OSS_SECRET_KEY = os.environ.get('OSS_SECRET_KEY')
    # ...

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    # ...

# 映射环境名称到配置类
config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig,
    test=TestingConfig
) 