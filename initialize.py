from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from apikeys import telegramBotToken

bot = Bot(telegramBotToken)
storage = RedisStorage2(host='localhost', port=6379, db=1)
dp = Dispatcher(bot, storage=storage)
