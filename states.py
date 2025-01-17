from aiogram.fsm.state import State, StatesGroup
class Profile(StatesGroup):
    Weight = State()
    Height = State()
    Age = State()
    Activity = State()
    City = State()

class WaterLogStates(StatesGroup):
    waiting_for_water_amount = State()

class FoodLogStates(StatesGroup):
    waiting_for_grams = State()