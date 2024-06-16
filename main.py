import os
import dotenv
import random
import telebot

from telebot import types
from database.db_connection import DBConnection
from database.models import create_tables, User, UserWord, Word
from sqlalchemy import func
from command import Command
from states import States
from translate import Translator


dotenv.load_dotenv()
bot_token = os.getenv('TOKEN')

bot = telebot.TeleBot(bot_token)

@bot.message_handler(commands=['start'])
def start(message):
    telegram_user_id = message.chat.id

    if not session.query(User).filter(User.telegram_id == telegram_user_id).first():
        user = User(telegram_id=telegram_user_id)
        session.add(user)
        session.commit()

        for i in range(1, 11):
            userword = UserWord(user_id=user.id, word_id=i)
            session.add(userword)

        session.commit()
        bot.send_message(message.chat.id,"Привет 👋 Давай попрактикуемся в английском языке. Тренировки можешь проходить в удобном для себя темпе.\nУ тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения. Для этого воспрользуйся инструментами:\nдобавить слово ➕,\nудалить слово 🔙.\nНу что, начнём ⬇️")
    else:
        bot.send_message(message.chat.id,"Привет 👋 Давай попрактикуемся в английском языке. Тренировки можешь проходить в удобном для себя темпе.\nУ тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения. Для этого воспрользуйся инструментами:\nдобавить слово ➕,\nудалить слово 🔙.\nНу что, начнём ⬇️")


@bot.message_handler(commands=['train'])
def train(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)

    random_userword_word_id = session.query(UserWord.word_id).order_by(func.random()).first()[0]

    russian_word = session.query(Word.word_rus).where(Word.id == random_userword_word_id).first()[0]
    target_word = session.query(Word.word_eng).where(Word.id == random_userword_word_id).first()[0]

    target_word_btn = types.KeyboardButton(target_word)

    other_wrong_words = session.query(Word.word_eng).where(Word.id != random_userword_word_id).order_by(func.random()).all()[:3]
    other_wrong_words_buttons = [types.KeyboardButton(word[0]) for word in other_wrong_words]

    buttons = other_wrong_words_buttons + [target_word_btn]
    random.shuffle(buttons)

    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    bot.send_message(message.chat.id, f'Какой перевод у слова:\n{russian_word}', reply_markup=markup)
    bot.set_state(message.from_user.id, States.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['russian_word'] = russian_word
        data['other_words'] = other_wrong_words


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    bot.send_message(message.chat.id, 'Введите слово, которое хотите добавить')
    bot.register_next_step_handler(message, add_word_to_db)

def add_word_to_db(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    yes_btn = types.InlineKeyboardButton(text='Да', callback_data='yes_btn')
    no_btn = types.InlineKeyboardButton(text='Нет', callback_data='no_btn')
    kb.add(yes_btn, no_btn)

    translator = Translator(from_lang="en", to_lang="ru")

    word_eng = message.text.lower().capitalize()
    word_rus = translator.translate(word_eng)

    if word_eng != word_rus:
        bot.send_message(message.chat.id, f'Добавить слово {word_eng} -> {word_rus}?', reply_markup=kb)
        bot.set_state(message.from_user.id, States.word_eng, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['word_eng'] = word_eng
            data['word_rus'] = word_rus
    else:
        bot.send_message(message.chat.id, "Извините, я не могу добавить такое слово...")

@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    if callback.data == "yes_btn":
        with bot.retrieve_data(callback.from_user.id, callback.from_user.id) as data:
            word_eng = data['word_eng']
            word_rus = data['word_rus']

        check_word = session.query(Word).filter(Word.word_eng == word_eng).all()

        if not check_word:
            word = Word(word_eng=word_eng, word_rus=word_rus)
            session.add(word)
            session.commit()

            userword = UserWord(user_id=callback.from_user.id, word_id=word.id)
            session.add(userword)
            session.commit()
            bot.send_message(f"Слово {word_eng} -> {word_rus} успешно добавлено в вашу базу знаний!")


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_word(message):
    train(message)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data.get('target_word')
        russian_word = data.get('russian_word')

    if message.text == target_word:
        bot.send_message(message.chat.id, f"Всё верно!\n{target_word} -> {russian_word}")
    else:
        bot.send_message(message.chat.id, f"Ответ неверный!\nПравильный ответ: {target_word}")


if __name__ == '__main__':
    db = DBConnection()
    engine = db.create_engine()
    session = db.create_session(engine)

    create_tables(engine)
    db.add_test_data(session=session, Word=Word)

    bot.polling()
    session.close()