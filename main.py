import os
import json
from fastapi import FastAPI, Request
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

# ───── 环境变量与初始化 ─────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
WEBHOOK_SECRET_PATH = "/webhook"

app = FastAPI()
application = ApplicationBuilder().token(BOT_TOKEN).build()

# ───── 加载技师资料 ─────
if os.path.exists("therapists.json"):
    with open("therapists.json", "r", encoding="utf-8") as f:
        THERAPISTS = json.load(f)
else:
    THERAPISTS = []

# ───── 主按钮键盘 ─────
def main_menu_keyboard():
    buttons = [
        [KeyboardButton("我要预约"), KeyboardButton("查看技师")],
        [KeyboardButton("联系客服")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ───── 指令：/start ─────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用 Ai Captain Bot 🤖\n您可以点击下方按钮或输入 ‘价格’, ‘预约’, ‘技师’ 等关键词试试！",
        reply_markup=main_menu_keyboard()
    )

application.add_handler(CommandHandler("start", start))

# ───── 自动回复关键词 ─────
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(word in text for word in ["价格", "price", "多少钱", "berapa", "how much"]):
        await update.message.reply_text("我们的价格如下：RM180 起，欢迎预约！", reply_markup=main_menu_keyboard())

    elif any(word in text for word in ["预约", "book"]):
        await update.message.reply_text("请提供技师名字、时间、分店名，例如：预约 Mymy 下午3点 @Ampang", reply_markup=main_menu_keyboard())

    elif any(word in text for word in ["技师", "小姐", "girl", "therapist"]):
        await send_therapist_list(update, context)

    elif any(word in text for word in ["我要预约"]):
        await update.message.reply_text("请直接输入：预约 + 技师名字 + 时间 + 分店名，如 ‘预约 Mymy 下午3点 @Ampang’", reply_markup=main_menu_keyboard())

    elif "查看技师" in text:
        await send_therapist_list(update, context)

    elif "联系客服" in text:
        await update.message.reply_text("您可直接联系 Ai Captain，或加入我们的频道了解更多资讯。", reply_markup=main_menu_keyboard())

    elif any(word in text for word in ["hi", "嗨", "哈啰", "哈咯", "老板", "boss", "bro", "pm", "有开吗"]):
        await update.message.reply_text(
            "欢迎使用 Ai Captain Bot 🤖\n您可以点击下方按钮或输入 ‘价格’, ‘预约’, ‘技师’ 等关键词试试！",
            reply_markup=main_menu_keyboard()
        )

    elif "预约" in text and "@" in text:
        await process_booking(update, context)

    else:
        await update.message.reply_text(
            "🤖 我还不太明白您的意思，可以输入 ‘价格’, ‘预约’ 或 ‘技师’ 试试看～",
            reply_markup=main_menu_keyboard()
        )

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

# ───── 发送技师图文列表 ─────
async def send_therapist_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not THERAPISTS:
        await update.message.reply_text("暂无技师资料，敬请期待更新！")
        return
    media = []
    for t in THERAPISTS:
        caption = f"{t['name']} {t['flag']}\n{t['desc']}"
        media.append(InputMediaPhoto(media=t["photo"], caption=caption))
    await update.message.reply_media_group(media)

# ───── 解析预约格式并推送店长群 ─────
async def process_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        parts = text.split("预约")[-1].strip().split(" @")
        main_part, store = parts[0], parts[1]
        for sep in ["下午", "中午", "晚上"]:
            if sep in main_part:
                tech, time = main_part.split(sep)
                time = sep + time.strip()
                break
        else:
            tech, time = main_part, "时间不明"

        customer = update.message.from_user.first_name or "客户"

        msg = f"📌 新预约请求：\n👤 客户：{customer}\n🧖‍♀️ 技师：{tech.strip()}\n🕒 时间：{time}\n📍 分店：{store.strip()}"

        if GROUP_CHAT_ID:
            buttons = [[
                InlineKeyboardButton("✅ 接受预约", callback_data=f"accept:{customer}:{tech}:{time}:{store}"),
                InlineKeyboardButton("❌ 拒绝预约", callback_data=f"reject:{customer}:{tech}:{time}:{store}")
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await context.bot.send_message(chat_id=int(GROUP_CHAT_ID), text=msg, reply_markup=reply_markup)

        await update.message.reply_text("✅ 已收到预约，我们将尽快为您安排技师并回覆确认！")
    except:
        await update.message.reply_text("⚠️ 格式错误，请参考：预约 Mymy 下午3点 @Ampang")

# ───── 店长接受或拒绝预约按钮 ─────
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    action, customer, tech, time, store = data.split(":")
    if action == "accept":
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"✅ 店长已接受预约：{tech} - {time} @ {store}")
        # 可加：发送私聊通知给客户（待对接 ID）
    elif action == "reject":
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=f"❌ 店长拒绝了 {tech} {time} 的预约，可另荐其他技师或时段")

application.add_handler(CallbackQueryHandler(handle_callback))

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
