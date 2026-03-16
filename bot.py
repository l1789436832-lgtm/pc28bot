import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 配置
BOT_TOKEN = "8691919071:AAGYpC3J14YvStKbiFZ4OyfS1PVyg3Dir5M"
CHAT_ID = os.getenv("CHAT_ID", "")
API_URL = "https://api.pearpc28.com/lotteryDraw/find"

# 日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据目录
DATA_DIR = Path("pc28_data")
DATA_DIR.mkdir(exist_ok=True)

class DataManager:
    """数据持久化管理"""
    
    @staticmethod
    def save(filename, data):
        with open(DATA_DIR / filename, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load(filename, default=None):
        try:
            with open(DATA_DIR / filename, 'r') as f:
                return json.load(f)
        except:
            return default if default else {}

class BettingManager:
    """资金管理 - 马丁格尔策略"""
    
    def __init__(self):
        self.data = DataManager.load('betting.json', {
            'capital': 1000,
            'initial': 1000,
            'base_bet': 10,
            'martin_level': 0,
            'max_level': 5,
            'history': [],
            'wins': 0,
            'losses': 0
        })
    
    def save(self):
        DataManager.save('betting.json', self.data)
    
    def get_bet_amount(self):
        return self.data['base_bet'] * (2 ** self.data['martin_level'])
    
    def record_win(self):
        bet = self.get_bet_amount()
        profit = bet * 1.95
        self.data['capital'] += profit
        self.data['wins'] += 1
        self.data['martin_level'] = 0
        self.data['history'].append({'result': 'win', 'profit': profit, 'time': str(datetime.now())})
        self.save()
        return profit
    
    def record_loss(self):
        bet = self.get_bet_amount()
        self.data['capital'] -= bet
        self.data['losses'] += 1
        if self.data['martin_level'] < self.data['max_level']:
            self.data['martin_level'] += 1
        self.data['history'].append({'result': 'loss', 'loss': bet, 'time': str(datetime.now())})
        self.save()
        return bet
    
    def reset(self, amount=1000):
        self.data['capital'] = amount
        self.data['initial'] = amount
        self.data['martin_level'] = 0
        self.data['wins'] = 0
        self.data['losses'] = 0
        self.data['history'] = []
        self.save()
    
    def get_status(self):
        profit_rate = (self.data['capital'] - self.data['initial']) / self.data['initial'] * 100
        total = self.data['wins'] + self.data['losses']
        win_rate = (self.data['wins'] / total * 100) if total > 0 else 0
        return {
            'capital': self.data['capital'],
            'profit_rate': profit_rate,
            'martin_level': self.data['martin_level'],
            'next_bet': self.get_bet_amount(),
            'wins': self.data['wins'],
            'losses': self.data['losses'],
            'win_rate': win_rate
        }

class PredictionEngine:
    """预测引擎"""
    
    @staticmethod
    def analyze(history):
        if len(history) < 10:
            return None
        
        recent = history[:30]
        
        # 统计大小单双
        big_count = sum(1 for h in recent if h['openNum'] >= 14)
        small_count = len(recent) - big_count
        odd_count = sum(1 for h in recent if h['openNum'] % 2 == 1)
        even_count = len(recent) - odd_count
        
        # MA分析
        ma5 = sum(h['openNum'] for h in recent[:5]) / 5
        ma10 = sum(h['openNum'] for h in recent[:10]) / 10
        
        # 预测大小
        if small_count > big_count * 1.3:
            size_pred, size_conf = '大', min(55 + (small_count - big_count) * 2, 75)
        elif big_count > small_count * 1.3:
            size_pred, size_conf = '小', min(55 + (big_count - small_count) * 2, 75)
        else:
            size_pred, size_conf = '大' if ma5 < 14 else '小', 52
        
        # 预测单双
        if even_count > odd_count * 1.3:
            parity_pred, parity_conf = '单', min(55 + (even_count - odd_count) * 2, 75)
        elif odd_count > even_count * 1.3:
            parity_pred, parity_conf = '双', min(55 + (odd_count - even_count) * 2, 75)
        else:
            parity_pred, parity_conf = '单' if recent[0]['openNum'] % 2 == 0 else '双', 52
        
        return {
            'size': {'pred': size_pred, 'conf': size_conf},
            'parity': {'pred': parity_pred, 'conf': parity_conf},
            'ma5': ma5,
            'ma10': ma10,
            'stats': {'big': big_count, 'small': small_count, 'odd': odd_count, 'even': even_count}
        }

# 全局实例
betting = BettingManager()

async def fetch_data(limit=100):
    """获取API数据"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"pageNum": 1, "pageSize": limit, "lotteryCode": "jnd28"}
            async with session.post(API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if data.get('code') == 200:
                    rows = data.get('data', {}).get('rows', [])
                    for row in rows:
                        nums = [int(row.get(f'num{i}', 0)) for i in range(1, 4)]
                        row['numbers'] = nums
                        row['openNum'] = sum(nums)
                    return rows
    except Exception as e:
        logger.error(f"API错误: {e}")
    return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始命令"""
    keyboard = [
        [InlineKeyboardButton("🎯 获取预测", callback_data="predict"),
         InlineKeyboardButton("📊 统计30期", callback_data="stat30")],
        [InlineKeyboardButton("💰 资金状态", callback_data="betting"),
         InlineKeyboardButton("📈 回测分析", callback_data="backtest")],
        [InlineKeyboardButton("✅ 记录胜", callback_data="win"),
         InlineKeyboardButton("❌ 记录负", callback_data="loss")]
    ]
    
    await update.message.reply_text(
        "🎰 *PC28 预测机器人 v26*\n\n"
        "功能列表:\n"
        "• /predict - 获取预测\n"
        "• /stat30 - 30期统计\n"
        "• /stat100 - 100期统计\n"
        "• /betting - 资金状态\n"
        "• /backtest - 准确率回测\n"
        "• /win - 记录胜利\n"
        "• /loss - 记录失败\n"
        "• /reset [金额] - 重置资金\n"
        "• /status - 系统状态",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """预测命令"""
    history = await fetch_data(50)
    if not history:
        await update.message.reply_text("❌ 数据获取失败")
        return
    
    latest = history[0]
    pred = PredictionEngine.analyze(history)
    status = betting.get_status()
    
    size_icon = "🔴" if pred['size']['pred'] == '大' else "🔵"
    parity_icon = "🔺" if pred['parity']['pred'] == '单' else "🔻"
    
    text = (
        f"🎯 *PC28 预测分析*\n\n"
        f"📍 最新: 第 {latest['periodsNumber']} 期\n"
        f"🎲 [{latest['numbers'][0]},{latest['numbers'][1]},{latest['numbers'][2]}] = {latest['openNum']}\n\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"🎯 *下期预测*\n"
        f"• 大小: {size_icon} {pred['size']['pred']} ({pred['size']['conf']}%)\n"
        f"• 单双: {parity_icon} {pred['parity']['pred']} ({pred['parity']['conf']}%)\n\n"
        f"📊 MA5: {pred['ma5']:.1f} | MA10: {pred['ma10']:.1f}\n\n"
        f"💰 *投注建议*\n"
        f"• 金额: {status['next_bet']}\n"
        f"• 马丁层: {status['martin_level']}"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def stat30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """30期统计"""
    await send_stats(update, 30)

async def stat100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """100期统计"""
    await send_stats(update, 100)

async def send_stats(update, count):
    """发送统计"""
    history = await fetch_data(count)
    if not history:
        await update.message.reply_text("❌ 数据获取失败")
        return
    
    big = sum(1 for h in history if h['openNum'] >= 14)
    small = len(history) - big
    odd = sum(1 for h in history if h['openNum'] % 2 == 1)
    even = len(history) - odd
    avg = sum(h['openNum'] for h in history) / len(history)
    
    text = (
        f"📊 *最近 {len(history)} 期统计*\n\n"
        f"🔴 大: {big} ({big/len(history)*100:.1f}%)\n"
        f"🔵 小: {small} ({small/len(history)*100:.1f}%)\n"
        f"🔺 单: {odd} ({odd/len(history)*100:.1f}%)\n"
        f"🔻 双: {even} ({even/len(history)*100:.1f}%)\n\n"
        f"📈 平均值: {avg:.2f}"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def backtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """回测分析"""
    history = await fetch_data(100)
    if len(history) < 50:
        await update.message.reply_text("❌ 数据不足")
        return
    
    size_hits = 0
    parity_hits = 0
    tests = 0
    
    for i in range(len(history) - 30):
        test_data = history[i+1:i+31]
        actual = history[i]
        pred = PredictionEngine.analyze(test_data)
        
        if pred:
            tests += 1
            actual_size = '大' if actual['openNum'] >= 14 else '小'
            actual_parity = '单' if actual['openNum'] % 2 == 1 else '双'
            
            if pred['size']['pred'] == actual_size:
                size_hits += 1
            if pred['parity']['pred'] == actual_parity:
                parity_hits += 1
    
    text = (
        f"📈 *回测分析 (最近{tests}期)*\n\n"
        f"🎯 大小准确率: {size_hits/tests*100:.1f}%\n"
        f"🎯 单双准确率: {parity_hits/tests*100:.1f}%\n\n"
        f"✅ 大小命中: {size_hits}/{tests}\n"
        f"✅ 单双命中: {parity_hits}/{tests}"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def betting_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """资金状态"""
    status = betting.get_status()
    
    profit_icon = "📈" if status['profit_rate'] >= 0 else "📉"
    
    text = (
        f"💰 *资金状态*\n\n"
        f"💵 当前资金: {status['capital']:.1f}\n"
        f"{profit_icon} 盈亏比例: {status['profit_rate']:.1f}%\n\n"
        f"🎯 胜/负: {status['wins']}/{status['losses']}\n"
        f"📊 胜率: {status['win_rate']:.1f}%\n\n"
        f"🔄 马丁层数: {status['martin_level']}\n"
        f"💎 下注金额: {status['next_bet']}"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """记录胜利"""
    profit = betting.record_win()
    status = betting.get_status()
    await update.message.reply_text(
        f"✅ *胜利!* +{profit:.1f}\n"
        f"💵 当前资金: {status['capital']:.1f}",
        parse_mode='Markdown'
    )

async def loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """记录失败"""
    lost = betting.record_loss()
    status = betting.get_status()
    await update.message.reply_text(
        f"❌ *失败!* -{lost:.1f}\n"
        f"🔄 马丁层数: {status['martin_level']}\n"
        f"💎 下注建议: {status['next_bet']}\n"
        f"💵 当前资金: {status['capital']:.1f}",
        parse_mode='Markdown'
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """重置资金"""
    amount = 1000
    if context.args:
        try:
            amount = float(context.args[0])
        except:
            pass
    
    betting.reset(amount)
    await update.message.reply_text(f"🔄 资金已重置为 {amount}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """系统状态"""
    history = await fetch_data(1)
    api_status = "✅ 正常" if history else "❌ 异常"
    
    text = (
        f"⚙️ *系统状态*\n\n"
        f"🤖 机器人: ✅ 运行中\n"
        f"🌐 API: {api_status}\n"
        f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    if history:
        text += f"\n\n📍 最新期号: {history[0]['periodsNumber']}"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """按钮回调"""
    query = update.callback_query
    await query.answer()
    
    # 创建假的 message 对象用于复用命令处理器
    class FakeUpdate:
        def __init__(self, message):
            self.message = message
    
    fake_update = FakeUpdate(query.message)
    
    if query.data == "predict":
        await predict_callback(query)
    elif query.data == "stat30":
        await stat_callback(query, 30)
    elif query.data == "betting":
        await betting_callback(query)
    elif query.data == "backtest":
        await backtest_callback(query)
    elif query.data == "win":
        profit = betting.record_win()
        status = betting.get_status()
        await query.message.reply_text(f"✅ 胜利! +{profit:.1f}\n💵 资金: {status['capital']:.1f}")
    elif query.data == "loss":
        lost = betting.record_loss()
        status = betting.get_status()
        await query.message.reply_text(f"❌ 失败! -{lost:.1f}\n🔄 马丁: {status['martin_level']}\n💵 资金: {status['capital']:.1f}")

async def predict_callback(query):
    """预测回调"""
    history = await fetch_data(50)
    if not history:
        await query.message.reply_text("❌ 数据获取失败")
        return
    
    latest = history[0]
    pred = PredictionEngine.analyze(history)
    status = betting.get_status()
    
    text = (
        f"🎯 *预测分析*\n\n"
        f"📍 第 {latest['periodsNumber']} 期: {latest['openNum']}\n\n"
        f"🎯 大小: {'🔴大' if pred['size']['pred']=='大' else '🔵小'} ({pred['size']['conf']}%)\n"
        f"🎯 单双: {'🔺单' if pred['parity']['pred']=='单' else '🔻双'} ({pred['parity']['conf']}%)\n\n"
        f"💰 建议: {status['next_bet']} (马丁{status['martin_level']}层)"
    )
    
    await query.message.reply_text(text, parse_mode='Markdown')

async def stat_callback(query, count):
    """统计回调"""
    history = await fetch_data(count)
    if not history:
        await query.message.reply_text("❌ 数据获取失败")
        return
    
    big = sum(1 for h in history if h['openNum'] >= 14)
    odd = sum(1 for h in history if h['openNum'] % 2 == 1)
    
    text = (
        f"📊 *{count}期统计*\n\n"
        f"🔴大: {big} | 🔵小: {count-big}\n"
        f"🔺单: {odd} | 🔻双: {count-odd}"
    )
    
    await query.message.reply_text(text, parse_mode='Markdown')

async def betting_callback(query):
    """资金回调"""
    status = betting.get_status()
    text = (
        f"💰 *资金状态*\n\n"
        f"💵 资金: {status['capital']:.1f}\n"
        f"📊 盈亏: {status['profit_rate']:.1f}%\n"
        f"🎯 胜率: {status['win_rate']:.1f}%\n"
        f"🔄 马丁: {status['martin_level']}层"
    )
    await query.message.reply_text(text, parse_mode='Markdown')

async def backtest_callback(query):
    """回测回调"""
    history = await fetch_data(100)
    if len(history) < 50:
        await query.message.reply_text("❌ 数据不足")
        return
    
    size_hits = parity_hits = tests = 0
    
    for i in range(min(50, len(history) - 30)):
        test_data = history[i+1:i+31]
        actual = history[i]
        pred = PredictionEngine.analyze(test_data)
        
        if pred:
            tests += 1
            if pred['size']['pred'] == ('大' if actual['openNum'] >= 14 else '小'):
                size_hits += 1
            if pred['parity']['pred'] == ('单' if actual['openNum'] % 2 == 1 else '双'):
                parity_hits += 1
    
    text = (
        f"📈 *回测分析*\n\n"
        f"🎯 大小: {size_hits/tests*100:.1f}%\n"
        f"🎯 单双: {parity_hits/tests*100:.1f}%"
    )
    
    await query.message.reply_text(text, parse_mode='Markdown')

async def auto_push(context: ContextTypes.DEFAULT_TYPE):
    """自动推送"""
    if not CHAT_ID:
        return
    
    history = await fetch_data(50)
    if not history:
        return
    
    latest = history[0]
    pred = PredictionEngine.analyze(history)
    
    text = (
        f"🔔 *自动推送*\n\n"
        f"📍 第 {latest['periodsNumber']} 期: {latest['openNum']}\n\n"
        f"🎯 下期预测:\n"
        f"• 大小: {'🔴大' if pred['size']['pred']=='大' else '🔵小'} ({pred['size']['conf']}%)\n"
        f"• 单双: {'🔺单' if pred['parity']['pred']=='单' else '🔻双'} ({pred['parity']['conf']}%)"
    )
    
    try:
        await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"推送失败: {e}")

def main():
    """主函数"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # 命令处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("stat30", stat30))
    app.add_handler(CommandHandler("stat100", stat100))
    app.add_handler(CommandHandler("backtest", backtest))
    app.add_handler(CommandHandler("betting", betting_status))
    app.add_handler(CommandHandler("win", win))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # 定时任务
    if CHAT_ID:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            lambda: asyncio.create_task(auto_push(app)),
            'cron',
            minute='1,4,7,10,13,16,19,22,25,28,31,34,37,40,43,46,49,52,55,58',
            max_instances=1
        )
        scheduler.start()
    
    logger.info("🚀 PC28机器人启动成功!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":   
    main()
