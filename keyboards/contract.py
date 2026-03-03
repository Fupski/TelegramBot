from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_contract_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать договор", callback_data="contract:create")],
        [InlineKeyboardButton(text="📋 Список договоров", callback_data="contract:list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")]
    ])

def get_counterparty_for_contract_keyboard(counterparties, page=0):
    """Клавиатура для выбора контрагента при создании договора"""
    buttons = []
    start = page * 5
    end = start + 5
    for c in counterparties[start:end]:
        name = c.full_name[:30] + "..." if len(c.full_name) > 30 else c.full_name
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"contract:choose_counterparty:{c.id.hex}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"contract:choose_page:{page-1}"))
    if end < len(counterparties):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"contract:choose_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="contract:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_contract_types_keyboard(contract_types):
    buttons = []
    for ct in contract_types:
        buttons.append([InlineKeyboardButton(text=ct.name, callback_data=f"contract:type:{ct.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="contract:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_contract_statuses_keyboard(statuses):
    buttons = []
    for s in statuses:
        buttons.append([InlineKeyboardButton(text=s.name, callback_data=f"contract:status:{s.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="contract:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_validity_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Конкретная дата", callback_data="validity:date")],
        [InlineKeyboardButton(text="⚖️ Условие (до исполнения)", callback_data="validity:condition")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="contract:main")]
    ])

def get_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Сохранить", callback_data="contract:save"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="contract:cancel")
        ]
    ])

def get_contract_list_keyboard(contracts, page=0):
    """Список договоров с пагинацией"""
    buttons = []
    start = page * 5
    end = start + 5
    for c in contracts[start:end]:
        title = f"{c.contract_number} - {c.counterparty.full_name[:20]}"
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"contract:detail:{c.id.hex}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"contract:list_page:{page-1}"))
    if end < len(contracts):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"contract:list_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="contract:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_contract_detail_menu(contract_id_hex: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📑 Этапы договора", callback_data=f"contract:stages:{contract_id_hex}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"contract:edit:{contract_id_hex}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"contract:delete:{contract_id_hex}")],
        [InlineKeyboardButton(text="🔙 К списку", callback_data="contract:list")]
    ])