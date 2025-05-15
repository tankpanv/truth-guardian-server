import subprocess
import socket
import time
import logging

def check_redis_connection(host='localhost', port=6379, timeout=3):
    """检查Redis连接是否可用"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except:
        return False

def install_and_start_redis():
    """安装并启动Redis服务"""
    try:
        # 检查是否已安装Redis
        result = subprocess.run(['which', 'redis-server'], capture_output=True)
        if result.returncode != 0:
            logging.info("Redis未安装,开始安装...")
            
            # 更新包列表
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            
            # 安装Redis
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'redis-server'], check=True)
            
            logging.info("Redis安装完成")
        
        # 检查Redis服务状态
        status = subprocess.run(['systemctl', 'is-active', 'redis-server'], capture_output=True)
        if status.stdout.decode().strip() != 'active':
            logging.info("启动Redis服务...")
            subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], check=True)
            
            # 等待服务启动
            for _ in range(5):
                if check_redis_connection():
                    break
                time.sleep(1)
            
            logging.info("Redis服务已启动")
            
            # 设置开机自启
            subprocess.run(['sudo', 'systemctl', 'enable', 'redis-server'], check=True)
            
        return True
    except Exception as e:
        logging.error(f"安装/启动Redis失败: {str(e)}")
        return False

def get_platform():
    """获取操作系统类型"""
    import platform
    return platform.system().lower()

def install_redis_by_platform():
    """根据平台选择安装方式"""
    platform = get_platform()
    
    if platform == 'linux':
        # 检测具体的Linux发行版
        import distro
        distro_name = distro.id()
        
        if distro_name in ['ubuntu', 'debian']:
            return install_and_start_redis()
        elif distro_name in ['centos', 'rhel', 'fedora']:
            # CentOS/RHEL系统的安装命令
            # ... 实现CentOS的安装逻辑 ...
            pass
    elif platform == 'darwin':
        # macOS的安装命令(使用homebrew)
        # ... 实现macOS的安装逻辑 ...
        pass
    
    return False 