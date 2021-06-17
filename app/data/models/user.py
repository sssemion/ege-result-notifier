import sqlalchemy
from sqlalchemy import orm

from app.data.db_session import db


class User(db):
    __tablename__ = "users"

    chat_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    namehash = sqlalchemy.Column(sqlalchemy.String)
    document = sqlalchemy.Column(sqlalchemy.String)
    region = sqlalchemy.Column(sqlalchemy.Integer)
    captcha_answer = sqlalchemy.Column(sqlalchemy.String)
    captcha_token = sqlalchemy.Column(sqlalchemy.String)
    participant_cookie = sqlalchemy.Column(sqlalchemy.String)
    status = sqlalchemy.Column(sqlalchemy.Integer)

    exam_results = orm.relation("ExamResult", back_populates="user", cascade="all, delete")
