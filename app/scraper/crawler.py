"""爬虫管理器

负责启动和管理网页爬虫进程
"""

import os
import time
import json
import queue
import logging
import schedule
import threading
import multiprocessing
from datetime import datetime
from typing import Dict, List, Optional

from flask import current_app
from app.scraper.spiders.news_spider import NewsSpider
from app.scraper.spiders.gov_spider import GovSpider
from app.scraper.spiders.weibo_spider import WeiboSpider

# 配置日志
logger = logging.getLogger('crawler_manager')
logger.setLevel(logging.INFO)

class CrawlerManager:
    """爬虫管理器类"""
    
    def __init__(self, app=None):
        """初始化爬虫管理器
        
        Args:
            app: Flask应用实例
        """
        self.app = app
        self.processes: Dict[str, multiprocessing.Process] = {}
        self.status: Dict[str, dict] = {}
        self.task_queue = queue.Queue()
        self.scheduler_thread = None
        self.monitor_thread = None
        self.running = False
        
        # 爬虫类映射
        self.spiders = {
            'news': NewsSpider,
            'gov': GovSpider,
            'weibo': WeiboSpider
        }
        
        # 初始化状态
        for spider_name in self.spiders.keys():
            self.status[spider_name] = {
                'status': 'stopped',
                'last_start': None,
                'last_end': None,
                'error_count': 0,
                'items_scraped': 0
            }
            
        logger.info("爬虫管理器初始化完成")
    
    def start_crawler(self, spider_name: str) -> bool:
        """启动指定爬虫
        
        Args:
            spider_name: 爬虫名称
            
        Returns:
            bool: 是否成功启动
        """
        if spider_name not in self.spiders:
            logger.error(f"未知的爬虫类型: {spider_name}")
            return False
        
        if spider_name in self.processes and self.processes[spider_name].is_alive():
            logger.warning(f"爬虫 {spider_name} 已在运行")
            return False
            
        try:
            # 创建爬虫进程
            process = multiprocessing.Process(
                target=self._run_spider,
                args=(spider_name, self.spiders[spider_name])
            )
            process.start()
        
            # 更新状态
        self.processes[spider_name] = process
            self.status[spider_name].update({
                'status': 'running',
                'last_start': datetime.now(),
                'error_count': 0
            })
            
            logger.info(f"爬虫 {spider_name} 启动成功")
        return True
    
        except Exception as e:
            logger.error(f"启动爬虫 {spider_name} 失败: {str(e)}")
            self.status[spider_name]['error_count'] += 1
            return False
            
    def stop_crawler(self, spider_name: str) -> bool:
        """停止指定爬虫
        
        Args:
            spider_name: 爬虫名称
            
        Returns:
            bool: 是否成功停止
        """
        if spider_name not in self.processes:
            logger.warning(f"爬虫 {spider_name} 未运行")
            return False
            
        try:
            process = self.processes[spider_name]
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                
            # 更新状态
            self.status[spider_name].update({
                'status': 'stopped',
                'last_end': datetime.now()
            })
            
            del self.processes[spider_name]
            logger.info(f"爬虫 {spider_name} 已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止爬虫 {spider_name} 失败: {str(e)}")
            return False
            
    def start_scheduler(self) -> bool:
        """启动调度器"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("调度器已在运行")
            return False
            
        try:
            self.running = True
            
            # 启动调度器线程
            self.scheduler_thread = threading.Thread(target=self._run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self._monitor_crawlers)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            logger.info("调度器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动调度器失败: {str(e)}")
            return False
            
    def stop_scheduler(self) -> bool:
        """停止调度器"""
        if not self.scheduler_thread or not self.scheduler_thread.is_alive():
            logger.warning("调度器未运行")
        return False
    
        try:
            self.running = False
            
            # 停止所有爬虫
        for spider_name in list(self.processes.keys()):
            self.stop_crawler(spider_name)
                
            # 等待线程结束
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
                
            logger.info("调度器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止调度器失败: {str(e)}")
            return False
            
    def add_task(self, spider_name: str, priority: int = 0) -> bool:
        """添加爬虫任务到队列
        
        Args:
            spider_name: 爬虫名称
            priority: 优先级(0-9)，数字越大优先级越高
            
        Returns:
            bool: 是否成功添加
        """
        if spider_name not in self.spiders:
            logger.error(f"未知的爬虫类型: {spider_name}")
            return False
            
        try:
            self.task_queue.put((priority, spider_name))
            logger.info(f"已添加任务: {spider_name} (优先级: {priority})")
            return True
        except Exception as e:
            logger.error(f"添加任务失败: {str(e)}")
            return False
            
    def get_status(self) -> Dict[str, dict]:
        """获取所有爬虫状态"""
        return self.status
        
    def _run_spider(self, spider_name: str, spider_class) -> None:
        """在进程中运行爬虫
        
        Args:
            spider_name: 爬虫名称
            spider_class: 爬虫类
        """
        try:
            with self.app.app_context():
                # 获取配置
                settings = current_app.config.get('TRUTH_GUARDIAN_SETTINGS', {})
                
                # 创建爬虫实例
                spider = spider_class()
                spider.custom_settings = {
                    'TRUTH_GUARDIAN_SETTINGS': settings,
                    'FLASK_APP': current_app
                }
                
                # 运行爬虫
                spider.start_crawl()
                
        except Exception as e:
            logger.error(f"爬虫 {spider_name} 运行出错: {str(e)}")
            logger.exception(e)
            self.status[spider_name]['error_count'] += 1
            
    def _run_scheduler(self) -> None:
        """运行调度器"""
        # 设置定时任务
        schedule.every().day.at("00:00").do(self.crawl_all)
        schedule.every().hour.do(self._check_tasks)
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)
            
    def _monitor_crawlers(self) -> None:
        """监控爬虫状态"""
        while self.running:
            try:
                # 检查进程状态
                for spider_name, process in list(self.processes.items()):
                    if not process.is_alive():
                        logger.warning(f"爬虫 {spider_name} 异常退出，尝试重启")
                        self.stop_crawler(spider_name)
                        self.start_crawler(spider_name)
                        
                # 处理任务队列
                while not self.task_queue.empty():
                    priority, spider_name = self.task_queue.get()
                    if spider_name not in self.processes or not self.processes[spider_name].is_alive():
                        self.start_crawler(spider_name)
                        
            except Exception as e:
                logger.error(f"监控线程出错: {str(e)}")
                logger.exception(e)
                
            time.sleep(60)  # 每分钟检查一次
            
    def _check_tasks(self) -> None:
        """检查并执行定时任务"""
        try:
            # 获取配置
            with self.app.app_context():
                settings = current_app.config.get('TRUTH_GUARDIAN_SETTINGS', {})
                schedules = settings.get('SCHEDULES', {})
                
            # 检查每个爬虫的调度时间
            current_hour = datetime.now().hour
            for spider_name, schedule_hours in schedules.items():
                if current_hour in schedule_hours:
                    self.add_task(spider_name)
                    
        except Exception as e:
            logger.error(f"检查任务出错: {str(e)}")
            logger.exception(e)
            
    def crawl_all(self) -> None:
        """启动所有爬虫"""
        for spider_name in self.spiders.keys():
            self.add_task(spider_name)

# 创建一个全局的爬虫管理器实例
crawler_manager = None

def init_crawler(app=None):
    """初始化爬虫管理器
    
    Args:
        app: Flask应用实例
    
    Returns:
        CrawlerManager: 爬虫管理器实例
    """
    global crawler_manager
    if crawler_manager is None:
        crawler_manager = CrawlerManager(app)
    return crawler_manager

def get_crawler_manager():
    """获取爬虫管理器实例
    
    Returns:
        CrawlerManager: 爬虫管理器实例
    """
    global crawler_manager
    if crawler_manager is None:
        crawler_manager = CrawlerManager()
    return crawler_manager 