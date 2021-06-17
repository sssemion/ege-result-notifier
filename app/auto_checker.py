import asyncio
import logging

from app import services
from app.data.db_session import create_session
from app.data.models import User, ExamResult
from app.main import bot
from app.static import strings


async def check_for_new_results():
    await asyncio.sleep(5)
    while True:
        logging.info("AUTOCHECKER: started")
        new = 0
        with create_session() as session:
            for user in session.query(User).filter(User.status == strings.Status.AUTHORIZED.value):
                exams = services.get_exams(user.chat_id)
                if exams is None:
                    break
                for exam in exams:
                    exam_result = session.query(ExamResult).filter(ExamResult.chat_id == user.chat_id,
                                                                   ExamResult.exam_id == exam["ExamId"]).first()
                    if exam["HasResult"] and exam_result.result is None:  # В полученных данных результат есть, а в бд - нет
                        new += 1
                        exam_result.result = exam["TestMark"]
                        await bot.send_message(user.chat_id, strings.new_result.format(subject=exam_result.exam.name,
                                                                                       result=exam_result.result))
                await asyncio.sleep(1)
        logging.info(f"AUTOCHECKER: finished ({new} new results)")
        await asyncio.sleep(600)