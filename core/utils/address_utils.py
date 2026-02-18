import asyncio
from pathlib import Path
from typing import List, Optional

from config import logger


async def read_addresses_async(file_path: Optional[str] = None) -> List[str]:
    """
    Асинхронно читает файл с адресами и возвращает список адресов.

    Args:
        file_path: Путь к файлу с адресами. Если None, используется путь по умолчанию.

    Returns:
        List[str]: Список адресов из файла.
    """
    if file_path is None:
        # Используем относительный путь от текущего файла
        current_dir = Path(__file__).parent.parent
        file_path = current_dir / "statics" / "addresses.txt"

    addresses = []

    try:
        # Используем asyncio.to_thread для выполнения файловой операции в отдельном потоке
        content = await asyncio.to_thread(_read_file_content, str(file_path))
        addresses = [line.strip() for line in content.split("\n") if line.strip()]
    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")

    return addresses


def _read_file_content(file_path: str) -> str:
    """Вспомогательная функция для чтения содержимого файла."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


async def get_all_addresses(file_path: Optional[str] = None) -> List[str]:
    """
    Получает все адресы из файла.

    Args:
        file_path: Путь к файлу с адресами.

    Returns:
        List[str]: Список всех адресов.
    """
    return await read_addresses_async(file_path)
