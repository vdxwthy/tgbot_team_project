from aiogram.fsm.state import State, StatesGroup

class MovieStates(StatesGroup):
    waiting_for_movie_search = State()
    waiting_for_movie_summary = State()
    waiting_for_genre_text = State()
