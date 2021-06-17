from enum import Enum

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from app.static import strings


class Callback(Enum):
    VIEW_REGION_LIST = "view-region-list"
    HIDE_REGION_LIST = "hide-region-list"


view_region_list_inline = InlineKeyboardMarkup()
view_region_list_inline.add(InlineKeyboardButton(strings.view_region_list, callback_data=Callback.VIEW_REGION_LIST.value))

hide_region_list_inline = InlineKeyboardMarkup()
hide_region_list_inline.add(InlineKeyboardButton(strings.hide, callback_data=Callback.HIDE_REGION_LIST.value))

for_authorized_users = ReplyKeyboardMarkup(resize_keyboard=True)
for_authorized_users.row(KeyboardButton(strings.results), KeyboardButton(strings.logout))

for_unauthorized_users = ReplyKeyboardMarkup(resize_keyboard=True)
for_unauthorized_users.add(KeyboardButton(strings.start))
