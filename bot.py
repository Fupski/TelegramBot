import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from sqlalchemy import select

from config import BOT_TOKEN
from db.database import engine, AsyncSessionLocal
from db import models
from db.models import ContractType, ContractStatus, PaymentCondition
from handlers import start, counterparty, contract

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def on_startup():
    logger.info("Создание таблиц в базе данных...")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    logger.info("Таблицы созданы/проверены.")

    # Заполнение справочника, если он пустой
    async with AsyncSessionLocal() as session:
        # Contract types
        result = await session.execute(select(ContractType))
        if not result.scalars().first():
            types = [
                ContractType(name="Договор поставки товаров для нашей компании", code="postavka", sort_order=1),
                ContractType(name="Договор предоставления услуг для нашей компании", code="uslugi", sort_order=2),
                ContractType(name="Договор подряда (работы) для нашей компании", code="podryad", sort_order=3),
                ContractType(name="Договор субподряда для нашего клиента", code="subpodryad", sort_order=4),
                ContractType(name="Договор оказания услуг для нашего клиента", code="uslugi_client", sort_order=5),
                ContractType(name="Договор подряда (работ) для нашего клиента", code="podryad_client", sort_order=6),
                ContractType(name="Договор поставки ТС ППЗ нашему клиенту", code="postavka_ppz", sort_order=7),
            ]
            session.add_all(types)
            await session.commit()
            logger.info("Справочник contract_types заполнен.")

        # Contract statuses
        result = await session.execute(select(ContractStatus))
        if not result.scalars().first():
            statuses = [
                ContractStatus(name="Проект", code="project"),
                ContractStatus(name="Действующий", code="active"),
                ContractStatus(name="Проект - аннулирован", code="project_canceled"),
                ContractStatus(name="Успешно завершен", code="success"),
                ContractStatus(name="Не успешно завершен", code="failed"),
                ContractStatus(name="Временно приостановлен", code="suspended"),
                ContractStatus(name="Сорваны сроки", code="deadline_missed"),
                ContractStatus(name="Истек срок", code="expired"),
                ContractStatus(name="Бездействие", code="inactive"),
            ]
            session.add_all(statuses)
            await session.commit()
            logger.info("Справочник contract_statuses заполнен.")

        # Payment conditions
        result = await session.execute(select(PaymentCondition))
        if not result.scalars().first():
            conditions = [
                PaymentCondition(name="100% Предоплата"),
                PaymentCondition(name="100% по факту"),
                PaymentCondition(name="Комбинированная")
            ]
            session.add_all(conditions)
            await session.commit()
            logger.info("Справочник payment_conditions заполнен.")

async def on_shutdown():
    logger.info("Закрытие соединения с базой данных...")
    await engine.dispose()
    logger.info("Соединение закрыто.")

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
    ]
    await bot.set_my_commands(commands)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(counterparty.router)
    dp.include_router(contract.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await set_commands(bot)

    try:
        logger.info("Бот запущен и готов к работе.")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())