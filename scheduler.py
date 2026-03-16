"""
定时任务模块
"""
from datetime import datetime
from typing import Callable, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import config
from logger import logger


class TaskScheduler:
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.check_callback: Optional[Callable] = None
        self.is_running = False
        self.last_check_time: Optional[datetime] = None
        self.check_count = 0
    
    def init_scheduler(self):
        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()
            logger.info("调度器初始化完成")
    
    def start(self):
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            self.is_running = True
            logger.info("调度器已启动")
    
    def stop(self):
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("调度器已停止")
    
    def set_check_callback(self, callback: Callable):
        self.check_callback = callback
    
    def add_check_job(self, interval: int = None):
        if not self.scheduler:
            self.init_scheduler()
        
        interval = interval or config.CHECK_INTERVAL
        
        try:
            self.scheduler.remove_job('check_data')
        except:
            pass
        
        self.scheduler.add_job(
            self._check_data_wrapper,
            trigger=IntervalTrigger(seconds=interval),
            id='check_data',
            name='检查新开奖数据',
            replace_existing=True
        )
        logger.info(f"数据检查任务已添加，间隔: {interval}秒")
    
    async def _check_data_wrapper(self):
        self.last_check_time = datetime.now()
        self.check_count += 1
        if self.check_callback:
            try:
                await self.check_callback()
            except Exception as e:
                logger.error(f"数据检查回调异常: {str(e)}")
    
    def get_status(self) -> dict:
        return {
            'is_running': self.is_running,
            'last_check_time': self.last_check_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_check_time else None,
            'check_count': self.check_count,
            'jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0
        }


task_scheduler = TaskScheduler()
