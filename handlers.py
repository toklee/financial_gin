from datetime import datetime, time, timedelta
from aiogram import Bot, F, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import keyboard as kb
import sqlite3
import asyncio
import re
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())

router = Router()


class Register(StatesGroup):
    name = State()
    birth = State()
    phone = State()
    email = State()


class TransactionStates(StatesGroup):
    AMOUNT = State()


class GoalStates(StatesGroup):
    AMOUNT = State()


class SettingsStates(StatesGroup):
    CHOOSE_OPTION = State()
    UPDATE_USER_DATA = State()
    UPDATE_GOAL = State()


def get_settings_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Изменить данные")],
            [KeyboardButton(text="🎯 Изменить цель")],
            [KeyboardButton(text="📊 Все траты")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        persistent=True
    )


async def execute_sql(query, params=()):
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"SQL error: {e}")
        return False
    finally:
        conn.close()


async def fetch_sql(query, params=()):
    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"SQL error: {e}")
        return None
    finally:
        conn.close()


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


async def reset_state(state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()


async def check_auth(message: Message, state: FSMContext) -> bool:
    user = await fetch_sql("SELECT password_hash FROM users WHERE user_id = ?", (message.from_user.id,))
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь через /register.")
        return False

    auth_data = await state.get_data()
    if auth_data.get("authenticated"):
        return True

    await message.answer("🔐 Введите пароль для доступа:", reply_markup=kb.remove_keyboard)
    await state.set_state("waiting_for_password")
    return False

@router.message(F.state == "waiting_for_password")
async def handle_password_input(message: Message, state: FSMContext):
    user = await fetch_sql("SELECT password_hash FROM users WHERE user_id = ?", (message.from_user.id,))
    if not user:
        await state.clear()
        return

    if check_password(message.text, user[0][0]):
        await state.update_data(authenticated=True)
        await message.answer("✅ Доступ разрешен!", reply_markup=kb.main)
        await state.clear()
    else:
        await message.answer("❌ Неверный пароль. Попробуйте еще раз:")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await reset_state(state)
    await message.answer(
        '💰 Привет! Я Финансовый Джин - твой помощник по учету финансов.\n'
        'Для начала регистрации напиши /register',
        reply_markup=kb.main
    )


@router.message(Command('register'))
async def start_registration(message: Message, state: FSMContext):
    await reset_state(state)
    await state.set_state(Register.name)
    await message.answer("Введите ваше ФИО:", reply_markup=kb.remove_keyboard)


@router.message(Register.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.birth)
    await message.answer("Введите дату рождения (ДД.ММ.ГГГГ):")


@router.message(Register.birth)
async def process_birth(message: Message, state: FSMContext):
    await state.update_data(birth=message.text)
    await state.set_state(Register.phone)
    await message.answer("Отправьте номер телефона:", reply_markup=kb.get_number)


@router.message(Register.phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(Register.email)
    await message.answer("Введите email. Пример example@mail.ru:", reply_markup=kb.remove_keyboard)

@router.message(Register.email)
async def process_email(message: Message, state: FSMContext):
    if not is_valid_email(message.text):
        await message.answer("Некорректный email. Попробуйте еще раз:")
        return

    data = await state.get_data()
    await message.answer("🔐 Придумайте пароль для доступа к боту:")
    await state.update_data(email=message.text)
    await state.set_state(Register.password)  # Новое состояние для пароля

@router.message(Register.password)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 4:
        await message.answer("❌ Пароль должен быть не менее 4 символов. Попробуйте еще раз:")
        return

    data = await state.get_data()
    hashed_password = hash_password(password)

    success = await execute_sql(
        "INSERT INTO users (user_id, name, birth_date, phone, email, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
        (message.from_user.id, data['name'], data['birth'], data['phone'], data['email'], hashed_password)
    )

    if success:
        await message.answer(
            "✅ Регистрация завершена! Теперь при каждом входе вводите пароль.",
            f"👤 {data['name']}\n"
            f"🎂 {data['birth']}\n"
            f"📱 {data['phone']}\n"
            f"📧 {message.text}",
            reply_markup=kb.main
        )
    else:
        await message.answer("❌ Ошибка сохранения", reply_markup=kb.main)
    await state.clear()

@router.message(F.text == 'Внести траты')
async def add_expense(message: Message, state: FSMContext):
    if not await check_auth(message, state):
        return

@router.message(F.text == 'Настройки')
async def settings_menu(message: Message, state: FSMContext):
    await reset_state(state)
    await state.set_state(SettingsStates.CHOOSE_OPTION)
    await message.answer("⚙️ Настройки:", reply_markup=get_settings_keyboard())


@router.message(SettingsStates.CHOOSE_OPTION, F.text == "🔄 Изменить данные")
async def update_user_data(message: Message, state: FSMContext):
    await state.set_state(SettingsStates.UPDATE_USER_DATA)
    user_data = await fetch_sql(
        "SELECT name, birth_date, email FROM users WHERE user_id = ?",
        (message.from_user.id,)
    )

    if user_data:
        name, birth, email = user_data[0]
        await message.answer(
            f"Текущие данные:\n{name}, {birth}, {email}\n\n"
            "Введите новые данные в формате:\n"
            "ФИО, Дата рождения, Email\n\n"
            "Пример:\nИванов Иван, 01.01.1990, ivan@mail.ru",
            reply_markup=kb.remove_keyboard
        )
    else:
        await message.answer("❌ Данные не найдены", reply_markup=get_settings_keyboard())
        await state.clear()


@router.message(SettingsStates.UPDATE_USER_DATA)
async def process_update_data(message: Message, state: FSMContext):
    try:
        parts = [p.strip() for p in message.text.split(',')]
        if len(parts) != 3:
            raise ValueError("Нужно ввести 3 значения через запятую")

        name, birth, email = parts
        if not is_valid_email(email):
            raise ValueError("Некорректный email")

        success = await execute_sql(
            "UPDATE users SET name = ?, birth_date = ?, email = ? WHERE user_id = ?",
            (name, birth, email, message.from_user.id)
        )

        if success:
            await message.answer("✅ Данные обновлены!", reply_markup=kb.main)
        else:
            await message.answer("❌ Ошибка обновления", reply_markup=kb.main)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_settings_keyboard())
    finally:
        await state.clear()


@router.message(SettingsStates.CHOOSE_OPTION, F.text == "🎯 Изменить цель")
async def update_goal(message: Message, state: FSMContext):
    await state.set_state(SettingsStates.UPDATE_GOAL)
    goal = await fetch_sql(
        "SELECT target_amount FROM goals WHERE user_id = ?",
        (message.from_user.id,)
    )

    if goal:
        await message.answer(
            f"Текущая цель: {goal[0][0]} руб.\n"
            "Введите новую сумму цели:",
            reply_markup=kb.remove_keyboard
        )
    else:
        await message.answer("Введите сумму цели:", reply_markup=kb.remove_keyboard)


@router.message(SettingsStates.UPDATE_GOAL)
async def process_update_goal(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")

        daily = amount / 200
        success = await execute_sql(
            "INSERT OR REPLACE INTO goals (user_id, target_amount, daily_amount) VALUES (?, ?, ?)",
            (message.from_user.id, amount, daily)
        )

        if success:
            await message.answer(
                f"✅ Цель обновлена!\n"
                f"Ежедневно: {daily:.2f} руб.",
                reply_markup=kb.main
            )
        else:
            await message.answer("❌ Ошибка сохранения", reply_markup=kb.main)
    except ValueError:
        await message.answer("❌ Введите число (например: 10000)", reply_markup=get_settings_keyboard())
    finally:
        await state.clear()


@router.message(SettingsStates.CHOOSE_OPTION, F.text == "📊 Все траты")
async def show_expenses(message: Message):
    expenses = await fetch_sql(
        "SELECT amount, category, date FROM transactions "
        "WHERE user_id = ? AND type = 'расход' "
        "ORDER BY date DESC LIMIT 50",
        (message.from_user.id,)
    )

    if not expenses:
        await message.answer("📭 Нет данных о тратах", reply_markup=get_settings_keyboard())
        return

    total = sum(e[0] for e in expenses)
    report = ["📅 Ваши траты:", ""]

    for amount, category, date in expenses:
        report.append(f"{date}: {amount} руб. - {category}")

    report.extend(["", f"💵 Всего: {total} руб."])

    # Разбиваем на сообщения по 10 трат, если их много
    for i in range(0, len(report), 10):
        await message.answer("\n".join(report[i:i + 10]), reply_markup=get_settings_keyboard())


@router.message(SettingsStates.CHOOSE_OPTION, F.text == "🔙 Назад")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=kb.main)


@router.message(F.text == 'Внести траты')
async def add_expense(message: Message, state: FSMContext):
    await reset_state(state)
    await state.set_state(TransactionStates.AMOUNT)
    await message.answer(
        "💸 Введите сумму траты и категорию товара (например: 500 продукты). Основные категории: Еда, Транспорт, Жильё, Учёба, Развлечения, Медицина, Другое(можете ввести категорию вручную)",
        reply_markup=kb.remove_keyboard
    )


@router.message(TransactionStates.AMOUNT)
async def process_expense(message: Message, state: FSMContext):
    if message.text in ['Настройки', 'Внести траты', 'Добавить цель']:
        await state.clear()
        return

    try:
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError("Нужно ввести сумму и категорию")

        amount = float(parts[0])
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")

        category = parts[1].strip()
        if not category:
            raise ValueError("Категория не может быть пустой")

        success = await execute_sql(
            "INSERT INTO transactions (user_id, amount, category, type, date) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, amount, category, "расход", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

        if success:
            await message.answer(
                f"✅ Трата {amount} руб. на '{category}' сохранена!",
                reply_markup=kb.main
            )
        else:
            await message.answer("❌ Ошибка сохранения", reply_markup=kb.main)
    except ValueError as e:
        await message.answer(f"❌ {str(e)}\nПример: 500 продукты", reply_markup=kb.main)
    finally:
        await state.clear()


@router.message(F.text == 'Добавить цель')
async def add_goal(message: Message, state: FSMContext):
    await reset_state(state)
    await state.set_state(GoalStates.AMOUNT)
    await message.answer(
        "🎯 Введите сумму цели:",
        reply_markup=kb.remove_keyboard
    )


@router.message(GoalStates.AMOUNT)
async def process_goal(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")

        daily = amount / 200
        success = await execute_sql(
            "INSERT OR REPLACE INTO goals (user_id, target_amount, daily_amount) VALUES (?, ?, ?)",
            (message.from_user.id, amount, daily)
        )

        if success:
            asyncio.create_task(send_daily_reminder(message.from_user.id, amount, daily))
            await message.answer(
                f"✅ Цель {amount} руб. установлена!\n"
                f"Ежедневно: {daily:.2f} руб.\n"
                "Напоминания будут приходить в 19:00",
                reply_markup=kb.main
            )
        else:
            await message.answer("❌ Ошибка сохранения", reply_markup=kb.main)
    except ValueError:
        await message.answer("❌ Введите число (например: 10000)", reply_markup=kb.main)
    finally:
        await state.clear()


async def send_daily_reminder(user_id: int, goal: float, daily: float):
    bot = Bot.get_current()
    while True:
        now = datetime.now()
        target = datetime.combine(now.date(), time(19, 0))

        if now > target:
            target += timedelta(days=1)

        await asyncio.sleep((target - now).total_seconds())

        try:
            await bot.send_message(
                user_id,
                f"⏰ Напоминание!\n"
                f"Сегодня нужно отложить {daily:.2f} руб.\n"
                f"Цель: {goal} руб.",
                reply_markup=kb.main
            )
        except Exception as e:
            print(f"Ошибка напоминания: {e}")

        await asyncio.sleep(86400)  # Ждем 24 часа

@router.message(F.text == 'Статистика')
async def show_statistics(message: Message):
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    three_months_ago = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    six_months_ago = (now - timedelta(days=180)).strftime("%Y-%m-%d")
    current_date = now.strftime("%Y-%m-%d")

    # Статистика по категориям за текущий месяц
    categories = await fetch_sql(
        "SELECT category, SUM(amount) FROM transactions "
        "WHERE user_id = ? AND type = 'расход' AND strftime('%Y-%m', date) = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC",
        (message.from_user.id, current_month)
    )

    # Общие суммы за периоды
    periods = [
        ("Текущий месяц", 
         "strftime('%Y-%m', date) = ?", 
         [current_month]),
        
        ("Прошлый месяц", 
         "strftime('%Y-%m', date) = ?", 
         [last_month]),
        
        ("3 месяца", 
         "date BETWEEN ? AND ?", 
         [three_months_ago, current_date]),
        
        ("6 месяцев", 
         "date BETWEEN ? AND ?", 
         [six_months_ago, current_date])
    ]

    response = ["<b>Статистика расходов</b>\n"]

    if categories:
        response.append("\n<b>По категориям в этом месяце:</b>")
        for category, amount in categories:
            response.append(f"▪️ {category}: {amount:.2f} руб.")
    else:
        response.append("\nНет данных о расходах в этом месяце.")

    response.append("\n<b>Общие суммы:</b>")
    for period_name, condition, params in periods:
        total = await fetch_sql(
            f"SELECT SUM(amount) FROM transactions "
            f"WHERE user_id = ? AND type = 'расход' AND {condition}",
            (message.from_user.id, *params)
        )
        
        amount = total[0][0] if total and total[0][0] is not None else 0
        response.append(f"{period_name}: {amount:.2f} руб.")

    await message.answer("\n".join(response), reply_markup=kb.main)