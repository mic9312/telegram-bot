import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from dotenv import load_dotenv

# ───── 环境变量与初始化 ─────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET_PATH = "/webhook"

app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ───── 指令：/start ─────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 Ai Captain Bot 🤖\n您可以输入 ‘价格’, ‘预约’, ‘技师’ 等关键词试试！")

application.add_handler(CommandHandler("start", start))

# ───── 自动回复关键词 ─────
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(word in text for word in ["价格", "price", "多少钱", "berapa", "how much"]):
        await update.message.reply_text("我们的价格如下：RM180 起，欢迎预约！")
    elif any(word in text for word in ["预约", "book"]):
        await update.message.reply_text("请提供技师名字、时间、分店名，例如：预约 Mymy 下午3点 @Ampang")
    elif any(word in text for word in ["技师", "小姐", "girl", "therapist"]):
        await update.message.reply_text("请点击菜单查看技师介绍，或输入技师名字。")
    else:
        await update.message.reply_text("🤖 我还不太明白您的意思，可以输入 ‘价格’, ‘预约’ 或 ‘技师’ 试试看～")

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

# ───── 设置 Webhook 地址 ─────
@app.on_event("startup")
async def on_startup():
    webhook_url = os.getenv("RENDER_EXTERNAL_URL") + WEBHOOK_SECRET_PATH
    await application.initialize()
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook 已设置为：{webhook_url}")

# ───── Webhook 接收处理 ─────
@app.post(WEBHOOK_SECRET_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}
