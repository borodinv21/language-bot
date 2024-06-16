import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    telegram_id = sq.Column(sq.Integer, nullable=False, unique=True)

    def __str__(self):
        return f'ID: {self.id} | TelegramID: {self.telegram_id}'


class Word(Base):
    __tablename__ = 'word'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    word_eng = sq.Column(sq.String(length=100), nullable=False)
    word_rus = sq.Column(sq.String(length=100), nullable=False)

    def __str__(self):
        return f'ID: {self.id} | ENG: {self.word_eng} | RUS: {self.word_rus}'


class UserWord(Base):
    __tablename__ = 'userword'

    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('user.id'), nullable=False)
    word_id = sq.Column(sq.Integer, sq.ForeignKey('word.id'), nullable=False)

    user = relationship(User, backref='userword')
    word = relationship(Word, backref='userword')

    def __str__(self):
        return f'UserTelegramID: {self.user_telegram_id} | WordID: {self.word_id}'


def create_tables(engine):
    Base.metadata.create_all(engine)
