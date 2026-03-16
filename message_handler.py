"""
消息处理模块
"""
from typing import Dict, List, Set
from datetime import datetime
from logger import logger


class MessageHandler:
    def __init__(self):
        self.subscribers: Set[int] = set()
    
    def format_latest_result(self, data: Dict) -> str:
        if not data:
            return "❌ 暂无开奖数据"
        
        period = data.get('period', '未知')
        total = data.get('total', 0)
        is_big = data.get('is_big')
        is_odd = data.get('is_odd')
        raw_string = data.get('raw_string', '')
        
        big_small = '大 🔴' if is_big else '小 🔵'
        odd_even = '单 ⚪' if is_odd else '双 ⚫'
        
        return f"""
🎰 <b>最新开奖结果</b> 🎰

📌 期号: <code>{period}</code>
🎲 号码: <b>{raw_string}</b>
📊 和值: <b>{total}</b>

📈 大小: {big_small}
📉 单双: {odd_even}

⏰ 更新时间: {datetime.now().strftime('%H:%M:%S')}
""".strip()
    
    def format_prediction(self, prediction: Dict) -> str:
        if not prediction:
            return "❌ 预测生成失败"
        
        period = prediction.get('period', '下一期')
        is_big = prediction.get('is_big')
        is_odd = prediction.get('is_odd')
        big_conf = prediction.get('big_confidence', 0.5)
        odd_conf = prediction.get('odd_confidence', 0.5)
        total_range = prediction.get('predicted_total_range', '')
        analysis = prediction.get('analysis', '')
        
        big_small = '大 🔴' if is_big else '小 🔵'
        odd_even = '单 ⚪' if is_odd else '双 ⚫'
        big_stars = self._confidence_to_stars(big_conf)
        odd_stars = self._confidence_to_stars(odd_conf)
        
        return f"""
🔮 <b>下期预测</b> 🔮

📌 期号: <code>{period}</code>

━━━━━━━━━━━━━━━
🎯 <b>预测结果</b>

📈 大小: {big_small}
   置信度: {big_stars} ({big_conf:.0%})

📉 单双: {odd_even}
   置信度: {odd_stars} ({odd_conf:.0%})

📊 和值范围: {total_range}
━━━━━━━━━━━━━━━

💡 <b>分析说明</b>
{analysis}

⚠️ <i>预测仅供参考，请理性投注</i>
""".strip()
    
    def format_history(self, history: List[Dict]) -> str:
        if not history:
            return "❌ 暂无历史数据"
        
        lines = ["📜 <b>最近开奖记录</b>\n", "期号 | 号码 | 和值 | 大小 | 单双", "━" * 30]
        
        for data in history[:10]:
            period = str(data.get('period', ''))[-4:]
            raw_string = data.get('raw_string', '')
            total = data.get('total', 0)
            big_small = '大' if data.get('is_big') else '小'
            odd_even = '单' if data.get('is_odd') else '双'
            lines.append(f"<code>{period}</code> | {raw_string} | {total} | {big_small} | {odd_even}")
        
        lines.append("━" * 30)
        lines.append(f"\n⏰ 更新时间: {datetime.now().strftime('%H:%M:%S')}")
        return "\n".join(lines)
    
    def format_stats(self, stats: Dict, history: List[Dict] = None) -> str:
        total = stats.get('total', 0)
        accuracy = stats.get('accuracy', 0)
        big_accuracy = stats.get('big_accuracy', 0)
        odd_accuracy = stats.get('odd_accuracy', 0)
        
        history_stats = ""
        if history and len(history) >= 10:
            recent = history[:50]
            big_count = sum(1 for d in recent if d.get('is_big'))
            odd_count = sum(1 for d in recent if d.get('is_odd'))
            history_stats = f"""
━━━━━━━━━━━━━━━
📊 <b>近50期统计</b>

🔴 大: {big_count}次 ({big_count/len(recent):.0%})
🔵 小: {len(recent)-big_count}次 ({(len(recent)-big_count)/len(recent):.0%})
⚪ 单: {odd_count}次 ({odd_count/len(recent):.0%})
⚫ 双: {len(recent)-odd_count}次 ({(len(recent)-odd_count)/len(recent):.0%})
"""
        
        return f"""
📈 <b>预测统计</b> 📈

━━━━━━━━━━━━━━━
🎯 <b>预测准确率</b>

📌 总预测次数: {total}
✅ 完全正确: {stats.get('correct', 0)}
📊 综合准确率: {accuracy:.1%}

📈 大小准确率: {big_accuracy:.1%}
📉 单双准确率: {odd_accuracy:.1%}
{history_stats}
━━━━━━━━━━━━━━━
⏰ 统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()
    
    def format_push_message(self, data: Dict, prediction: Dict = None) -> str:
        result_msg = self.format_latest_result(data)
        if prediction:
            pred_msg = self.format_prediction(prediction)
            return f"{result_msg}\n\n{'='*20}\n\n{pred_msg}"
        return result_msg
    
    def format_status(self, bot_status: Dict) -> str:
        return f"""
🤖 <b>机器人状态</b>

━━━━━━━━━━━━━━━
📌 运行时间: {bot_status.get('uptime', '未知')}
👥 订阅用户: {bot_status.get('subscribers', 0)}
🔄 最后更新: {bot_status.get('last_update', '未知')}
🌐 API状态: {bot_status.get('api_status', '未知')}
━━━━━━━━━━━━━━━
""".strip()
    
    def _confidence_to_stars(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "⭐⭐⭐⭐⭐"
        elif confidence >= 0.7:
            return "⭐⭐⭐⭐☆"
        elif confidence >= 0.6:
            return "⭐⭐⭐☆☆"
        elif confidence >= 0.5:
            return "⭐⭐☆☆☆"
        return "⭐☆☆☆☆"
    
    def add_subscriber(self, user_id: int) -> bool:
        if user_id in self.subscribers:
            return False
        self.subscribers.add(user_id)
        logger.info(f"用户 {user_id} 订阅成功")
        return True
    
    def remove_subscriber(self, user_id: int) -> bool:
        if user_id not in self.subscribers:
            return False
        self.subscribers.discard(user_id)
        logger.info(f"用户 {user_id} 取消订阅")
        return True
    
    def is_subscribed(self, user_id: int) -> bool:
        return user_id in self.subscribers
    
    def get_subscribers(self) -> Set[int]:
        return self.subscribers.copy()


message_handler = MessageHandler()
