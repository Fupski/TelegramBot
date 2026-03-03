import os
import csv
import asyncio
from sqlalchemy import text
from db.database import engine, AsyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def export_table_to_csv(table_name, output_dir="exports"):
    """Экспортирует одну таблицу в CSV с кодировкой utf-8-sig (с BOM)."""
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{table_name}.csv")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(f"SELECT * FROM {table_name}"))
        rows = result.fetchall()
        if not rows:
            logger.info(f"Таблица {table_name} пуста, файл не создан.")
            return
        
        columns = result.keys()
        
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(columns)  # заголовок
            for row in rows:
                processed_row = [str(val) if val is not None else '' for val in row]
                writer.writerow(processed_row)
        
        logger.info(f"Таблица {table_name} экспортирована в {output_file}")

async def export_all_tables():
    """Экспортирует все таблицы из базы данных."""
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        )
        tables = [row[0] for row in result]
    
    logger.info(f"Найдено таблиц: {tables}")
    
    for table in tables:
        try:
            await export_table_to_csv(table)
        except Exception as e:
            logger.error(f"Ошибка при экспорте таблицы {table}: {e}")

if __name__ == "__main__":
    asyncio.run(export_all_tables())