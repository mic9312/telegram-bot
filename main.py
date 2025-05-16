import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

# ─── 加载环境变量 ───
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ─── 初始化 FastAPI 和 Telegram 应用 ───
app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ─── 指令 /start ───
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 Ai Captain Bot 🤖")

application.add_handler(CommandHandler("start", start))

# ─── 意图识别函数 ───
def detect_intent(user_input: str) -> str:
    user_input = user_input.lower()
    if "价格" in user_input or "how much" in user_input or "harga" in user_input:
        return "price"
    elif "预约" in user_input or "book" in user_input:
        return "book"
    return None

# ─── 自动回复消息 ───
async def reply_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    intent = detect_intent(text)
    if intent == "price":
        await update.message.reply_text("我们的价格如下：RM180/30分钟，RM250/1小时～")
    elif intent == "book":
        await update.message.reply_text("请告诉我您想预约的技师和时间，例如：预约 Mymy 下午3点 @Ampang")
    else:
        await update.message.reply_text("🤖 我还不太明白您的意思，请输入“价格”或“预约”等关键词试试看～")

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_all))

# ─── Webhook 接收端 ───
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}