import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from handlers import router
import sqlite3
import os


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
            email TEXT NOT NULL,
            password_hash TEXT   
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
        token="8075714721:AAF053-mBOuGP_AxzPUXeaLhABQM04CIgJE",
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)
    

if __name__ == '__main__':
    asyncio.run(main())