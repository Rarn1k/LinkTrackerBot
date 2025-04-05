from src.db.db_manager.base import DBManager
from src.db.db_manager.orm_manager import ORMDBManager
from src.db.db_manager.sql_manager import SQLDBManager
from src.settings import settings

DB_MANAGER_MAP = {
    "ORM": ORMDBManager,
    "SQL": SQLDBManager,
}


def get_db_manager(access_type: str) -> DBManager:
    """Фабричная функция для создания менеджера базы данных на основе типа доступа.

    :param access_type: Тип доступа к базе данных ("ORM" или "SQL").
    :return: Экземпляр менеджера базы данных (DBManager).
    :raises ValueError: Если тип доступа неизвестен.
    """
    access_type = access_type.upper()
    manager_cls = DB_MANAGER_MAP.get(access_type)
    if manager_cls is None:
        raise ValueError(f"Неизвестный тип доступа: {access_type}")
    return manager_cls()


db_manager = get_db_manager(settings.db.access_type)
