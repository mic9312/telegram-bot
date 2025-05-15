from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ✅ 替换成你自己的 Bot Token（来自 BotFather）
BOT_TOKEN = "7813649440:AAFFr95FUq_uH5jodVDaDGopHDyQRuoEVX4"

WELCOME_MESSAGE = """您好，欢迎来到小美按摩预约服务 🤖

我们提供如下服务内容（全程可镜）：
- 按摩 + 陪聊 💆‍♀️
- 房间舒适干净 🛏️
- 现金付款 💵

🕒 营业时间：每天 11am - 4am  
📍 可服务地点：Ampang / Kajang / Seremban / Mahkota

📌 请直接输入您想预约的分店和技师名字 😊
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def reply_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_all))
    app.run_polling()

if __name__ == "__main__":
    main()
