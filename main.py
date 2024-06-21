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
from messages import Message


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
    bot.send_message(message.chat.id, Message.start_message + Message.abilities, reply_markup=show_default_buttons())

@bot.message_handler(func=lambda message: message.text == Command.EXIT)
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, Message.commands_list, reply_markup=show_default_buttons())

def show_default_buttons():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    train_btn = types.KeyboardButton(Command.TRAIN)

    buttons = [add_word_btn, delete_word_btn, train_btn]
    markup.add(*buttons)

    return markup

@bot.message_handler(func=lambda message: message.text == Command.TRAIN)
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
    exit_btn = types.KeyboardButton(Command.EXIT)
    buttons.extend([next_btn, add_word_btn, delete_word_btn, exit_btn])

    markup.add(*buttons)

    bot.send_message(message.chat.id, f'Какой перевод у слова:\n{russian_word}', reply_markup=markup)
    bot.set_state(message.from_user.id, States.target_word, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['russian_word'] = russian_word
        data['other_words'] = other_wrong_words


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    bot.send_message(message.chat.id, "Введите слово, которое хотите удалить из вашей базы знаний.🗑")
    bot.register_next_step_handler(message, delete_word_from_db)

def delete_word_from_db(message):
    check_word = session.query(Word).filter(Word.word_eng == message.text.lower().capitalize()).all()
    if check_word:
        check_userword = session.query(UserWord).filter(UserWord.word_id == check_word[0].id).first()
        if check_userword:
            kb = types.InlineKeyboardMarkup(row_width=1)
            yes_btn = types.InlineKeyboardButton(text=Message.answer_yes, callback_data='delete_yes_btn')
            no_btn = types.InlineKeyboardButton(text=Message.answer_no, callback_data='delete_no_btn')
            kb.add(yes_btn, no_btn)

            bot.send_message(message.chat.id, f'Удалить слово {check_word[0].word_eng} -> {check_word[0].word_rus}?🗑', reply_markup=kb)
            bot.set_state(message.from_user.id, States.userword, message.chat.id)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['userword'] = check_userword
        else:
            bot.send_message(message.from_user.id, f'Такого слова нет в вашей базе знаний➖', reply_markup=show_default_buttons())
    else:
        bot.send_message(message.from_user.id, f'Такого слова нет в вашей базе знаний➖', reply_markup=show_default_buttons())


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    bot.send_message(message.chat.id, 'Введите слово, которое хотите добавить.☑')
    bot.register_next_step_handler(message, add_word_to_db)

def add_word_to_db(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    yes_btn = types.InlineKeyboardButton(text=Message.answer_yes, callback_data='add_yes_btn')
    no_btn = types.InlineKeyboardButton(text=Message.answer_no, callback_data='add_no_btn')
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
        bot.send_message(message.chat.id, "Извините, я не могу добавить такое слово...", reply_markup=show_default_buttons())

@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    if callback.data == "add_yes_btn":
        with bot.retrieve_data(callback.from_user.id, callback.from_user.id) as data:
            word_eng = data['word_eng']
            word_rus = data['word_rus']

        check_word = session.query(Word).filter(Word.word_eng == word_eng).all()

        if not check_word:
            add_word_to_user(callback, word_eng, word_rus)
        else:
            check_userword = session.query(UserWord).filter(UserWord.word_id == check_word[0].id).all()

            if check_userword:
                bot.send_message(callback.from_user.id, f"Слово {word_eng} -> {word_rus} уже есть в вашей базе знаний!")
            else:
                add_word_to_user(callback, word_eng, word_rus)

    if callback.data == "delete_yes_btn":
        with bot.retrieve_data(callback.from_user.id, callback.from_user.id) as data:
            userword = data['userword']

        session.delete(userword)
        session.commit()

        bot.send_message(callback.from_user.id, "Слово успешно удалено из вашей базы знаний!")

    if callback.data == "add_no_btn" or callback.data == "delete_no_btn":
        bot.send_message(callback.from_user.id, 'Хорошо, продолжим тренировку?', reply_markup=show_default_buttons())

def add_word_to_user(callback, word_eng, word_rus):
    max_word_id = session.query(func.max(Word.id)).first()[0]
    word = Word(id=max_word_id + 1, word_eng=word_eng, word_rus=word_rus)
    session.add(word)
    session.commit()

    max_userword_id = session.query(func.max(UserWord.id)).first()[0]
    user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()

    userword = UserWord(id=max_userword_id + 1, user_id=user.id, word_id=word.id)
    session.add(userword)
    session.commit()
    bot.send_message(callback.from_user.id, f"Слово {word_eng} -> {word_rus} успешно добавлено в вашу базу знаний!")


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_word(message):
    train(message)



@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    if States.target_word:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            target_word = data['target_word']
            russian_word = data['russian_word']
            print(target_word)
            print(russian_word)

        if message.text == target_word:
            bot.send_message(message.chat.id, Message.correct_answer + f"\n{target_word}🇺🇲 -> {russian_word}🇷🇺")
            train(message)
        else:
            bot.send_message(message.chat.id, Message.incorrect_answer + f"\nПравильный ответ: {target_word}🇺🇲")
            train(message)
    else:
        bot.send_message(message.chat.id, 'Простите, я не понял что вы хотели сказать...')
        help(message)





if __name__ == '__main__':
    db = DBConnection()
    engine = db.create_engine()
    session = db.create_session(engine)

    # create_tables(engine)
    # db.add_test_data(session=session, Word=Word)

    bot.polling()
    session.close()