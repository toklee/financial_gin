from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import keyboard as kb
import sqlite3
from datetime import datetime

router = Router()

class Register(StatesGroup):
    name = State()
    birth = State()
    number = State()

# Состояния для операций с бюджетом
class TransactionStates(StatesGroup):
    TYPE = State()
    AMOUNT = State()
    CATEGORY = State()


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

# Обработчик команды /budget (начало работы с бюджетом)
@router.message(Command("budget"))
async def cmd_budget(message: Message, state: FSMContext):
    await message.answer(
        "Хотите добавить доход или расход?",
        reply_markup=kb.operation_type_keyboard
    )
    await state.set_state(TransactionStates.TYPE)

@router.message(TransactionStates.TYPE, F.text.in_(["Доход", "Расход"]))
async def get_type(message: Message, state: FSMContext):
    op_type = message.text.lower()
    await state.update_data(type=op_type)
    await message.answer(
        f"Введите сумму {op_type}a:",
        reply_markup=kb.remove_keyboard
    )
    await state.set_state(TransactionStates.AMOUNT)


@router.message(TransactionStates.AMOUNT)
async def get_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        await state.update_data(amount=amount)
        data = await state.get_data()
        await message.answer(
            "Выберите категорию:",
            reply_markup=kb.get_categories_keyboard(data["type"])
        )
        await state.set_state(TransactionStates.CATEGORY)
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


@router.message(TransactionStates.CATEGORY)
async def get_category(message: Message, state: FSMContext):
    category = message.text
    data = await state.get_data()
    # Сохранение в БД
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
        (None, message.from_user.id, data['amount'], category,
         data['type'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

    await message.answer(
        f"✅ {data['type'].capitalize()} {data['amount']} руб. "
        f"в категории '{category}' сохранен!",
        reply_markup=kb.main
    )
    await state.clear()