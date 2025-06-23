from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Настройки'), KeyboardButton(text='Внести траты')],
        [KeyboardButton(text='Добавить цель'), KeyboardButton(text='Статистика')]
    ],
    resize_keyboard=True,
    persistent=True
)

get_number = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отправить номер телефона', request_contact=True)]
    ],
    resize_keyboard=True
)

remove_keyboard = ReplyKeyboardRemove()