from aiogram.dispatcher.filters.state import State, StatesGroup


class PlaceStates(StatesGroup):
    input_place = State()
    is_clicked = State()
