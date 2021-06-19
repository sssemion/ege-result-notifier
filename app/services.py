import base64
import hashlib
import json
import logging
import os
import typing
from io import BytesIO

import requests
from fuzzywuzzy import process

from app.data.db_session import create_session
from app.data.models import User, Exam, ExamResult
from app.static import strings

with open(os.path.join(os.path.dirname(__file__), "data", "regions.json"), encoding="utf-8") as f:
    regions = json.loads(f.read())


def start(chat_id):
    with create_session() as session:
        user = session.query(User).get(chat_id)
        if user is not None:
            user.status = strings.Status.NAME.value
            user.namehash = None
            user.document = None
            user.region = None
            user.captcha_answer = None
            user.captcha_token = None
            user.participant_cookie = None
        else:
            user = User(chat_id=chat_id, status=strings.Status.NAME.value)
            session.add(user)


def is_user_authorized(chat_id) -> bool:
    with create_session() as session:
        user = session.query(User).get(chat_id)
        if user is None:
            return False
        return user.status == strings.Status.AUTHORIZED.value


def get_user_status(chat_id) -> strings.Status:
    with create_session() as session:
        user = session.query(User).get(chat_id)
        if user is None:
            return strings.Status.NOT_FOUND
        return strings.Status(user.status)


def set_name(chat_id, name) -> bool:
    if not 2 <= len(name.split()) <= 3:
        return False
    with create_session() as session:
        user = session.query(User).get(chat_id)
        namehash = hashlib.md5(name.lower().replace(" ", "").replace("ё", "е")
                               .replace("й", "и").replace("-", "").encode()).hexdigest()
        user.namehash = namehash
        user.status = strings.Status.DOCUMENT.value
        return True


def set_document(chat_id, document) -> bool:
    if len(document) not in (6, 12):
        return False
    with create_session() as session:
        user = session.query(User).get(chat_id)
        user.document = document.rjust(12, "0")
        user.status = strings.Status.REGION.value
        return True


def set_region(chat_id, region) -> bool:
    if region.isalpha():
        if len(region) < 3:
            return False
        name, rate, region = process.extractOne(region, regions)
        if rate < 50:  # Если коэффициент "сходства" строк низкий, точно определить регион невозможно
            return False
    elif region.isdigit():
        if region not in regions.keys():
            return False
    else:
        return False

    with create_session() as session:
        user = session.query(User).get(chat_id)
        user.region = int(region)
        return True


def get_region(chat_id) -> typing.Optional[str]:
    with create_session() as session:
        user = session.query(User).get(chat_id)
        if user is None or user.region is None:
            return None
        return regions[str(user.region)]


def set_captcha(chat_id) -> typing.Optional[BytesIO]:
    try:
        r = requests.get(os.environ.get("CHECK_EGE_CAPTCHA_URL"))
        if r:
            data = r.json()
        else:
            logging.error(f"CAPTCHA: {r.status_code} - {r.text}")
            return None
    except requests.exceptions.ConnectionError:
        logging.error("CAPTCHA: ConnectionError")
        return None

    with create_session() as session:
        user = session.query(User).get(chat_id)
        user.captcha_token = data["Token"]
        user.status = strings.Status.CAPTCHA.value
    img = BytesIO()
    img.write(base64.b64decode(data["Image"]))
    img.seek(0)
    return img


def set_captcha_answer(chat_id, answer) -> bool:
    if not answer.isdigit():
        return False
    with create_session() as session:
        user = session.query(User).get(chat_id)
        user.captcha_answer = answer
        return True


def log_in(chat_id) -> bool:
    with create_session() as session:
        user = session.query(User).get(chat_id)
        data = {
            "Hash": user.namehash,
            "Document": user.document,
            "Region": user.region,
            "Captcha": user.captcha_answer,
            "Token": user.captcha_token,
        }

        try:
            r = requests.post(os.environ.get("CHECK_EGE_LOGIN_URL"), data=data)
            if r:
                user.participant_cookie = r.cookies.get("Participant")
                user.status = strings.Status.AUTHORIZED.value
                return True
            else:
                if r.status_code != 401:
                    logging.error(f"AUTHORIZATION: {r.status_code} - {r.text}")
                user.status = strings.Status.AUTHORIZATION_ERROR.value
                return False
        except requests.exceptions.ConnectionError:
            logging.error("AUTHORIZATION: ConnectionError")


def save_initial_exams(chat_id) -> bool:
    exams = get_exams(chat_id)
    if exams is None:
        return False
    with create_session() as session:
        user = session.query(User).get(chat_id)
        for exam in exams:
            exam_obj = session.query(Exam).get(exam["ExamId"])
            if exam_obj is None:
                session.add(Exam(id=exam["ExamId"], name=exam["Subject"]))
            if exam["HasResult"]:
                result = ExamResult(exam_id=exam["ExamId"], result=exam["TestMark"])
            else:
                result = ExamResult(exam_id=exam["ExamId"], result=None)
            user.exam_results.append(result)
            return True


def get_exams(chat_id) -> typing.Optional[dict]:
    with create_session() as session:
        user = session.query(User).get(chat_id)
        headers = {
            "Cookie": f"Participant={user.participant_cookie}",
            "User-Agent": os.environ.get("USER_AGENT"),
        }
        try:
            r = requests.get(os.environ.get("CHECK_EGE_EXAM_URL"), headers=headers)
            if r:
                return r.json()["Result"]["Exams"]
            else:
                logging.error(f"EXAM: {r.status_code} {r.text} (user {chat_id})")
                return None
        except requests.exceptions.ConnectionError:
            logging.error("EXAM: ConnectionError")


def get_current_results(chat_id) -> list[dict]:
    with create_session() as session:
        user = session.query(User).get(chat_id)
        return [
            {
                "examId": exam_result.exam.id,
                "subject": exam_result.exam.name,
                "result": exam_result.result
            } for exam_result in user.exam_results
        ]


def get_text_results(chat_id) -> str:
    results = get_current_results(chat_id)
    text_results = []
    for result in results:
        if result["result"] is None:
            text_results.append(f"*{result['subject']}*: {strings.no_result_yet}")
        elif result["examId"] == int(os.environ.get("ESSAY_ID")):
            text_results.append(f"*{result['subject']}*: "
                                f"{strings.essay_passed if result['result'] else strings.essay_not_passed}")
        else:
            text_results.append(f"*{result['subject']}*: {result['result']}")
    return "\n".join(text_results)


def delete_user(chat_id):
    with create_session() as session:
        user = session.query(User).get(chat_id)
        session.delete(user)


def get_region_list_text() -> str:
    return strings.view_region_list + "\n\n" + "\n".join([
        f"*{k}* - {v}"
        for k, v in regions.items()
    ])
