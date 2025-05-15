from app import create_app, db
import os
import click
import sys
import eventlet
eventlet.monkey_patch()  # 必须在导入其他模块之前进行猴子补丁
from flask.cli import with_appcontext

# 检查命令行参数
if '--env=prod' in sys.argv:
    os.environ['SERVER_ENV'] = 'prod'
    print("从命令行参数设置环境为: prod")
    # 移除这个参数，避免传给 Flask
    sys.argv.remove('--env=prod')
elif '--env=dev' in sys.argv:
    os.environ['SERVER_ENV'] = 'dev'
    print("从命令行参数设置环境为: dev")
    sys.argv.remove('--env=dev')

app = create_app()

@click.command('init-db')
@with_appcontext
def init_db_command():
    """初始化数据库表结构"""
    db.create_all()
    click.echo('成功初始化数据库。')
    
@click.command('drop-db')
@with_appcontext
def drop_db_command():
    """删除所有数据库表"""
    if click.confirm('确定要删除所有表吗？这将永久删除所有数据'):
        db.drop_all()
        click.echo('成功删除所有表。')

# 向Flask CLI添加自定义命令
app.cli.add_command(init_db_command)
app.cli.add_command(drop_db_command)

if __name__ == '__main__':
    with app.app_context():
        # 确保所有表都存在
        db.create_all()
    
    # 从环境变量获取端口号
    port = int(os.getenv('PORT', 5005))
    print(f"----- 服务将在端口 {port} 上启动（使用 eventlet） -----")
    
    # 使用 eventlet 的 WSGI 服务器
    eventlet.wsgi.server(
        eventlet.listen(('0.0.0.0', port)), 
        app,
        debug=app.config.get('DEBUG', True)
    ) 