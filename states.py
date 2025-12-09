"""FSM состояния для регистрации пользователей."""
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации."""
    waiting_for_full_name = State()
    waiting_for_phone = State()
    waiting_for_plot_number = State()
    waiting_for_document = State()


class AdminSearchStates(StatesGroup):
    """Состояния для админ-поиска."""
    waiting_for_plot = State()
    waiting_for_phone = State()
    waiting_for_name = State()
    waiting_for_universal = State()

