from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# тут делаем кнопочки

main = ReplyKeyboardMarkup(keyboard = [[KeyboardButton(text = 'Сбербанк')],
                                       [KeyboardButton(text = 'Tinkoff')]],
                           resize_keyboard=True, input_field_placeholder='Выберите свой банк')
cards = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text = 'Дебетовая', callback_data='Дебетовая')],
                                              [InlineKeyboardButton(text = 'Кредитная', callback_data='Кредитная')],
                                              [InlineKeyboardButton(text = 'Счёт', callback_data='Счёт')]])

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Отправить номер телефона', request_contact=True)]],
                                 resize_keyboard=True)