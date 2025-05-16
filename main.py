import os
import json
import re
import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters

# 1. 加载环境变量
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

# 2. 加载关键词和回复映射
with open("keywords.json", "r", encoding="utf-8") as f:
    KEYWORDS = json.load(f)
with open("reply_map.json", "r", encoding="utf-8") as f:
    REPLY_MAP = json.load(f)

# 3. 意图识别函数
def detect_intent(user_input: str) -> str:
    user_input = user_input.lower()
    for intent, words in KEYWORDS.items():
        if any(keyword in user_input for keyword in words):
            return intent
    return None

# 4. 保存预约记录
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

# 5. 菜单按钮
def get_main_menu():
    keyboard = [
        ["📅 我要预约", "👩‍📫 查看技师"],
        ["📍 查地址", "💬 联系客服"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# 6. 欢迎消息
WELCOME_MESSAGE = """您好，欢迎来到小美按摩预约服务 🤖

我们提供如下服务内容（全程可镜）：
- 按摩 + 陪聊 💆‍♀️
- 房间舒适干净 🛏️
- 现金付款 💵

🕒 营业时间：每天 11am - 4am  
📍 可服务地点：Ampang / Kajang / Seremban / Mahkota

📌 请直接输入您想预约的分店和技师名字 😊"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=get_main_menu())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    await query.edit_message_text(text=f"✅ 店长操作完成：{action}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip().lower()
    match = re.search(r"(预约|book)\s*(\w+)\s*(下午|am|pm)?\s*([\d:]+)?\s*@?(\w+)?", user_text)
    if match:
        tech = match.group(2)
        time = match.group(4) or "未填写时间"
        store = match.group(5) or "未注明分店"
        username = update.message.from_user.username or update.message.from_user.first_name

        save_appointment(username, tech, time, store)
        await update.message.reply_text(f"📥 预约请求已提交：\n技师：{tech}\n时间：{time}\n分店：{store}\n\n请稍候店长确认 ✅")

        if GROUP_CHAT_ID:
            buttons = [[
                InlineKeyboardButton("✅ 接受", callback_data=f"接受预约：{username}-{tech}"),
                InlineKeyboardButton("❌ 拒绝", callback_data=f"拒绝预约：{username}-{tech}")
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"📥 新预约请求：\n客户：{username}\n技师：{tech}\n时间：{time}\n分店：{store}\n\n请确认是否接受：",
                reply_markup=reply_markup
            )
        return

    intent = detect_intent(user_text)
    if intent and intent in REPLY_MAP:
        await update.message.reply_text(REPLY_MAP[intent])
    else:
        await update.message.reply_text("🤖 我还不太明白您的意思，请输入“价格”或“预约”等关键词试试看～")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
