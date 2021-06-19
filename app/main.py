import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv

from app import services, auto_checker
from app.data import db_session
from app.static import strings, keyboards

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    raise FileNotFoundError(".env file not found")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s:%(name)s:%(message)s"))
logger.handlers.clear()
logger.addHandler(handler)

bot = Bot(token=os.environ.get("BOT_API_TOKEN"))
dp = Dispatcher(bot)


@dp.message_handler(commands=["start"])
@dp.message_handler(regexp=strings.start)
async def send_welcome(message: types.Message):
    if services.is_user_authorized(message.chat.id):
        await message.answer(strings.start_for_authorized, parse_mode=types.ParseMode.MARKDOWN)
    else:
        await message.answer(strings.welcome, parse_mode=types.ParseMode.MARKDOWN)
        await message.answer(strings.input_name, parse_mode=types.ParseMode.MARKDOWN,
                             reply_markup=types.ReplyKeyboardRemove())
        services.start(message.chat.id)


@dp.message_handler(commands=["results"])
@dp.message_handler(regexp=strings.results)
async def send_results(message: types.Message):
    if services.is_user_authorized(message.chat.id):
        await message.answer(services.get_text_results(message.chat.id), parse_mode=types.ParseMode.MARKDOWN)
    else:
        await message.answer(strings.for_not_authorized, parse_mode=types.ParseMode.MARKDOWN)


@dp.message_handler(commands=["logout"])
@dp.message_handler(regexp=strings.logout)
async def logout(message: types.Message):
    if services.is_user_authorized(message.chat.id):
        services.delete_user(message.chat.id)
        await message.answer(strings.successfully_deleted, parse_mode=types.ParseMode.MARKDOWN,
                             reply_markup=keyboards.for_unauthorized_users)
    else:
        await message.answer(strings.for_not_authorized, parse_mode=types.ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda c: c.data == keyboards.Callback.VIEW_REGION_LIST.value)
async def view_region_list(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, services.get_region_list_text(),
                           parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboards.hide_region_list_inline)


@dp.callback_query_handler(lambda c: c.data == keyboards.Callback.HIDE_REGION_LIST.value)
async def hide_region_list(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)


@dp.message_handler()
async def handle(message: types.Message):
    status = services.get_user_status(message.chat.id)
    if status == strings.Status.NAME:
        if services.set_name(message.chat.id, message.text):
            await message.answer(strings.input_document, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await message.answer(strings.incorrect_name_format, parse_mode=types.ParseMode.MARKDOWN)
    elif status == strings.Status.DOCUMENT:
        if services.set_document(message.chat.id, message.text):
            await message.answer(strings.input_region, parse_mode=types.ParseMode.MARKDOWN,
                                 reply_markup=keyboards.view_region_list_inline)
        else:
            await message.answer(strings.incorrect_document_format, parse_mode=types.ParseMode.MARKDOWN)
    elif status == strings.Status.REGION:
        if services.set_region(message.chat.id, message.text):
            await message.answer(strings.confirm_region.format(region=services.get_region(message.chat.id)),
                                 parse_mode=types.ParseMode.MARKDOWN)
            captcha_img = services.set_captcha(message.chat.id)
            if captcha_img:
                await bot.send_photo(message.chat.id, captcha_img, caption=strings.input_captcha)
        else:
            await message.answer(strings.incorrect_region_format, parse_mode=types.ParseMode.MARKDOWN)
    elif status == strings.Status.CAPTCHA:
        if services.set_captcha_answer(message.chat.id, message.text):
            if services.log_in(message.chat.id):
                success = services.save_initial_exams(message.chat.id)
                if success:
                    await message.answer(strings.successful_authorization + services.get_text_results(message.chat.id),
                                         parse_mode=types.ParseMode.MARKDOWN, reply_markup=keyboards.for_authorized_users)
                else:
                    await message.answer(strings.authorization_denied, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(strings.authorization_error, parse_mode=types.ParseMode.MARKDOWN)
        else:
            await message.answer(strings.incorrect_captcha_format, parse_mode=types.ParseMode.MARKDOWN)
    elif status == strings.Status.AUTHORIZED:
        await message.answer(strings.for_authorized, parse_mode=types.ParseMode.MARKDOWN)
    elif status == strings.Status.AUTHORIZATION_ERROR:
        await message.answer(strings.authorization_error, parse_mode=types.ParseMode.MARKDOWN)


if __name__ == "__main__":
    db_session.global_init()
    asyncio.get_event_loop().create_task(auto_checker.check_for_new_results())
    executor.start_polling(dp, skip_updates=True)
