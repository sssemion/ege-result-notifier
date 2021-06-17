import sqlalchemy

from app.data.db_session import db


class Exam(db):
    __tablename__ = "exams"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
