from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import re

TOKEN = "9173872519:AAEXejtVRPNjJhlM4q6K5BtIETdV36LlxDY"

ADMINS = {8788829431}

warns = {}

messages = {
    "kick": "@user fantezi sırasında abarttı.",
    "ban": "@user abarttı.",
    "mute": "@user fazla konuşkan çıktı.",
    "unmute": "@user konuşmasına izin verildi.",
    "unban": "@user banı kaldırıldı, abartmaması gerek.",
    "warn1": "@user (1/3) dikkatli olmalı.",
    "warn2": "@user (2/3) biraz daha dikkatli olmalı.",
    "warn3": "@user (3/3) dikkatsiz çıktı. sessize alındı.",
    "warns_info": "@user şu an {count}/3 uyarı aldı.",
    "clearwarn_done": "@user dosya kapatıldı tahliye edildi."
}

def is_admin(uid: int):
    return uid in ADMINS

# ---------------- GET USER (ASYNC FIX) ----------------
async def get_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg and msg.reply_to_message:
        return msg.reply_to_message.from_user

    if context.args:
        arg = context.args[0]

        # Kullanıcı ID ile arama
        if arg.isdigit():
            try:
                member = await context.bot.get_chat_member(update.effective_chat.id, int(arg))
                return member.user
            except Exception:
                return None

        # Kullanıcı adı (@username) ile arama
        if arg.startswith("@"):
            try:
                chat = await context.bot.get_chat(arg)
                member = await context.bot.get_chat_member(update.effective_chat.id, chat.id)
                return member.user
            except Exception:
                return None

    return None

def fmt(text: str, user):
    name = f"@{user.username}" if user.username else user.first_name
    return text.replace("@user", name)

# ---------------- TIME PARSE ----------------
def parse_duration(text: str):
    text = text.lower()

    m = re.match(r"(\d+)([mhd])", text)
    if m:
        v = int(m.group(1))
        u = m.group(2)
        if u == "m": return v * 60
        if u == "h": return v * 3600
        if u == "d": return v * 86400

    if "saat" in text:
        return int(text.split()[0]) * 3600
    if "dakika" in text:
        return int(text.split()[0]) * 60
    if "gün" in text:
        return int(text.split()[0]) * 86400

    return None

# ---------------- UNMUTE JOB ----------------
async def unmute_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]
    user_id = job.data["user_id"]

    await context.bot.restrict_chat_member(
        chat_id,
        user_id,
        ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )

# ---------------- MUTE ----------------
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = await get_user(update, context)
    if not user:
        return

    seconds = None

    for a in context.args:
        s = parse_duration(a)
        if s:
            seconds = s

    await context.bot.restrict_chat_member(
        update.effective_chat.id,
        user.id,
        ChatPermissions(can_send_messages=False)
    )

    await update.message.reply_text(fmt(messages["mute"], user))

    if seconds:
        context.job_queue.run_once(
            unmute_job,
            seconds,
            data={
                "chat_id": update.effective_chat.id,
                "user_id": user.id
            }
        )

# ---------------- KICK ----------------
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = await get_user(update, context)
    if not user:
        return

    # Kullanıcıyı gruptan atıp hemen banını kaldırıyoruz ki tekrar katılabilsin
    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    await context.bot.unban_chat_member(update.effective_chat.id, user.id, only_if_banned=True)
    await update.message.reply_text(fmt(messages["kick"], user))

# ---------------- BAN ----------------
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = await get_user(update, context)
    if not user:
        return

    await context.bot.ban_chat_member(update.effective_chat.id, user.id)
    await update.message.reply_text(fmt(messages["ban"], user))

# ---------------- UNBAN (DÜZELTİLDİ) ----------------
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = await get_user(update, context)
    if not user:
        return

    # only_if_banned=True parametresi banın sorunsuz kalkmasını sağlar
    await context.bot.unban_chat_member(
        chat_id=update.effective_chat.id, 
        user_id=user.id, 
        only_if_banned=True
    )
    await update.message.reply_text(fmt(messages["unban"], user))

# ---------------- WARN ----------------
async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = await get_user(update, context)
    if not user:
        return

    uid = user.id
    warns[uid] = warns.get(uid, 0) + 1
    w = warns[uid]

    if w == 1:
        await update.message.reply_text(fmt(messages["warn1"], user))
    elif w == 2:
        await update.message.reply_text(fmt(messages["warn2"], user))
    else:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            uid,
            ChatPermissions(can_send_messages=False)
        )
        warns[uid] = 0
        await update.message.reply_text(fmt(messages["warn3"], user))

# ---------------- WARN INFO ----------------
async def warns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = await get_user(update, context)
    if not user:
        return

    w = warns.get(user.id, 0)
    await update.message.reply_text(
        fmt(messages["warns_info"], user).replace("{count}", str(w))
    )

# ---------------- CLEARWARN ----------------
async def clearwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    user = await get_user(update, context)
    if not user:
        return

    warns[user.id] = 0
    await update.message.reply_text(fmt(messages["clearwarn_done"], user))

# ---------------- KELİME YAKALAMA (BEACH / KUMSAL) ----------------
async def keyword_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text.lower()
        if "beach" in text or "kumsal" in text:
            await update.message.reply_text("ALLAHIN ASLANI 🦁")

# ---------------- BOT ----------------
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("kick", kick))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("warn", warn))
app.add_handler(CommandHandler("warns", warns_cmd))
app.add_handler(CommandHandler("clearwarn", clearwarn))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_response))

print("bot hızlı mode aktif")
app.run_polling()
