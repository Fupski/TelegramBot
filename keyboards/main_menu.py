from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📇 Контрагенты", callback_data="menu:counterparties")],
        [InlineKeyboardButton(text="📄 Договоры", callback_data="menu:contracts")],
        [InlineKeyboardButton(text="📦 Заказы", callback_data="menu:orders")],
        [InlineKeyboardButton(text="💰 Доходы", callback_data="menu:incomes")],
        [InlineKeyboardButton(text="📊 Отчёты", callback_data="menu:reports")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)