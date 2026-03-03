from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_payment_conditions_keyboard(conditions):
    buttons = []
    for cond in conditions:
        buttons.append([InlineKeyboardButton(text=cond.name, callback_data=f"stage_pay_cond:{cond.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="stage:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_stage_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Сохранить", callback_data="stage:save"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="stage:cancel")
        ]
    ])

def get_stage_list_keyboard(stages, contract_id_hex: str):
    buttons = []
    for stage in stages:
        buttons.append([InlineKeyboardButton(text=stage.name, callback_data=f"stage:detail:{stage.id.hex}")])
    buttons.append([InlineKeyboardButton(text="➕ Добавить этап", callback_data=f"stage:add:{contract_id_hex}")])
    buttons.append([InlineKeyboardButton(text="🔙 К договору", callback_data=f"contract:detail:{contract_id_hex}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)