import os
import dotenv
import random

import telebot
from telebot import types

dotenv.load_dotenv()
bot_token = os.getenv('TOKEN')

bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)

    russian_word = 'Яблоко'

    target_word = 'Apple'
    target_word_btn = types.KeyboardButton(target_word)

    other_wrong_words = ['Potato', 'Juice', 'Orange']
    other_wrong_words_buttons = [types.KeyboardButton(word) for word in other_wrong_words]

    buttons = other_wrong_words_buttons + [target_word_btn]
    random.shuffle(buttons)
    markup.add(*buttons)

    bot.send_message(message.chat.id, f'Какой перевод у слова:\n{russian_word}', reply_markup=markup)


if __name__ == '__main__':
    bot.polling()