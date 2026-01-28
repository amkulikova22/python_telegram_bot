import asyncio
import requests
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import API_TOKEN
from dataclasses import dataclass

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


class UserInfo(StatesGroup):
    weight = State()
    height = State()
    age = State()
    activity = State()
    city = State()

class LogWater(StatesGroup):
    log_water = State()

class LogFood(StatesGroup):
    log_food = State()
    amount = State()

class LogWorkout(StatesGroup):
    log_workout = State()

@dataclass
class UserProfile:
    user_id: int
    weight: int = None
    height: int = None
    age: int = None
    activity: int = None
    city: str = None
    base_water: int = None
    drunk_water: int = 0
    food_eaten: str = None
    calories: int = 0
    total_calories: int = 0
    workout: str = None
    time: int = 0
    calories_burned: int = 0
    calories_in_food: int = 0

users: dict[int, UserProfile] = {}


@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привет! Я бот, который рассчитывает дневные нормы воды, калорий и трекает активность"
    )

@dp.message(Command("set_profile"))
async def start_profile(message: Message, state: FSMContext):
    await state.set_state(UserInfo.weight)
    user_id = message.from_user.id
    profile = users.setdefault(user_id, UserProfile(user_id=user_id))
    await message.answer("Введите ваш вес (в кг):")

@dp.message(UserInfo.weight)
async def get_weight(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    user_id = message.from_user.id
    profile = users.setdefault(user_id, UserProfile(user_id=user_id))
    weight = int(message.text)
    profile.weight = weight
    await state.set_state(UserInfo.height) 
    await message.answer("Введите ваш рост (в см):")

@dp.message(UserInfo.height)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    user_id = message.from_user.id
    profile = users.setdefault(user_id, UserProfile(user_id=user_id))
    height = int(message.text)
    profile.height = height
    await state.set_state(UserInfo.age) 
    await message.answer("Введите ваш возраст:")

@dp.message(UserInfo.age)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    user_id = message.from_user.id
    profile = users.setdefault(user_id, UserProfile(user_id=user_id))
    age = int(message.text)
    profile.age = age
    await state.set_state(UserInfo.activity) 
    await message.answer("Сколько минут активности у вас в день?")

@dp.message(UserInfo.activity)
async def get_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    user_id = message.from_user.id
    profile = users.setdefault(user_id, UserProfile(user_id=user_id))
    activity = int(message.text)
    profile.activity = activity
    await state.set_state(UserInfo.city) 
    await message.answer("В каком городе вы находитесь?")

@dp.message(UserInfo.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    user_id = message.from_user.id
    profile = users.setdefault(user_id, UserProfile(user_id=user_id))
    city = str(message.text)
    profile.city = city
    data = await state.get_data()
    await state.clear()
    await message.answer(
        f"✅ Профиль сохранен!\n\n"
        f"Ваши данные:\n"
        f"• Вес: {data.get('weight', 'не указан')} кг\n"
        f"• Рост: {data.get('height', 'не указан')} см\n"
        f"• Возраст: {data.get('age', 'не указан')} лет\n"
        f"• Активность: {data.get('activity', 'не указан')} мин/день\n"
        f"• Город: {data.get('city', 'не указан')}\n\n"
        f"Теперь используйте:\n"
        f"/water - расчет нормы воды\n"
        f"/calories - расчет калорий\n"
        f"/log_water - логирование воды"
        f"/log_food - логирование еды"
        f"/log_workout - логирование тренировок"
        f"/log_workout - логирование тренировок"
        f"/check_progress - прогресс по еде и тренировкам"
    )

api_key = "13e489d16133d222e13e602f3c726e5e"

def get_temperature(city, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'ru'
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if response.status_code == 200:
        temp = data['main']['temp']
        print(f"Температура в {city}: {temp}°C")
        return temp
    else:
        print(f"Ошибка: {data.get('message', 'Неизвестная ошибка')}")
        return None

@dp.message(Command("water"))
async def calculate_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = users.get(user_id)
    current_temperature = get_temperature(profile.city, api_key)
    bonus_for_activity = profile.activity // 30
    if current_temperature > 25:
        base_water = profile.weight * 30 + 500 * bonus_for_activity + 500
    else:
        base_water = profile.weight * 30 + 500 * bonus_for_activity
    profile.base_water = base_water
    await message.answer(f"✅ Норма воды: {base_water} мл/день) для текущей температуры {current_temperature}")

@dp.message(Command("log_water"))
async def log_water_command(message: Message, state: FSMContext):
    await state.set_state(LogWater.log_water) 
    await message.answer("Сколько воды вы сегодня выпили?")

@dp.message(LogWater.log_water)
async def water_drunk(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = users.get(user_id)
    # await state.update_data(log_water=message.text)
    drunk_water = int(message.text)
    profile.drunk_water = profile.drunk_water + drunk_water
    water_remained = profile.base_water - profile.drunk_water 
    await message.answer(
            f"✅ Записано: {drunk_water} мл\n\n"
            f"🎯 Норма: {profile.base_water} мл\n"
            f"💧 Осталось: {water_remained} мл\n"
            f"📈 Прогресс: {(drunk_water/profile.base_water*100):.1f}%"
        )
    await state.clear()

def get_calories(product):
    url = f"https://world.openfoodfacts.net/api/v2/search?categories_tags={product}&fields=nutriments"
    response = requests.get(url)

    def find_key_value(json_object, target_key):
        if isinstance(json_object, dict):
            for key, value in json_object.items():
                if key == target_key:
                    return value
                found_value = find_key_value(value, target_key)
                if found_value is not None:
                    return found_value
        elif isinstance(json_object, list):
            for item in json_object:
                found_value = find_key_value(item, target_key)
                if found_value is not None:
                    return found_value
        return None

    return find_key_value(json.loads(response.text), 'energy-kcal')

@dp.message(Command("calories"))
async def calculate_calories(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = users.get(user_id)
    calories = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age
    profile.total_calories = calories
    await message.answer(f"✅ Норма калорий: {calories}/день)")

@dp.message(Command("log_food"))
async def log_water_command(message: Message, state: FSMContext):
    await state.set_state(LogFood.log_food) 
    await message.answer("Какой продукт вы съели?")

@dp.message(LogFood.log_food)
async def food_eaten(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = users.get(user_id)
    await state.update_data(food_eaten=message.text)
    food_eaten = str(message.text)
    profile.food_eaten = food_eaten
    calories_for_banana = get_calories(food_eaten)
    profile.calories = calories_for_banana
    await message.answer(
            f"{food_eaten} содержит {calories_for_banana} на 100 г. Сколько грамм вы съели?"
        )
    await state.set_state(LogFood.amount)

@dp.message(LogFood.amount)
async def amount_of_food(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = users.get(user_id)
    await state.update_data(amount=message.text)
    amount = int(message.text)
    total_amount = amount / 100 * profile.calories
    profile.calories_in_food = profile.calories_in_food + total_amount
    await message.answer(
            f"Записано: {total_amount} ккал."
        )
    await state.clear()

@dp.message(Command("log_workout"))
async def log_water_command(message: Message, state: FSMContext):
    await state.set_state(LogWorkout.log_workout) 
    await message.answer("Укажите тип и продолжительность тренировки")

@dp.message(LogWorkout.log_workout)
async def type_of_workout(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = users.get(user_id)
    await state.update_data(log_workout=message.text)
    workout_calories_per_minute = {
        "ходьба": 4.2,
        "йога": 3.2,
        "стретчинг": 2.8,
        "пилатес": 3.5,
        "езда на велосипеде": 7.5,
        "аэробика": 6.8,
        "танцы": 5.5,
        "плавание": 8.2,
        "бег": 12.5,
        "силовая тренировка": 7.0,
        "гребля": 12.2}
    data = await state.get_data()
    splitted_data = str.split(data['log_workout'])
    type_of_activity = str(splitted_data[0])
    time = int(splitted_data[1])
    total_calories = workout_calories_per_minute[type_of_activity] * time
    profile.calories_burned = profile.calories_burned + total_calories
    await message.answer(f"Вы выполнили тренировку по {type_of_activity} и сожгли {total_calories} калорий.")
    await state.clear() 

@dp.message(Command("check_progress"))
async def progress_tracker(message: Message, state: FSMContext):
    user_id = message.from_user.id
    profile = users.get(user_id)
    balance = profile.calories_in_food - profile.calories_burned
    remained = profile.base_water - profile.drunk_water
    await message.answer(f"""📊 Прогресс:\n
    Вода:
        - Выпито: {profile.drunk_water} мл из {profile.base_water} мл.
        - Осталось: {remained} мл.
    Калории:
        - Потреблено: {profile.calories_in_food} ккал из {profile.total_calories} ккал.
        - Сожжено: {profile.calories_burned} ккал.
        - Баланс: {balance} ккал.""")

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
