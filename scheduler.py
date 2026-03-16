"""
任务调度模块 - 异步增强版
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from logger import logger

class TaskScheduler:
    def __init__(self):
        # 明确使用异步调度器
        self.scheduler = AsyncIOScheduler()
        self.check_callback = None

    def init_scheduler(self):
        # 如果已经运行，先关掉，防止重复运行
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.scheduler = AsyncIOScheduler()

    def set_check_callback(self, callback):
        self.check_callback = callback

    def add_check_job(self, interval_seconds):
        # 添加定时任务，并设置错失触发策略
        self.scheduler.add_job(
            self.check_callback, 
            'interval', 
            seconds=interval_seconds,
            id='check_new_data',
            replace_existing=True,
            misfire_grace_time=60  # 如果错过时间，60秒内允许补发
        )
        logger.info(f"⏰ 定时检查任务已添加，每 {interval_seconds} 秒运行一次")

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("🚀 异步调度器已启动")

    def get_status(self):
        job = self.scheduler.get_job('check_new_data')
        return {
            'running': self.scheduler.running,
            'next_run': str(job.next_run_time) if job else "未排程"
        }

task_scheduler = TaskScheduler()


task_scheduler = TaskScheduler()
