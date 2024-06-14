import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):

    id = sq.Column(sq.Integer, primary_key=True)
    telegram_id = sq.Column(sq.Integer)


class Word(Base):
    id = sq.Column(sq.Integer, primary_key=True)
    word_eng = sq.Column(sq.String(length=100), nullable=False)
    work_rus = sq.Column(sq.String(length=100), nullable=False)

