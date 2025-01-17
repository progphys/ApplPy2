import os
from dotenv import load_dotenv

load_dotenv() #Загружаем конфиг
TOKEN = os.getenv("BOT_TOKEN")
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN")