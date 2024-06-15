import os
import dotenv
import random
import json

from database.db_connection import DBConnection
from database.models import create_tables, User, UserWord, Word

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
    db = DBConnection()
    engine = db.create_engine()
    session = db.create_session(engine)

    # create_tables(engine)
    # db.add_test_data(session=session, json=json, Word=Word)

    bot.polling()
    session.close()