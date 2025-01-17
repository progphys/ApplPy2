from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import aiohttp
from states import Profile, WaterLogStates,FoodLogStates
from external_func import get_current_temperature_async,fetch_product_calories
from config import WEATHER_TOKEN
# Глобальная переменная для хранения данных в памяти
GLOBAL_DATA = {
    "Weight": 0,  # Вес пользователя в кг
    "Height": 0,  # Рост пользователя в см
    "Age": 0,     # Возраст пользователя в годах
    "Activity": 0, # Минуты активности в день
    "City": "",    # Город проживания пользователя
    "water_goal": 0,  # Цель по потреблению воды (мл)
    "calorie_goal": 0,  # Цель по калориям
    "water_drank": 0,  # Выпитое количество воды (мл)
    "food_ate": 0,      # Потребленные калории
    "calories_burned":0 #Соженно калорий
}

WORKOUTS = {
    "бег": 10,     
    "ходьба": 5,   
    "плавание": 8, 
    "йога": 4,
    "борьба":15
}

router = Router()

#Обработка команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать в мега-приложение по подсчету калорий")

#Обработка команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "Доступные команды:\n"
        "/start - Начало работы\n"
        "/set_profile - Установка параметров человека а\n"
        "/log_water - Сохраняет сколько воды выпито\n"
        "/log_food- Получение информации о продукте и сохранение его калорийности\n"
        "/log_workout - Фиксирует соженные калории, учет расхода воды" 
        "/check_progress - Показывает сколько воды и калорий потреблено, соженно и сколько осталось до цели"
    )   
#FSM-диалог по установке профиля
@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес:")
    await state.set_state(Profile.Weight)
@router.message(Profile.Weight)
async def set_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text)
        if weight <= 0 or weight > 500:
            raise ValueError("Вес должен быть в диапазоне от 1 до 500 кг.")
        await state.update_data(Weight=weight)
        await message.reply("Введите ваш рост (в см):")
        await state.set_state(Profile.Height)
    except ValueError:
        await message.reply("Неверный ввод. Пожалуйста, введите ваш вес числом в диапазоне от 1 до 500.")


@router.message(Profile.Height)
async def set_height(message: Message, state: FSMContext):
    try:
        height = float(message.text)
        if height <= 50 or height > 280:
            raise ValueError("Рост должен быть в диапазоне от 50 до 300 см.")
        await state.update_data(Height=height)
        await message.reply("Введите ваш возраст (в годах):")
        await state.set_state(Profile.Age)
    except ValueError:
        await message.reply("Неверный ввод. Пожалуйста, введите ваш рост числом в диапазоне от 50 до 300.")


@router.message(Profile.Age)
async def set_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age < 1 or age > 120:
            raise ValueError("Возраст должен быть в диапазоне от 1 до 120 лет.")
        await state.update_data(Age=age)
        await message.reply("Сколько минут активности у вас в день?")
        await state.set_state(Profile.Activity)
    except ValueError:
        await message.reply("Неверный ввод. Пожалуйста, введите ваш возраст числом от 1 до 120.")


@router.message(Profile.Activity)
async def set_activity(message: Message, state: FSMContext):
    try:
        activity = int(message.text)
        if activity < 0 or activity > 1440:
            raise ValueError("Минуты активности должны быть в диапазоне от 0 до 1440.")
        await state.update_data(Activity=activity)
        await message.reply("Введите ваш город:")
        await state.set_state(Profile.City)
    except ValueError:
        await message.reply("Неверный ввод. Пожалуйста, введите количество минут активности числом от 0 до 1440.")

@router.message(Profile.City)
async def set_city(message: Message, state: FSMContext):
    global GLOBAL_DATA
    city = message.text.strip()
    try:
        if len(city) < 2:
            await message.reply("Название города должно содержать хотя бы 2 символа. Попробуйте снова.")
            return
        await state.update_data(City=city)
        try:
            Temp = (await get_current_temperature_async(city, WEATHER_TOKEN))[0]
        except Exception as e:
            await message.reply(f"Ошибка получения данных о температуре для города {city}. Проверьте название города.")
            return
        additional_water = 0
        if Temp >= 25:
            additional_water = (float(Temp) - 25) / 25 * 200 + 500
        else:
            additional_water = 0
        GLOBAL_DATA.update(await state.get_data())
        GLOBAL_DATA['water_goal'] = (
            30 * GLOBAL_DATA['Weight'] + 500 * GLOBAL_DATA['Activity'] / 30 + additional_water
        )
        GLOBAL_DATA['calorie_goal'] = (
            10 * GLOBAL_DATA['Weight'] + 6.25 * GLOBAL_DATA['Height'] - 5 * GLOBAL_DATA['Age'] + 200
        )
        await message.reply(f"Ваши цели:\n"
                            f"Вода: {GLOBAL_DATA['water_goal']:.2f} мл\n"
                            f"Калории: {GLOBAL_DATA['calorie_goal']:.2f} ккал\n")
        await state.clear()
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}. Попробуйте снова.")
        return

@router.message(Command("log_water"))
async def log_water(message: Message,state: FSMContext):
    await message.reply("Сколько ж ты выпил, малыш!")
    await state.set_state(WaterLogStates.waiting_for_water_amount)

@router.message(WaterLogStates.waiting_for_water_amount)
async def print_log_water(message: Message, state: FSMContext):
    global GLOBAL_DATA
    try:
        GLOBAL_DATA['water_drank'] += float(message.text)
        remaining = GLOBAL_DATA['water_goal'] - GLOBAL_DATA['water_drank']
        await message.reply(f'Было выпито: {message.text}, осталось выпить {remaining} мл.')
        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введи число, малыш!")


@router.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    global GLOBAL_DATA
    try:
        args = message.text.split(" ", 1)
        if len(args) < 2:
            await message.reply("Пожалуйста, укажите название продукта. Пример: /log_food яблоко")
            return
        product_name = args[1].strip()
        if not product_name:
            await message.reply("Название продукта не может быть пустым. Попробуйте снова.")
            return
        try:
            calories = await fetch_product_calories(product_name)
        except Exception as e:
            await message.reply(f"Ошибка при запросе данных о продукте: {str(e)}")
            return
        if calories > 0:
            await state.update_data(product_name=product_name, calories=calories)
            await message.reply(
                f"Продукт '{product_name}' найден. Калорийность: {calories} ккал на 100г.\n"
                f"Сколько грамм вы употребили?"
            )
            await state.set_state(FoodLogStates.waiting_for_grams)
        else:
            await message.reply(f"Не удалось найти продукт '{product_name}'. Попробуйте уточнить название.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}. Попробуйте снова.")

@router.message(FoodLogStates.waiting_for_grams)
async def log_food_grams(message: Message, state: FSMContext):
    try:
        grams = float(message.text)
        if grams <= 0:
            raise ValueError("Вес должен быть положительным числом.")
        data = await state.get_data()
        product_name = data["product_name"]
        calories = data["calories"]
        total_calories = (calories / 100) * grams

        # Обновляем глобальные данные
        GLOBAL_DATA["food_ate"] = GLOBAL_DATA.get("food_ate", 0) + total_calories

        await message.reply(
            f"Вы добавили {grams} г '{product_name}' ({total_calories:.2f} ккал).\n"
            f"Общее потребление калорий: {GLOBAL_DATA['food_ate']:.2f} ккал."
        )
        await state.clear()
    except ValueError:
        await message.reply("Пожалуйста, введите положительное число для веса продукта.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {str(e)}. Попробуйте снова.")

@router.message(Command("log_workout"))
async def log_workout(message: Message):
    global GLOBAL_DATA
    args = message.text.split(" ", 2) 
    if len(args) < 3:
        await message.reply("Пожалуйста, укажите тип тренировки и время. Пример: /log_workout бег 30")
        return
    workout_type = args[1].lower()  # Тип тренировки
    try:
        workout_time = int(args[2]) 
        if workout_time <= 0:
            raise ValueError("Время должно быть положительным числом.")
    except ValueError:
        await message.reply("Пожалуйста, укажите корректное время в минутах. Пример: /log_workout бег 30")
        return
    if workout_type not in WORKOUTS:
        available_workouts = ", ".join(WORKOUTS.keys())
        await message.reply(f"Неизвестный тип тренировки '{workout_type}'. Доступные типы: {available_workouts}")
        return
    calories_burned = WORKOUTS[workout_type] * workout_time
    GLOBAL_DATA["calories_burned"] += calories_burned
    additional_water = (workout_time // 30) * 200
    GLOBAL_DATA["water_goal"] += additional_water
    await message.reply(
        f"🏃‍♂️ {workout_type.capitalize()} {workout_time} минут — {calories_burned} ккал.\n"
        f"Дополнительно: выпейте {additional_water} мл воды.\n"
    )

@router.message(Command("check_progress"))
async def check_progress(message: Message):
 
    water_goal = GLOBAL_DATA.get("water_goal", 0)
    water_drank = GLOBAL_DATA.get("water_drank", 0)
    calorie_goal = GLOBAL_DATA.get("calorie_goal", 0)
    food_ate = GLOBAL_DATA.get("food_ate", 0)
    calories_burned = GLOBAL_DATA.get("calories_burned", 0)

    water_remaining = max(water_goal - water_drank, 0)
    calorie_balance = max(calorie_goal + food_ate - calories_burned, 0)

    progress_message = (
        "📊 <b>Прогресс:</b>\n\n"
        "<b>Вода:</b>\n"
        f"- Выпито: {water_drank} мл из {water_goal} мл.\n"
        f"- Осталось выпить: {water_remaining} мл.\n\n"
        "<b>Калории:</b>\n"
        f"- Потреблено: {food_ate} ккал из {calorie_goal} ккал.\n"
        f"- Сожжено: {calories_burned} ккал.\n"
        f"- Осталось съесть: {calorie_balance} ккал.\n"
    )
    await message.reply(progress_message, parse_mode="HTML")
