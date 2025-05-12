from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import keyboard as kb

router = Router()

class Register(StatesGroup):
    name = State()
    birth = State()
    number = State()

@router.message(CommandStart()) # тут обработка конкретно для команды /start
async def cmd_start(message: Message):
    await message.answer('Привет! Я Финансовый Джин - твой друг, который поможет тебе следить за своими финансами.Давай сначала определим, каким банком ты пользуешься, а затем напиши "/register", чтобы пройти регистрацию', reply_markup=kb.main)

@router.message(Command('help')) # команда /help
async def cmd_help(message: Message):
    await message.answer('Я помогу тебе анализировать свои расходы и доходы, выделю категории покупок, на которые ты тратишь больше всего денег, а также напомню о приближающихся оплатах подписок, сотовой связи и ещё многое другое! ')

@router.message(F.text == 'Сбербанк') # если при выборе банка ответили Сбер
async def cards(message: Message):
    await message.answer('Выберите вид карты', reply_markup=kb.cards)

@router.message(F.text == 'Tinkoff') # если соответственнно Тинькоф
async def cards(message: Message):
    await message.answer('Выберите вид карты', reply_markup=kb.cards)

@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Введите ваше ФИО')

@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name = message.text)
    await state.set_state(Register.birth)
    await message.answer("Введите вашу дату рождения")

@router.message(Register.birth)
async def register_birth(message: Message, state: FSMContext):
    await state.update_data(birth = message.text)
    await state.set_state(Register.number)
    await message.answer("Введите ваш номер телефона", reply_markup=kb.get_number)

@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number = message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f'Ваше имя: {data["name"]}\nВаша дата рождения: {data["birth"]}\nНомер: {data["number"]}')
    await state.clear()

