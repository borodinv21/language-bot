import sqlalchemy
import os
from dotenv import load_dotenv

from sqlalchemy.orm import sessionmaker

load_dotenv()

USERNAME = os.getenv('db_USERNAME')
PASSWORD = os.getenv('db_PASSWORD')
DB_NAME = os.getenv('db_NAME')


class DBConnection:
    def __init__(self):
        self.DSN = f"postgresql://{USERNAME}:{PASSWORD}@localhost:5432/{DB_NAME}"

    def create_session(self, engine):
        Session = sessionmaker(bind=engine)
        return Session()

    def create_engine(self):
        return sqlalchemy.create_engine(self.DSN)

    def add_test_data(self, json, Word, session):
        with open('fixtures/words.json', 'r') as fd:
            data = json.load(fd)

        for record in data:
            model = {
                'word': Word,
            }[record.get('model')]
            session.add(model(id=record.get('pk'), **record.get('fields')))

        session.commit()