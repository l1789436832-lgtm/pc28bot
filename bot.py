"""
加拿大28预测机器人 - 主程序
"""
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

from config import config
from logger import logger
from data_fetcher import data_fetcher
from predictor import predictor
from message_handler import message_handler
from scheduler import task_scheduler


class Canada28Bot:
    def __init__(self):
        self.application = None
        self.start_time = datetime.now()
        self.last_prediction = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        logger.info(f"用户 {user.id} 启动机器人")
        await update.message.reply_text(config.WELCOME_MESSAGE, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(config.HELP_MESSAGE, parse_mode='HTML')
    
    async def latest_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔄 正在获取最新数据...")
        data = await data_fetcher.fetch_latest_data()
        if data:
            message = message_handler.format_latest_result(data)
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ 获取数据失败，请稍后重试")
    
    async def predict_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔄 正在分析数据...")
        history = await data_fetcher.fetch_history_data(50)
        if history:
            predictor.update_history(history)
            prediction = predictor.predict_next()
            self.last_prediction = prediction
            message = message_handler.format_prediction(prediction)
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ 获取数据失败，无法生成预测")
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🔄 正在获取历史记录...")
        history = await data_fetcher.fetch_history_data(10)
        if history:
            message = message_handler.format_history(history)
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ 获取历史数据失败")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        history = await data_fetcher.fetch_history_data(50)
        stats = predictor.get_stats()
        message = message_handler.format_stats(stats, history)
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if message_handler.add_subscriber(user_id):
            await update.message.reply_text("✅ 订阅成功！\n\n您将收到：\n• 🎰 新开奖结果推送\n• 🔮 下期预测推送\n\n使用 /unsubscribe 取消订阅")
        else:
            await update.message.reply_text("ℹ️ 您已经订阅过了")
    
    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if message_handler.remove_subscriber(user_id):
            await update.message.reply_text("✅ 已取消订阅")
        else:
            await update.message.reply_text("ℹ️ 您还没有订阅")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not config.is_admin(user_id):
            await update.message.reply_text("⛔ 无权限")
            return
        
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        data = await data_fetcher.fetch_latest_data()
        api_status = "✅ 正常" if data else "❌ 异常"
        scheduler_status = task_scheduler.get_status()
        
        status = {
            'uptime': f"{hours}小时{minutes}分{seconds}秒",
            'subscribers': len(message_handler.get_subscribers()),
            'last_update': scheduler_status.get('last_check_time', '未知'),
            'api_status': api_status
        }
        message = message_handler.format_status(status)
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not config.is_admin(user_id):
            await update.message.reply_text("⛔ 无权限")
            return
        
        if not context.args:
            await update.message.reply_text("用法: /broadcast <消息内容>")
            return
        
        message = " ".join(context.args)
        subscribers = message_handler.get_subscribers()
        success = 0
        failed = 0
        
        for sub_id in subscribers:
            try:
                await context.bot.send_message(chat_id=sub_id, text=f"📢 <b>系统通知</b>\n\n{message}", parse_mode='HTML')
                success += 1
            except:
                failed += 1
        
        await update.message.reply_text(f"✅ 广播完成\n成功: {success}\n失败: {failed}")
    
    async def check_and_push(self):
        try:
            new_data = await data_fetcher.check_new_data()
            if new_data:
                logger.info(f"发现新开奖: {new_data.get('period')}")
                
                if self.last_prediction:
                    predictor.record_result(self.last_prediction, new_data)
                
                history = await data_fetcher.fetch_history_data(50)
                if history:
                    predictor.update_history(history)
                    prediction = predictor.predict_next()
                    self.last_prediction = prediction
                else:
                    prediction = None
                
                subscribers = message_handler.get_subscribers()
                if subscribers:
                    push_message = message_handler.format_push_message(new_data, prediction)
                    for user_id in subscribers:
                        try:
                            await self.application.bot.send_message(chat_id=user_id, text=push_message, parse_mode='HTML')
                        except Exception as e:
                            logger.error(f"推送失败 {user_id}: {e}")
                    logger.info(f"推送完成，共 {len(subscribers)} 个用户")
        except Exception as e:
            logger.error(f"检查推送异常: {e}")
    
    async def post_init(self, application: Application):
        commands = [
            BotCommand("start", "开始使用"),
            BotCommand("help", "帮助信息"),
            BotCommand("latest", "最新开奖"),
            BotCommand("predict", "获取预测"),
            BotCommand("history", "历史记录"),
            BotCommand("stats", "统计数据"),
            BotCommand("subscribe", "订阅推送"),
            BotCommand("unsubscribe", "取消订阅"),
        ]
        await application.bot.set_my_commands(commands)
        
        task_scheduler.init_scheduler()
        task_scheduler.set_check_callback(self.check_and_push)
        task_scheduler.add_check_job(config.CHECK_INTERVAL)
        task_scheduler.start()
        
        logger.info("机器人初始化完成")
    
    def run(self):
        logger.info("正在启动机器人...")
        
        self.application = Application.builder().token( "8691919071:AAGdwFG_Sh-EWW31FkrOZa3jLdw0v_V8YDc").post_init(self.post_init).build()
        
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("latest", self.latest_command))
        self.application.add_handler(CommandHandler("predict", self.predict_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("unsubscribe", self.unsubscribe_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        
        logger.info("机器人启动成功！")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    bot = Canada28Bot()
    bot.run()


if __name__ == "__main__":
    main()
