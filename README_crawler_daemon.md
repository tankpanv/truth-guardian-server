# 爬虫守护进程使用说明

## 概述
这是一个后台运行的爬虫守护进程系统，每小时自动执行爬虫和消息推送任务。使用相对路径设计，方便部署到不同环境。

## 文件说明

### 1. `crawler_daemon.sh` - 守护进程主脚本
- 后台循环运行，每小时执行一次任务
- 自动检测重复启动
- 完善的信号处理和清理机制
- 详细的日志记录

### 2. `crawler_control.sh` - 控制脚本
- 提供启动、停止、重启、状态查看等功能
- 友好的命令行界面
- 实时日志查看功能

## 使用方法

### 启动守护进程
```bash
./crawler_control.sh start
```

### 停止守护进程
```bash
./crawler_control.sh stop
```

### 重启守护进程
```bash
./crawler_control.sh restart
```

### 查看运行状态
```bash
./crawler_control.sh status
```

### 查看日志
```bash
# 查看今天的守护进程日志
./crawler_control.sh logs

# 实时查看日志（按Ctrl+C退出）
./crawler_control.sh tail
```

## 执行任务

守护进程会在每小时的0分钟执行以下任务：
1. 执行爬虫：`python app/scraper/spiders/xinlang_search.py`
2. 推送消息：`python send_message.py --now`

## 日志文件

所有日志文件保存在 `./logs/` 目录下：

- `crawler_daemon_YYYYMMDD.log` - 守护进程日志
- `crawler_push_YYYYMMDD.log` - 任务执行日志

日志文件会自动按日期分割，并保留最近7天的记录。

## 部署说明

### 1. 环境要求
- Python 3.x
- 虚拟环境（可选，脚本会自动检测）
- 必要的Python依赖包

### 2. 部署步骤
1. 将项目文件复制到目标服务器
2. 确保脚本有执行权限：`chmod +x crawler_daemon.sh crawler_control.sh`
3. 启动守护进程：`./crawler_control.sh start`

### 3. 相对路径设计
- 脚本使用相对路径，可以部署到任何目录
- 自动检测脚本所在目录并切换工作目录
- 无需修改配置即可在不同环境运行

## 进程管理

### PID文件
- 守护进程运行时会创建 `crawler_daemon.pid` 文件
- 记录进程ID，用于状态检查和进程管理
- 进程停止时自动清理PID文件

### 信号处理
- 支持SIGTERM和SIGINT信号优雅停止
- 自动清理资源和临时文件
- 防止僵尸进程产生

## 故障排除

### 1. 守护进程启动失败
- 检查脚本权限：`ls -la crawler_daemon.sh`
- 查看错误日志：`./crawler_control.sh logs`
- 确认虚拟环境路径正确

### 2. 任务执行失败
- 查看任务日志：`cat logs/crawler_push_$(date +%Y%m%d).log`
- 检查Python环境和依赖包
- 确认网络连接正常

### 3. 进程僵死
- 强制停止：`./crawler_control.sh stop`
- 手动清理：`rm -f crawler_daemon.pid`
- 重新启动：`./crawler_control.sh start`

## 监控建议

### 1. 系统监控
- 定期检查进程状态：`./crawler_control.sh status`
- 监控日志文件大小和磁盘空间
- 设置系统资源使用告警

### 2. 日志监控
- 监控错误日志关键字
- 设置任务执行失败告警
- 定期清理旧日志文件

### 3. 自动重启
可以配合系统的进程监控工具（如supervisord）实现自动重启功能。

## 注意事项

1. **单实例运行**：脚本会自动检测并防止重复启动
2. **资源清理**：进程停止时会自动清理PID文件和临时资源
3. **日志轮转**：自动清理7天前的日志文件，防止磁盘空间不足
4. **虚拟环境**：自动检测并激活虚拟环境，如果不存在则使用系统Python
5. **部署灵活**：使用相对路径，可以部署到任何目录而无需修改配置 