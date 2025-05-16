import os
import json
import re
import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.ext.fastapi import get_webhook_listener

# ├─── 1. FastAPI App ───
app = FastAPI()

# ├─── 2. 加载环境变量 ───
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # 你的 Render 网址

# ├─── 3. 加载数据 ───
with open("keywords.json", "r", encoding="utf-8") as f:
    KEYWORDS = json.load(f)
with open("reply_map.json", "r", encoding="utf-8") as f:
    REPLY_MAP = json.load(f)

# ├─── 4. 定义加密功能 ───
def detect_intent(user_input: str) -> str:
    user_input = user_input.lower()
    for intent, words in KEYWORDS.items():
        if any(keyword in user_input for keyword in words):
            return intent
    return None

def save_appointment(username, tech, time, store, status="pending"):
    record = {
        "user": username,
        "technician": tech,
        "time": time,
        "branch": store,
        "status": status,
        "timestamp": datetime.datetime.now().isoformat()
    }
    path = "appointments.json"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    with open(path, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(record)
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)

WELCOME_MESSAGE = """\
🤖 您好，欢迎来到小美按摩预约服务

- 按摩 + 陪聊
- 房间舒适干净
- 现金付款

⏰ 营业时间：11am ～ 4am
📍 服务地点：Ampang / Kajang / Seremban / Mahkota

🔹 请直接输入预约的分店 + 技师名字
"""

# ├─── 5. 处理函数 ───
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    await query.edit_message_text(f"✅ 店长操作已执行：{action}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip().lower()
    match = re.search(r"(book|\u9884\u7ea6)\s*(\w+)\s*(\d+:\d+|\d+[ap]m)?\s*@?(\w+)?", user_text)
    if match:
        tech = match.group(2)
        time = match.group(3) or "未填写时间"
        store = match.group(4) or "未注明分店"
        username = update.message.from_user.username or update.message.from_user.first_name
        save_appointment(username, tech, time, store)
        await update.message.reply_text(f"✉ 预约提交成功\n技师：{tech}\n时间：{time}\n分店：{store}\n请等待店长确认")

        if GROUP_CHAT_ID:
            buttons = [[
                InlineKeyboardButton("✅ 接受", callback_data=f"接受预约：{username}-{tech}"),
                InlineKeyboardButton("❌ 拒绝", callback_data=f"拒绝预约：{username}-{tech}")
            ]]
            markup = InlineKeyboardMarkup(buttons)
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"\n✉ 新预约：{username}\n技师：{tech}\n时间：{time}\n分店：{store}\n请确认是否接受",
                reply_markup=markup
            )
        return

    intent = detect_intent(user_text)
    if intent and intent in REPLY_MAP:
        await update.message.reply_text(REPLY_MAP[intent])
    else:
        await update.message.reply_text("\ud83e\udd16 我暂时看不懂，请输入 \"\u4ef7\u683c\" \"\u9884\u7ea6\" 等关键词试试~")

# ├─── 6. Telegram Bot 应用 ───
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ├─── 7. 接入 webhook 到 FastAPI ───
webhook_listener = get_webhook_listener(application, domain=WEBHOOK_URL, path="/webhook")
app.include_router(webhook_listener, prefix="")

# └───请确保 .env 里有以下三项：
# BOT_TOKEN=xxxx
# GROUP_CHAT_ID=-100xxxx
# WEBHOOK_URL=https://your-web-url.onrender.com
