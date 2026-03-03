from aiogram.fsm.state import State, StatesGroup

class ContractStageCreation(StatesGroup):
    name = State()
    expected_result = State()
    confirmation_document = State()
    payment_condition = State()
    prepayment_percent = State()
    prepayment_days = State()
    final_payment_days = State()
    amount = State()
    confirm = State()