"""
消息处理器 - 增强版 (适配资金管理建议)
"""
from typing import Dict, List, Optional

class MessageHandler:
    def __init__(self):
        # 订阅者列表 (简单演示，实际建议存入数据库)
        self.subscribers = set()

    def format_latest_result(self, data: Dict) -> str:
        """格式化最新开奖结果"""
        if not data: return "❌ 获取数据失败"
        
        nums = " + ".join(map(str, data.get('numbers', [])))
        total = data.get('total', 0)
        dx = "大" if data.get('is_big') else "小"
        ds = "单" if data.get('is_odd') else "双"
        
        return (
            f"<b>🎰 加拿大28 最新开奖</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>期数：</b> <code>{data.get('period')}</code>\n"
            f"<b>号码：</b> <code>{nums} = {total}</code>\n"
            f"<b>结果：</b> <pre>{dx} | {ds}</pre>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⏰ <i>更新时间：{data.get('open_time')}</i>"
        )

    def format_prediction(self, pred: Dict) -> str:
        """格式化预测消息 (包含资金建议)"""
        if not pred: return "❌ 预测生成失败"
        
        dx = "大" if pred.get('is_big') else "小"
        ds = "单" if pred.get('is_odd') else "双"
        
        # 信心指数转换成进度条
        def get_bar(conf):
            filled = int(conf * 10)
            return "●" * filled + "○" * (10 - filled)

        return (
            f"<b>🔮 AI 智能预测 - 期号 {pred.get('period')}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>推荐选择：</b> <code>【 {dx} {ds} 】</code>\n"
            f"<b>范围参考：</b> <code>{pred.get('predicted_total_range')}</code>\n\n"
            f"<b>分析：</b>\n<i>{pred.get('analysis')}</i>\n\n"
            f"<b>💰 资金管理建议：</b>\n"
            f"<code>{pred.get('betting_plan')}</code>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>风险提示：AI预测仅供参考，请根据个人承受能力合理安排计划。</i>"
        )

    def format_history(self, history: List[Dict]) -> str:
        """格式化历史记录列表"""
        if not history: return "❌ 暂无历史数据"
        
        lines = []
        for d in history[:10]:
            dx = "大" if d.get('is_big') else "小"
            ds = "单" if d.get('is_odd') else "双"
            lines.append(f"<code>{d.get('period')}</code> | {d.get('total')} | {dx}{ds}")
        
        content = "\n".join(lines)
        return (
            f"<b>📜 历史开奖记录 (近10期)</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>期号 | 总和 | 结果</b>\n"
            f"{content}\n"
            f"━━━━━━━━━━━━━━━"
        )

    def format_stats(self, stats: Dict, history: List[Dict]) -> str:
        """格式化统计数据"""
        accuracy = stats.get('accuracy', 0) * 100
        total = stats.get('total', 0)
        
        return (
            f"<b>📊 AI 运行统计报告</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>总计样本：</b> {total} 期\n"
            f"<b>预测胜率：</b> <code>{accuracy:.2f}%</code>\n\n"
            f"<b>近期走势偏向：</b>\n"
            f"• 近20期大数：{sum(1 for d in history[:20] if d.get('is_big'))} 次\n"
            f"• 近20期单数：{sum(1 for d in history[:20] if d.get('is_odd'))} 次\n"
            f"━━━━━━━━━━━━━━━"
        )

    # --- 订阅管理功能 ---
    def add_subscriber(self, user_id: int) -> bool:
        if user_id in self.subscribers: return False
        self.subscribers.add(user_id)
        return True

    def remove_subscriber(self, user_id: int) -> bool:
        if user_id not in self.subscribers: return False
        self.subscribers.remove(user_id)
        return True

    def get_subscribers(self) -> List[int]:
        return list(self.subscribers)

    def format_status(self, status: Dict) -> str:
        return (
            f"<b>🖥️ 系统运行状态</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>运行时长：</b> {status.get('uptime')}\n"
            f"<b>活跃订阅：</b> {status.get('subscribers')} 人\n"
            f"<b>接口状态：</b> {status.get('api_status')}\n"
            f"<b>上次推送：</b> {status.get('last_update')}\n"
            f"━━━━━━━━━━━━━━━"
        )

    def format_push_message(self, actual: Dict, prediction: Optional[Dict]) -> str:
        """当新一期开出时，生成推送给所有人的总结消息"""
        dx = "大" if actual.get('is_big') else "小"
        ds = "单" if actual.get('is_odd') else "双"
        
        msg = (
            f"<b>🆕 新开奖推送 [ {actual.get('period')} ]</b>\n"
            f"结果：<code>{actual.get('total')} ({dx}{ds})</code>\n"
        )
        
        if prediction:
            # 检查预测是否正确
            p_dx = "大" if prediction.get('is_big') else "小"
            p_ds = "单" if prediction.get('is_odd') else "双"
            correct = (p_dx == dx and p_ds == ds)
            
            result_tag = "✅ 预测全中！" if correct else "❌ 本期未中"
            msg += f"预测：<code>{p_dx}{p_ds}</code> -> {result_tag}\n"
            
        msg += f"\n👉 使用 /predict 获取下一期分析"
        return msg

message_handler = MessageHandler()
