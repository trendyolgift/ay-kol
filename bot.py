import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8403692094:AAGM3PBAgHp4OYV4ZghC92p9ytml5aaSv1g"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("🌐 Ayık Ol Web", url="https://beachcumen.github.io/ay-kol/")
    markup.add(button)
    
    msg = (
        "Hoş geldin. Ayık Ol Botu aktif.\n"
        "Aşağıdaki butondan aradığın şeye ulaşabilirsin.\n"
        "Ayık ol, yeter.\n\n"
        "İyi eğlenceler. 👁️"
    )
    
    bot.send_message(message.chat.id, msg, reply_markup=markup)

bot.polling()
