from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards.main_menu import get_main_menu
from keyboards.counterparty import get_counterparty_menu
from keyboards.contract import get_contract_main_menu  # импорт клавиатуры договоров

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот-бухгалтер. Выберите раздел:",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "menu:counterparties")
async def show_counterparty_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Раздел «Контрагенты». Выберите действие:",
        reply_markup=get_counterparty_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "menu:contracts")
async def show_contracts_menu(callback: types.CallbackQuery):
    """Обработчик для раздела Договоры"""
    await callback.message.edit_text(
        "📄 Раздел «Договоры». Выберите действие:",
        reply_markup=get_contract_main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Выберите раздел:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

# Заглушки для остальных разделов (ещё не реализованы)
@router.callback_query(F.data.startswith("menu:"))
async def process_other_menu(callback: types.CallbackQuery):
    await callback.answer("Этот раздел в разработке", show_alert=True)