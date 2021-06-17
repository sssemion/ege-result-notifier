import sqlalchemy
from sqlalchemy import orm

from app.data.db_session import db


class ExamResult(db):
    __tablename__ = "exam_results"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    chat_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.chat_id"))
    exam_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("exams.id"))
    result = sqlalchemy.Column(sqlalchemy.Integer)

    user = orm.relation("User", foreign_keys=[chat_id])
    exam = orm.relation("Exam", foreign_keys=[exam_id])
