import asyncio
import requests
import time
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from handlers import router
import sqlite3
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
import os

load_dotenv()  # Загружает переменные из .env
TOKEN = os.getenv("TOKEN")


# --- Инициализация Flask (для Replit 24/7) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает! Сервер активен."

def run_flask():
    app.run(host='0.0.0.0', port=8080)


# Функция для пинга 
def auto_ping():
    while True:
        try:
            requests.get("https://replit.com/@annadanilenko06/financialgin-2#main_fin_gin.py") 
            time.sleep(300)
        except:
            pass


def init_db():
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
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


async def on_startup():
    """Действия при запуске бота"""
    print("🟢 Бот запускается...")
    init_db()  
    print("✅ База данных готова к работе")
    

if __name__ == '__main__':
    init_db()
    Thread(target=run_flask, daemon=True).start()
    Thread(target=auto_ping, daemon=True).start()
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup)
 