"""
配置文件 - 加拿大28预测机器人
"""
import os
from typing import List


class Config:
    # 这里的 os.getenv 会自动读取你在 Railway 设置的 BOT_TOKEN 环境变量
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "7888887488:AAHbFpdqC6-ZCfGx4PXGyhCOYqbMhiMnpxk")
    ADMIN_IDS: List[int] = [7572817792]
    API_BASE_URL: str = "https://dd28yc.com/data/get/getForecastByType"
    API_PARAMS: dict = {'game': 'jnd28', 'type': 'zh', 'sf': '1'}
    PREDICT_MODE: str = "standard"
    HISTORY_COUNT: int = 50
    CONFIDENCE_THRESHOLD: float = 0.6
    AUTO_PUSH_ENABLED: bool = True
    CHECK_INTERVAL: int = 30
    LOTTERY_INTERVAL: int = 210
    SHOW_ANALYSIS: bool = True
    RECORD_RESULTS: bool = True
    
    WELCOME_MESSAGE: str = """
🎰 <b>加拿大28预测机器人</b> 🎰

欢迎使用！我可以帮你：
📊 查询最新开奖结果
🔮 获取下期预测
📈 查看历史走势

<b>功能命令：</b>
/start - 开始使用
/help - 帮助信息
/latest - 最新开奖
/predict - 获取预测
/history - 历史记录
/stats - 统计数据
/subscribe - 订阅推送
/unsubscribe - 取消订阅

祝您好运！🍀
"""
    
    HELP_MESSAGE: str = """
📖 <b>使用帮助</b>

<b>基础功能：</b>
/latest - 查看最新一期开奖结果
/predict - 获取下一期预测
/history - 查看最近10期开奖记录
/stats - 查看统计数据和胜率

<b>订阅功能：</b>
/subscribe - 订阅开奖推送
/unsubscribe - 取消订阅

<b>管理功能：</b>
/status - 查看机器人状态 (管理员)
/broadcast - 广播消息 (管理员)
"""
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        return user_id in cls.ADMIN_IDS


config = Config()
