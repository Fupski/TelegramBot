from aiogram.fsm.state import State, StatesGroup

class ContractCreation(StatesGroup):
    select_counterparty = State()
    select_type = State()
    input_post_number = State()
    input_contract_number = State()
    select_status = State()
    input_conclusion_date = State()
    input_place = State()
    select_validity_type = State()
    input_expiry_date = State()
    input_estimated_date = State()
    input_total_amount = State()
    confirm = State()