from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete

from states.counterparty import CounterpartyCreation, ContactCreation, CounterpartyDeleteConfirm
from db.database import AsyncSessionLocal
from db.models import Counterparty, ContactPerson, BankAccount
from keyboards.counterparty import (
    get_counterparty_menu,
    get_counterparty_list_keyboard,
    get_counterparty_detail_menu,
    get_contact_list_menu,
    get_bank_account_list_menu
)

router = Router()

# ========== Вспомогательные функции ==========
def get_confirm_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, сохранить", callback_data="counterparty:save"),
            InlineKeyboardButton(text="❌ Нет, отменить", callback_data="counterparty:cancel")
        ]
    ])

def get_delete_confirm_keyboard(counterparty_id: str):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"counterparty:delete_confirm:{counterparty_id}"),
            InlineKeyboardButton(text="❌ Нет, отменить", callback_data=f"counterparty:detail:{counterparty_id}")
        ]
    ])

# ========== Список контрагентов с пагинацией ==========
@router.callback_query(F.data == "counterparty:list")
async def show_counterparty_list(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Counterparty).order_by(Counterparty.full_name)
        )
        counterparts = result.scalars().all()
    
    if not counterparts:
        await callback.message.edit_text(
            "📭 Список контрагентов пуст.",
            reply_markup=get_counterparty_menu()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "Выберите контрагента:",
        reply_markup=get_counterparty_list_keyboard(counterparts, page=0)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("counterparty:list_page:"))
async def paginate_counterparty_list(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Counterparty).order_by(Counterparty.full_name)
        )
        counterparts = result.scalars().all()
    
    await callback.message.edit_text(
        "Выберите контрагента:",
        reply_markup=get_counterparty_list_keyboard(counterparts, page)
    )
    await callback.answer()

# ========== Детальная карточка контрагента ==========
@router.callback_query(F.data.startswith("counterparty:detail:"))
async def show_counterparty_detail(callback: types.CallbackQuery):
    counterparty_id = callback.data.split(":")[2]
    async with AsyncSessionLocal() as session:
        counterparty = await session.get(Counterparty, counterparty_id)
        if not counterparty:
            await callback.answer("Контрагент не найден", show_alert=True)
            return
        # Загрузка связанных данных
        await session.refresh(counterparty, ["contact_persons", "bank_accounts"])
    
    text = f"**{counterparty.full_name}**\n"
    text += f"УНП: {counterparty.unp or 'не указан'}\n"
    text += f"Юр.адрес: {counterparty.legal_address or 'не указан'}\n"
    if counterparty.actual_address:
        text += f"Факт.адрес: {counterparty.actual_address}\n"
    if counterparty.director_full_name:
        text += f"Руководитель: {counterparty.director_full_name} ({counterparty.director_position or ''})\n"
    text += f"\nКонтактных лиц: {len(counterparty.contact_persons)}\n"
    text += f"Банковских счетов: {len(counterparty.bank_accounts)}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_counterparty_detail_menu(str(counterparty.id)),
        parse_mode="Markdown"
    )
    await callback.answer()

# ========== Контактные лица ==========
@router.callback_query(F.data.startswith("counterparty:contacts:"))
async def show_contact_list(callback: types.CallbackQuery):
    counterparty_id = callback.data.split(":")[2]
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ContactPerson).where(ContactPerson.counterparty_id == counterparty_id).order_by(ContactPerson.full_name)
        )
        contacts = result.scalars().all()
    
    if not contacts:
        text = "📭 Нет контактных лиц."
    else:
        text = "📞 **Контактные лица:**\n\n"
        for contact in contacts:
            text += f"• {contact.full_name}"
            if contact.position:
                text += f" ({contact.position})"
            if contact.phone_mobile1:
                text += f"\n  📱 {contact.phone_mobile1}"
            if contact.email1:
                text += f"\n  📧 {contact.email1}"
            text += "\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_contact_list_menu(counterparty_id),
        parse_mode="Markdown"
    )
    await callback.answer()

# ========== Банковские счета (заглушка с выводом) ==========
@router.callback_query(F.data.startswith("counterparty:bank_accounts:"))
async def show_bank_account_list(callback: types.CallbackQuery):
    counterparty_id = callback.data.split(":")[2]
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BankAccount).where(BankAccount.counterparty_id == counterparty_id)
        )
        accounts = result.scalars().all()
    
    if not accounts:
        text = "🏦 Нет банковских счетов."
    else:
        text = "🏦 **Банковские счета:**\n\n"
        for acc in accounts:
            text += f"• {acc.bank_name}"
            if acc.bic:
                text += f" (BIC {acc.bic})"
            text += f"\n  Счёт: {acc.account_number}"
            if acc.currency:
                text += f" ({acc.currency})"
            if acc.is_main:
                text += " (основной)"
            text += "\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_bank_account_list_menu(counterparty_id),
        parse_mode="Markdown"
    )
    await callback.answer()

# ========== Добавление контактного лица ==========
@router.callback_query(F.data.startswith("counterparty:add_contact:"))
async def add_contact_start(callback: types.CallbackQuery, state: FSMContext):
    counterparty_id = callback.data.split(":")[2]
    await state.update_data(counterparty_id=counterparty_id)
    await callback.message.edit_text("Введите ФИО контактного лица:")
    await state.set_state(ContactCreation.full_name)
    await callback.answer()

@router.message(StateFilter(ContactCreation.full_name))
async def process_contact_full_name(message: types.Message, state: FSMContext):
    if len(message.text) < 2:
        await message.reply("Слишком короткое имя. Введите минимум 2 символа:")
        return
    await state.update_data(full_name=message.text)
    await message.answer("Введите должность (или отправьте '—' для пропуска):")
    await state.set_state(ContactCreation.position)

@router.message(StateFilter(ContactCreation.position))
async def process_contact_position(message: types.Message, state: FSMContext):
    position = message.text if message.text != '—' else None
    await state.update_data(position=position)
    await message.answer("Введите рабочий телефон (или отправьте '—' для пропуска):")
    await state.set_state(ContactCreation.phone_work)

@router.message(StateFilter(ContactCreation.phone_work))
async def process_contact_phone_work(message: types.Message, state: FSMContext):
    phone = message.text if message.text != '—' else None
    await state.update_data(phone_work=phone)
    await message.answer("Введите мобильный телефон (или отправьте '—'):")
    await state.set_state(ContactCreation.phone_mobile)

@router.message(StateFilter(ContactCreation.phone_mobile))
async def process_contact_phone_mobile(message: types.Message, state: FSMContext):
    phone = message.text if message.text != '—' else None
    await state.update_data(phone_mobile=phone)
    await message.answer("Введите email (или отправьте '—'):")
    await state.set_state(ContactCreation.email)

@router.message(StateFilter(ContactCreation.email))
async def process_contact_email(message: types.Message, state: FSMContext):
    email = message.text if message.text != '—' else None
    await state.update_data(email=email)
    # Вывод сводки
    data = await state.get_data()
    summary = (
        f"📋 Проверьте данные контактного лица:\n"
        f"ФИО: {data['full_name']}\n"
        f"Должность: {data.get('position', '—')}\n"
        f"Раб.тел: {data.get('phone_work', '—')}\n"
        f"Моб.тел: {data.get('phone_mobile', '—')}\n"
        f"Email: {data.get('email', '—')}\n\n"
        f"Сохранить?"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="contact:save"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="contact:cancel")]
    ])
    await message.answer(summary, reply_markup=kb)
    await state.set_state(ContactCreation.confirm)

@router.callback_query(StateFilter(ContactCreation.confirm), F.data == "contact:save")
async def save_contact(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        contact = ContactPerson(
            counterparty_id=data["counterparty_id"],
            full_name=data["full_name"],
            position=data.get("position"),
            phone_work=data.get("phone_work"),
            phone_mobile1=data.get("phone_mobile"),
            email1=data.get("email")
        )
        session.add(contact)
        await session.commit()
    await callback.message.edit_text("✅ Контактное лицо добавлено!")
    await state.clear()
    # Возврат к списку контактов
    await callback.message.answer(
        "Вернуться к списку?",
        reply_markup=get_contact_list_menu(data["counterparty_id"])
    )
    await callback.answer()

@router.callback_query(StateFilter(ContactCreation.confirm), F.data == "contact:cancel")
async def cancel_contact(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("❌ Добавление отменено.")
    await state.clear()
    await callback.message.answer(
        "Вернуться к списку?",
        reply_markup=get_contact_list_menu(data["counterparty_id"])
    )
    await callback.answer()

# ========== Удаление контрагента ==========
@router.callback_query(F.data.startswith("counterparty:delete:"))
async def delete_counterparty_confirm(callback: types.CallbackQuery, state: FSMContext):
    counterparty_id = callback.data.split(":")[2]
    await state.update_data(counterparty_id=counterparty_id)
    await callback.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить этого контрагента? Это действие необратимо.",
        reply_markup=get_delete_confirm_keyboard(counterparty_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("counterparty:delete_confirm:"))
async def delete_counterparty_execute(callback: types.CallbackQuery, state: FSMContext):
    counterparty_id = callback.data.split(":")[2]
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Counterparty).where(Counterparty.id == counterparty_id))
        await session.commit()
    await callback.message.edit_text("✅ Контрагент удалён.")
    await state.clear()
    await show_counterparty_list(callback)

# ========== Создание контрагента (уже было) ==========
@router.callback_query(F.data == "counterparty:create")
async def cmd_create_counterparty(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите полное наименование контрагента (юридического лица):")
    await state.set_state(CounterpartyCreation.full_name)
    await callback.answer()

@router.message(StateFilter(CounterpartyCreation.full_name))
async def process_full_name(message: types.Message, state: FSMContext):
    if len(message.text) < 3:
        await message.reply("Название слишком короткое. Введите минимум 3 символа:")
        return
    await state.update_data(full_name=message.text)
    await message.answer("Введите УНП (9 цифр):")
    await state.set_state(CounterpartyCreation.unp)

@router.message(StateFilter(CounterpartyCreation.unp))
async def process_unp(message: types.Message, state: FSMContext):
    unp = message.text.strip()
    if not (unp.isdigit() and len(unp) == 9):
        await message.reply("УНП должен состоять из 9 цифр. Повторите ввод:")
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Counterparty).where(Counterparty.unp == unp))
        if result.scalar_one_or_none():
            await message.reply("Контрагент с таким УНП уже существует. Введите другой УНП:")
            return
    await state.update_data(unp=unp)
    await message.answer("Введите юридический адрес:")
    await state.set_state(CounterpartyCreation.legal_address)

@router.message(StateFilter(CounterpartyCreation.legal_address))
async def process_legal_address(message: types.Message, state: FSMContext):
    if len(message.text) < 5:
        await message.reply("Адрес слишком короткий. Введите более подробно:")
        return
    await state.update_data(legal_address=message.text)
    data = await state.get_data()
    summary = (
        f"📋 Проверьте введённые данные:\n"
        f"Наименование: {data['full_name']}\n"
        f"УНП: {data['unp']}\n"
        f"Юр.адрес: {data['legal_address']}\n\n"
        f"Сохранить?"
    )
    await message.answer(summary, reply_markup=get_confirm_keyboard())
    await state.set_state(CounterpartyCreation.confirm)

@router.callback_query(StateFilter(CounterpartyCreation.confirm), F.data == "counterparty:save")
async def confirm_save(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        new_counterparty = Counterparty(
            party_type="legal",
            full_name=data["full_name"],
            unp=data["unp"],
            legal_address=data["legal_address"]
        )
        session.add(new_counterparty)
        await session.commit()
        await session.refresh(new_counterparty)
    await callback.message.edit_text(f"✅ Контрагент успешно сохранён с ID: {new_counterparty.id}")
    await state.clear()
    await callback.message.answer(
        "Выберите следующее действие:",
        reply_markup=get_counterparty_menu()
    )
    await callback.answer()

@router.callback_query(StateFilter(CounterpartyCreation.confirm), F.data == "counterparty:cancel")
async def confirm_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Создание контрагента отменено.")
    await state.clear()
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_counterparty_menu()
    )
    await callback.answer()