import asyncio
from aiogram import Bot, Dispatcher, F
from handlers import router

# создаем два экземпляра класса, просто два объекта
bot = Bot(token='8075714721:AAF053-mBOuGP_AxzPUXeaLhABQM04CIgJE')
dp = Dispatcher() # обрабатывает входящие сообщения


# ту особо ничего, просто запуск бота

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен')
