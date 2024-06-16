from telebot.handler_backends import State, StatesGroup

class States(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()
    word_eng = State()
    word_rus = State()