import uuid
from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime
from states.contract import ContractCreation
from states.contract_stage import ContractStageCreation
from db.database import AsyncSessionLocal
from db.models import (
    Counterparty, Contract, ContractType, ContractStatus,
    PaymentCondition, ContactPerson, ContractStage

)
from keyboards.contract import (
    get_contract_main_menu,
    get_counterparty_for_contract_keyboard,
    get_contract_types_keyboard,
    get_contract_statuses_keyboard,
    get_validity_type_keyboard,
    get_confirm_keyboard,
    get_contract_list_keyboard,
    get_contract_detail_menu
)
from keyboards.contract_stage import (
    get_payment_conditions_keyboard,
    get_stage_confirm_keyboard,
    get_stage_list_keyboard
)

router = Router()
logger = logging.getLogger(__name__)

# ========== Вход в раздел договоров ==========
@router.callback_query(F.data == "menu:contracts")
async def enter_contracts(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📄 Раздел «Договоры». Выберите действие:",
        reply_markup=get_contract_main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "contract:main")
async def back_to_contracts_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📄 Раздел «Договоры». Выберите действие:",
        reply_markup=get_contract_main_menu()
    )
    await callback.answer()

# ========== Создание договора ==========
@router.callback_query(F.data == "contract:create")
async def start_contract_creation(callback: types.CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Counterparty).order_by(Counterparty.full_name))
        counterparts = result.scalars().all()
    if not counterparts:
        await callback.message.edit_text(
            "❌ Нет контрагентов. Сначала создайте хотя бы одного.",
            reply_markup=get_contract_main_menu()
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "Выберите контрагента для договора:",
        reply_markup=get_counterparty_for_contract_keyboard(counterparts, page=0)
    )
    await state.set_state(ContractCreation.select_counterparty)
    await callback.answer()

@router.callback_query(F.data.startswith("contract:choose_page:"))
async def choose_counterparty_page(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Counterparty).order_by(Counterparty.full_name))
        counterparts = result.scalars().all()
    await callback.message.edit_text(
        "Выберите контрагента для договора:",
        reply_markup=get_counterparty_for_contract_keyboard(counterparts, page)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contract:choose_counterparty:"), StateFilter(ContractCreation.select_counterparty))
async def process_counterparty_choice(callback: types.CallbackQuery, state: FSMContext):
    counterparty_id = callback.data.split(":")[2]
    await state.update_data(counterparty_id=counterparty_id)
    # Загрузка типов договоров
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ContractType).order_by(ContractType.sort_order))
        types_list = result.scalars().all()
    await callback.message.edit_text(
        "Выберите тип договора:",
        reply_markup=get_contract_types_keyboard(types_list)
    )
    await state.set_state(ContractCreation.select_type)
    await callback.answer()

@router.callback_query(F.data.startswith("contract:type:"), StateFilter(ContractCreation.select_type))
async def process_type_choice(callback: types.CallbackQuery, state: FSMContext):
    type_id = int(callback.data.split(":")[2])
    await state.update_data(contract_type_id=type_id)
    await callback.message.edit_text("Введите номер поста (например, 7/19):")
    await state.set_state(ContractCreation.input_post_number)
    await callback.answer()

@router.message(StateFilter(ContractCreation.input_post_number))
async def process_post_number(message: types.Message, state: FSMContext):
    post_number = message.text.strip()
    if not post_number:
        await message.reply("Номер поста не может быть пустым. Введите снова:")
        return
    await state.update_data(post_number=post_number)
    await message.answer("Введите номер договора (или отправьте 'авто' для автоматической генерации):")
    await state.set_state(ContractCreation.input_contract_number)

@router.message(StateFilter(ContractCreation.input_contract_number))
async def process_contract_number(message: types.Message, state: FSMContext):
    number = message.text.strip()
    
    if not number:
        await message.reply("Номер договора не может быть пустым. Введите снова:")
        return
    await state.update_data(contract_number=number)
    # Загрузка статуса
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ContractStatus))
        statuses = result.scalars().all()
    await message.answer(
        "Выберите статус договора:",
        reply_markup=get_contract_statuses_keyboard(statuses)
    )
    await state.set_state(ContractCreation.select_status)

@router.callback_query(F.data.startswith("contract:status:"), StateFilter(ContractCreation.select_status))
async def process_status_choice(callback: types.CallbackQuery, state: FSMContext):
    status_id = int(callback.data.split(":")[2])
    await state.update_data(status_id=status_id)
    await callback.message.edit_text("Введите дату заключения договора (в формате ДД.ММ.ГГГГ) или отправьте 'пропустить':")
    await state.set_state(ContractCreation.input_conclusion_date)
    await callback.answer()

@router.message(StateFilter(ContractCreation.input_conclusion_date))
async def process_conclusion_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() == 'пропустить':
        date_val = None
    else:
        # Простейшая валидация формата
        parts = text.split('.')
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            await message.reply("Неверный формат. Используйте ДД.ММ.ГГГГ или отправьте 'пропустить':")
            return
        date_val = text
    await state.update_data(conclusion_date=date_val)
    await message.answer("Введите место заключения договора (или отправьте 'пропустить'):")
    await state.set_state(ContractCreation.input_place)

@router.message(StateFilter(ContractCreation.input_place))
async def process_place(message: types.Message, state: FSMContext):
    text = message.text.strip()
    place = text if text.lower() != 'пропустить' else None
    await state.update_data(place=place)
    await message.answer(
        "Выберите тип срока действия договора:",
        reply_markup=get_validity_type_keyboard()
    )
    await state.set_state(ContractCreation.select_validity_type)

@router.callback_query(F.data.startswith("validity:"), StateFilter(ContractCreation.select_validity_type))
async def process_validity_type(callback: types.CallbackQuery, state: FSMContext):
    v_type = callback.data.split(":")[1]  # 'date' or 'condition'
    await state.update_data(validity_period_type=v_type)
    if v_type == 'date':
        await callback.message.edit_text("Введите дату окончания договора (ДД.ММ.ГГГГ):")
        await state.set_state(ContractCreation.input_expiry_date)
    else:
        await callback.message.edit_text("Введите ориентировочную дату завершения (ДД.ММ.ГГГГ):")
        await state.set_state(ContractCreation.input_estimated_date)
    await callback.answer()

@router.message(StateFilter(ContractCreation.input_expiry_date))
async def process_expiry_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    parts = text.split('.')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        await message.reply("Неверный формат. Используйте ДД.ММ.ГГГГ:")
        return
    await state.update_data(expiry_date=text)
    await message.answer("Введите итоговую сумму договора (число, например 1500.50):")
    await state.set_state(ContractCreation.input_total_amount)

@router.message(StateFilter(ContractCreation.input_estimated_date))
async def process_estimated_date(message: types.Message, state: FSMContext):
    text = message.text.strip()
    parts = text.split('.')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        await message.reply("Неверный формат. Используйте ДД.ММ.ГГГГ:")
        return
    await state.update_data(estimated_date=text)
    await message.answer("Введите итоговую сумму договора (число, например 1500.50):")
    await state.set_state(ContractCreation.input_total_amount)

@router.message(StateFilter(ContractCreation.input_total_amount))
async def process_total_amount(message: types.Message, state: FSMContext):
    text = message.text.strip().replace(',', '.')
    try:
        amount = float(text)
    except ValueError:
        await message.reply("Введите число (например, 1500.50):")
        return
    await state.update_data(total_amount=amount)

    # Сводку
    data = await state.get_data()
    # Получение имен по id
    async with AsyncSessionLocal() as session:
        counterparty = await session.get(Counterparty, data['counterparty_id'])
        contract_type = await session.get(ContractType, data['contract_type_id'])
        status = await session.get(ContractStatus, data['status_id'])
    summary = (
        f"📋 **Проверьте данные договора:**\n"
        f"Контрагент: {counterparty.full_name}\n"
        f"Тип: {contract_type.name}\n"
        f"Номер поста: {data['post_number']}\n"
        f"Номер договора: {data['contract_number']}\n"
        f"Статус: {status.name}\n"
        f"Дата заключения: {data.get('conclusion_date', 'не указана')}\n"
        f"Место: {data.get('place', 'не указано')}\n"
        f"Тип срока: {'дата' if data['validity_period_type']=='date' else 'условие'}\n"
    )
    if data['validity_period_type'] == 'date':
        summary += f"Дата окончания: {data.get('expiry_date', 'не указана')}\n"
    else:
        summary += f"Ориентировочная дата: {data.get('estimated_date', 'не указана')}\n"
    summary += f"Сумма: {data['total_amount']}\n\n"
    summary += "Сохранить?"

    await message.answer(summary, reply_markup=get_confirm_keyboard(), parse_mode="Markdown")
    await state.set_state(ContractCreation.confirm)


@router.callback_query(StateFilter(ContractCreation.confirm), F.data == "contract:save")
async def confirm_save(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Даты из строк в объекты date
    conclusion_date = None
    if data.get('conclusion_date'):
        conclusion_date = datetime.strptime(data['conclusion_date'], '%d.%m.%Y').date()
    
    expiry_date = None
    if data.get('expiry_date') and data['validity_period_type'] == 'date':
        expiry_date = datetime.strptime(data['expiry_date'], '%d.%m.%Y').date()
    
    estimated_date = None
    if data.get('estimated_date') and data['validity_period_type'] == 'condition':
        estimated_date = datetime.strptime(data['estimated_date'], '%d.%m.%Y').date()
    
    async with AsyncSessionLocal() as session:
        new_contract = Contract(
            contract_number=data['contract_number'],
            post_number=data['post_number'],
            contract_type_id=data['contract_type_id'],
            counterparty_id=data['counterparty_id'],
            status_id=data['status_id'],
            conclusion_date=conclusion_date,  # теперь это date, а не строка
            place_of_conclusion=data.get('place'),
            validity_period_type=data['validity_period_type'],
            expiry_date=expiry_date,
            estimated_completion_date=estimated_date,
            total_amount=data['total_amount']
        )
        session.add(new_contract)
        await session.commit()
        await session.refresh(new_contract)
    await callback.message.edit_text(f"✅ Договор успешно создан с ID: {new_contract.id}")
    await state.clear()
    await callback.message.answer(
        "Выберите следующее действие:",
        reply_markup=get_contract_main_menu()
    )
    await callback.answer()

@router.callback_query(StateFilter(ContractCreation.confirm), F.data == "contract:cancel")
async def confirm_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Создание договора отменено.")
    await state.clear()
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_contract_main_menu()
    )
    await callback.answer()

# ========== Список договоров ==========
@router.callback_query(F.data == "contract:list")
async def show_contract_list(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Contract).options(selectinload(Contract.counterparty)).order_by(Contract.created_at.desc())
        )
        contracts = result.scalars().all()
    if not contracts:
        await callback.message.edit_text(
            "📭 Список договоров пуст.",
            reply_markup=get_contract_main_menu()
        )
        await callback.answer()
        return
    await callback.message.edit_text(
        "Список договоров:",
        reply_markup=get_contract_list_keyboard(contracts, page=0)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("contract:list_page:"))
async def paginate_contract_list(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[2])
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Contract).options(selectinload(Contract.counterparty)).order_by(Contract.created_at.desc())
        )
        contracts = result.scalars().all()
    await callback.message.edit_text(
        "Список договоров:",
        reply_markup=get_contract_list_keyboard(contracts, page)
    )
    await callback.answer()

# ========== Детальная карточка договора ==========
@router.callback_query(F.data.startswith("contract:detail:"))
async def show_contract_detail(callback: types.CallbackQuery):
    contract_id = callback.data.split(":")[2]
    async with AsyncSessionLocal() as session:
        contract = await session.get(
            Contract, contract_id,
            options=[
                selectinload(Contract.counterparty),
                selectinload(Contract.contract_type),
                selectinload(Contract.status),
                selectinload(Contract.signed_by)
            ]
        )
        if not contract:
            await callback.answer("Договор не найден", show_alert=True)
            return
    text = f"**Договор {contract.contract_number}**\n"
    text += f"Контрагент: {contract.counterparty.full_name}\n"
    text += f"Тип: {contract.contract_type.name}\n"
    text += f"Статус: {contract.status.name}\n"
    text += f"Пост: {contract.post_number}\n"
    text += f"Дата заключения: {contract.conclusion_date or 'не указана'}\n"
    text += f"Место: {contract.place_of_conclusion or 'не указано'}\n"
    if contract.validity_period_type == 'date':
        text += f"Действует до: {contract.expiry_date or 'не указано'}\n"
    else:
        text += f"Ориентировочная дата завершения: {contract.estimated_completion_date or 'не указана'}\n"
    text += f"Сумма: {contract.total_amount}\n"
    await callback.message.edit_text(
        text,
        reply_markup=get_contract_detail_menu(str(contract.id)),
        parse_mode="Markdown"
    )
    await callback.answer()

# ========== Управление этапами договора ==========
@router.callback_query(F.data.startswith("contract:stages:"))
async def show_contract_stages(callback: types.CallbackQuery):
    contract_id = callback.data.split(":")[2]
    async with AsyncSessionLocal() as session:
        # Проверка существование договора
        contract = await session.get(Contract, contract_id)
        if not contract:
            await callback.answer("Договор не найден", show_alert=True)
            return
        # Получаем этапы
        result = await session.execute(
            select(ContractStage).where(ContractStage.contract_id == contract_id).order_by(ContractStage.stage_number)
        )
        stages = result.scalars().all()
    
    if not stages:
        text = "📭 У этого договора пока нет этапов."
    else:
        text = "📑 **Этапы договора:**\n\n"
        for s in stages:
            text += f"**{s.stage_number}. {s.name}**\n"
            if s.expected_result:
                text += f"   Ожидаемый результат: {s.expected_result}\n"
            if s.amount:
                text += f"   Сумма: {s.amount}\n"
            text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_stage_list_keyboard(stages, contract_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("stage:add:"))
async def add_stage_start(callback: types.CallbackQuery, state: FSMContext):
    contract_id = callback.data.split(":")[2]
    await state.update_data(contract_id=contract_id)
    # Cледующий номер этапа
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ContractStage).where(ContractStage.contract_id == contract_id).order_by(ContractStage.stage_number.desc())
        )
        last_stage = result.scalars().first()
        next_number = (last_stage.stage_number + 1) if last_stage else 1
    await state.update_data(stage_number=next_number)
    await callback.message.edit_text("Введите наименование этапа:")
    await state.set_state(ContractStageCreation.name)
    await callback.answer()

@router.message(StateFilter(ContractStageCreation.name))
async def process_stage_name(message: types.Message, state: FSMContext):
    if len(message.text) < 3:
        await message.reply("Слишком короткое название. Введите минимум 3 символа:")
        return
    await state.update_data(name=message.text)
    await message.answer("Введите ожидаемый результат этапа:")
    await state.set_state(ContractStageCreation.expected_result)

@router.message(StateFilter(ContractStageCreation.expected_result))
async def process_stage_expected_result(message: types.Message, state: FSMContext):
    if len(message.text) < 3:
        await message.reply("Слишком короткое описание. Введите минимум 3 символа:")
        return
    await state.update_data(expected_result=message.text)
    await message.answer("Введите наименование документа, подтверждающего результат (или отправьте 'пропустить'):")
    await state.set_state(ContractStageCreation.confirmation_document)

@router.message(StateFilter(ContractStageCreation.confirmation_document))
async def process_stage_confirmation_doc(message: types.Message, state: FSMContext):
    text = message.text.strip()
    doc = text if text.lower() != 'пропустить' else None
    await state.update_data(confirmation_document=doc)
    # Загрузка условия оплаты
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PaymentCondition))
        conditions = result.scalars().all()
    await message.answer(
        "Выберите условия оплаты:",
        reply_markup=get_payment_conditions_keyboard(conditions)
    )
    await state.set_state(ContractStageCreation.payment_condition)

@router.callback_query(F.data.startswith("stage_pay_cond:"), StateFilter(ContractStageCreation.payment_condition))
async def process_payment_condition(callback: types.CallbackQuery, state: FSMContext):
    cond_id = int(callback.data.split(":")[1])
    await state.update_data(payment_condition_id=cond_id)
    async with AsyncSessionLocal() as session:
        cond = await session.get(PaymentCondition, cond_id)
    if cond.name == "100% Предоплата":
        await callback.message.edit_text("Введите количество дней на предоплату (от даты подписания):")
        await state.set_state(ContractStageCreation.prepayment_days)
    elif cond.name == "100% по факту":
        await callback.message.edit_text("Введите количество дней на оплату после подписания акта:")
        await state.set_state(ContractStageCreation.final_payment_days)
    elif cond.name == "Комбинированная":
        await callback.message.edit_text("Введите процент предоплаты (число от 0 до 100):")
        await state.set_state(ContractStageCreation.prepayment_percent)
    else:
        await callback.message.edit_text("Условие не поддерживается. Отмена.")
        await state.clear()
    await callback.answer()

@router.message(StateFilter(ContractStageCreation.prepayment_percent))
async def process_prepayment_percent(message: types.Message, state: FSMContext):
    try:
        percent = float(message.text.strip().replace(',', '.'))
        if percent < 0 or percent > 100:
            raise ValueError
    except ValueError:
        await message.reply("Введите число от 0 до 100:")
        return
    await state.update_data(prepayment_percent=percent)
    await message.answer("Введите количество дней на предоплату (от даты подписания):")
    await state.set_state(ContractStageCreation.prepayment_days)

@router.message(StateFilter(ContractStageCreation.prepayment_days))
async def process_prepayment_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError
    except ValueError:
        await message.reply("Введите целое неотрицательное число:")
        return
    await state.update_data(prepayment_days=days)
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        cond = await session.get(PaymentCondition, data['payment_condition_id'])
    if cond.name == "100% Предоплата":
        await message.answer("Введите сумму этапа (число, например 1500.00):")
        await state.set_state(ContractStageCreation.amount)
    elif cond.name == "Комбинированная":
        await message.answer("Введите количество дней на окончательный расчёт:")
        await state.set_state(ContractStageCreation.final_payment_days)
    else:
        await state.clear()

@router.message(StateFilter(ContractStageCreation.final_payment_days))
async def process_final_payment_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError
    except ValueError:
        await message.reply("Введите целое неотрицательное число:")
        return
    await state.update_data(final_payment_days=days)
    await message.answer("Введите сумму этапа (число, например 1500.00):")
    await state.set_state(ContractStageCreation.amount)

@router.message(StateFilter(ContractStageCreation.amount))
async def process_stage_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(',', '.'))
        if amount < 0:
            raise ValueError
    except ValueError:
        await message.reply("Введите положительное число:")
        return
    await state.update_data(amount=amount)

    # сводка
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        cond = await session.get(PaymentCondition, data['payment_condition_id'])
    summary = f"**Проверьте данные этапа:**\n"
    summary += f"Наименование: {data['name']}\n"
    summary += f"Ожидаемый результат: {data['expected_result']}\n"
    summary += f"Подтверждающий документ: {data.get('confirmation_document', 'не указан')}\n"
    summary += f"Условия оплаты: {cond.name}\n"
    if cond.name == "100% Предоплата":
        summary += f"Дней на предоплату: {data['prepayment_days']}\n"
    elif cond.name == "100% по факту":
        summary += f"Дней на оплату: {data['final_payment_days']}\n"
    elif cond.name == "Комбинированная":
        summary += f"Процент предоплаты: {data['prepayment_percent']}%\n"
        summary += f"Дней на предоплату: {data['prepayment_days']}\n"
        summary += f"Дней на окончательный расчёт: {data['final_payment_days']}\n"
    summary += f"Сумма этапа: {data['amount']}\n\n"
    summary += "Сохранить?"

    await message.answer(summary, reply_markup=get_stage_confirm_keyboard(), parse_mode="Markdown")
    await state.set_state(ContractStageCreation.confirm)

@router.callback_query(StateFilter(ContractStageCreation.confirm), F.data == "stage:save")
async def save_stage(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        stage = ContractStage(
            contract_id=data['contract_id'],
            stage_number=data['stage_number'],
            name=data['name'],
            expected_result=data['expected_result'],
            confirmation_document=data.get('confirmation_document'),
            payment_condition_id=data['payment_condition_id'],
            prepayment_percent=data.get('prepayment_percent'),
            prepayment_days=data.get('prepayment_days'),
            final_payment_days=data.get('final_payment_days'),
            amount=data['amount']
        )
        session.add(stage)
        await session.commit()
        await session.refresh(stage)
    await callback.message.edit_text("✅ Этап успешно добавлен!")
    await state.clear()
    await callback.message.answer(
        "Вернуться к этапам?",
        reply_markup=get_stage_list_keyboard([], data['contract_id'])  # передаём пустой список, но клавиатура всё равно покажет кнопки
    )
    await callback.answer()

@router.callback_query(StateFilter(ContractStageCreation.confirm), F.data == "stage:cancel")
async def cancel_stage_creation(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("❌ Добавление этапа отменено.")
    await state.clear()
    await callback.message.answer(
        "Вернуться к этапам?",
        reply_markup=get_stage_list_keyboard([], data['contract_id'])
    )
    await callback.answer()

# ========== Заглушки для будущих функций ==========
@router.callback_query(F.data.startswith("contract:edit:"))
async def contract_edit(callback: types.CallbackQuery):
    await callback.answer("Редактирование пока не реализовано", show_alert=True)

@router.callback_query(F.data.startswith("contract:delete:"))
async def contract_delete(callback: types.CallbackQuery):
    contract_id = callback.data.split(":")[2]
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Contract).where(Contract.id == contract_id))
        await session.commit()
    await callback.answer("Договор удалён", show_alert=True)
    await show_contract_list(callback)