from src.db.factory.data_access_service import DataAccessService
from src.db.factory.orm_factory import OrmDataAccessFactory
from src.db.factory.sql_factory import SqlDataAccessFactory
from src.settings import settings

DB_DATA_ACCESS_MAP: dict[str, type[OrmDataAccessFactory | SqlDataAccessFactory]] = {
    "ORM": OrmDataAccessFactory,
    "SQL": SqlDataAccessFactory,
}


def get_data_access_service(access_type: str) -> DataAccessService:
    """Создает сервис доступа к данным в зависимости от типа хранилища.

    :param access_type: Тип доступа к данным (`"ORM"` или `"SQL"`).
    :return: Экземпляр `DataAccessService`.
    :raises ValueError: Если передан неизвестный тип доступа.
    """
    access_type = access_type.upper()
    factory_cls = DB_DATA_ACCESS_MAP.get(access_type)
    if factory_cls is None:
        raise ValueError(f"Неизвестный тип доступа: {access_type}")

    factory = factory_cls()

    chat_service = factory.create_chat_service()
    link_service = factory.create_link_service()

    return DataAccessService(chat_service, link_service)


db_service: DataAccessService = get_data_access_service(settings.db.access_type)
