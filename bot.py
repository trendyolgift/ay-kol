import telebot

bot = telebot.TeleBot("8261687996:AAHKxy5AuX-CS0aavPUCEllNq1MGyQ4CwDY")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Bot çalışıyor koçum.")

bot.polling()
