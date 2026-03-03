from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup

class CounterpartyCreation(StatesGroup):
    full_name = State()
    unp = State()
    legal_address = State()
    confirm = State()

class ContactCreation(StatesGroup):
    full_name = State()
    position = State()
    phone_work = State()
    phone_mobile = State()
    email = State()
    confirm = State()

class CounterpartyDeleteConfirm(StatesGroup):
    confirm = State()
    
def get_counterparty_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать нового", callback_data="counterparty:create")],
        [InlineKeyboardButton(text="📋 Список контрагентов", callback_data="counterparty:list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")]
    ])

def get_counterparty_list_keyboard(counterparties, page=0):
    """Формирует клавиатуру со списком контрагентов (по 5 на страницу)"""
    buttons = []
    start = page * 5
    end = start + 5
    for c in counterparties[start:end]:
        name = c.full_name[:30] + "..." if len(c.full_name) > 30 else c.full_name
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"counterparty:detail:{c.id}")])
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"counterparty:list_page:{page-1}"))
    if end < len(counterparties):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"counterparty:list_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="menu:counterparties")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_counterparty_detail_menu(counterparty_id: str):
    """Клавиатура для карточки контрагента"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Контактные лица", callback_data=f"counterparty:contacts:{counterparty_id}")],
        [InlineKeyboardButton(text="🏦 Банковские счета", callback_data=f"counterparty:bank_accounts:{counterparty_id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"counterparty:edit:{counterparty_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"counterparty:delete:{counterparty_id}")],
        [InlineKeyboardButton(text="🔙 К списку", callback_data="counterparty:list")]
    ])

def get_contact_list_menu(counterparty_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить контакт", callback_data=f"counterparty:add_contact:{counterparty_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"counterparty:detail:{counterparty_id}")]
    ])

def get_bank_account_list_menu(counterparty_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить счёт", callback_data=f"counterparty:add_bank_account:{counterparty_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"counterparty:detail:{counterparty_id}")]
    ])