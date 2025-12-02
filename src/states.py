from aiogram.fsm.state import State, StatesGroup


class EmailState(StatesGroup):
    waiting_for_email = State()


class AdminState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_username = State()
    waiting_for_delete_user = State()
    awaiting_broadcast_message = State()
    awaiting_gift_days = State()
