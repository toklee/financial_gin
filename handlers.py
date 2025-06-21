from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import keyboard as kb

router = Router()

class Register(StatesGroup):
    name = State()
    birth = State()
    number = State()

# Добавим состояние для хранения выбранного банка
class BankSelection:
    selected_bank = None

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет! Я Финансовый Джин - твой друг, который поможет тебе следить за своими финансами.Давай сначала определим, каким банком ты пользуешься, а затем напиши "/register", чтобы пройти регистрацию', reply_markup=kb.main)

@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Я помогу тебе анализировать свои расходы и доходы, выделю категории покупок, на которые ты тратишь больше всего денег, а также напомню о приближающихся оплатах подписок, сотовой связи и ещё многое другое! ')

@router.message(F.text == 'Сбербанк')
async def cards(message: Message):
    BankSelection.selected_bank = 'Сбербанк'  # Сохраняем выбранный банк
    await message.answer('Выберите вид карты', reply_markup=kb.cards)

@router.message(F.text == 'Tinkoff')
async def cards(message: Message):
    BankSelection.selected_bank = 'Tinkoff'  # Сохраняем выбранный банк
    await message.answer('Выберите вид карты', reply_markup=kb.cards)

# Обработчик выбора типа карты
@router.callback_query(F.data.in_(['Дебетовая', 'Кредитная', 'Счёт']))
async def card_type_selected(callback: CallbackQuery):
    if not hasattr(BankSelection, 'selected_bank') or not BankSelection.selected_bank:
        await callback.answer("❌ Сначала выберите банк!", show_alert=True)
        return

    # Определяем правильное название карты/счёта
    card_type = callback.data.lower()
    if card_type == 'дебетовая':
        card_text = 'дебетовую карту'
    elif card_type == 'кредитная':
        card_text = 'кредитную карту'
    else:  # Счёт
        card_text = 'счёт'

    await callback.message.answer(
        f"✅ Отлично! Значит, мы будем отслеживать {card_text} в банке {BankSelection.selected_bank}."
    )
    await callback.answer()  # закрываем всплывающее уведомление

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
