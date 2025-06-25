import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from handlers import router
import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()  # Загружает переменные из .env

TOKEN = os.getenv("TOKEN")


def init_db():
    if os.path.exists('budget.db'):
        os.remove('budget.db')

    conn = sqlite3.connect('budget.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE goals (
            user_id INTEGER PRIMARY KEY,
            target_amount REAL NOT NULL,
            daily_amount REAL NOT NULL,
            reminder_time TEXT DEFAULT '19:00',
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')

    conn.commit()
    conn.close()


async def main():
    init_db()
    bot = Bot(
        token="TOKEN",
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


async def on_startup():
    """Действия при запуске бота"""
    print("🟢 Бот запускается...")
    if await init_db():
        print("✅ База данных готова к работе")
    else:
        print("❌ Проблемы с инициализацией БД!")


async def init_db():
    try:
        await execute_sql("CREATE TABLE IF NOT EXISTS users (...)")
        print("Таблицы созданы")
        return True
    except Exception as e:
        print(f"Ошибка инициализации БД: {e}")
        return False
    

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup)
    asyncio.run(main())
    asyncio.run(init_db())