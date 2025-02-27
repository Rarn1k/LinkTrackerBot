from telethon.events import NewMessage

from src.bd.memory_storage.enum_states import State
from src.bd.memory_storage.key_builder import build_storage_key
from src.bd.memory_storage.memory import MemoryStorage
from src.bd.repository import Repository, Subscription
from src.handlers.utils.registration_required import require_registration

__all__ = ("msg_handler",)

EXPECTED_TRACK_PARTS: int = 2


@require_registration
async def msg_handler(
    event: NewMessage.Event,
) -> None:
    """Обрабатывает входящие сообщения, связанные c машиной состояний (FSM) для команды /track.
    Декоратор @require_registration обеспечивает выполнение только для зарегистрированных
    пользователей.

    B зависимости от текущего состояния (FSM), функция:
      - Если состояние равно State.WAITING_FOR_TAGS, интерпретирует сообщение как список тегов,
        сохраняет их в хранилище, переводит FSM в состояние State.WAITING_FOR_FILTERS и
        запрашивает фильтры.
      - Если состояние равно State.WAITING_FOR_FILTERS, интерпретирует сообщение как фильтры,
        сохраняет их в хранилище, создаёт подписку и добавляет её в репозиторий.
      - Если состояние равно None, игнорирует сообщение.

    Если сообщение начинается c символа '/', обработчик игнорирует это сообщение, так как
    такие команды обрабатываются другими обработчиками.

    :param event: Событие Telethon c типом NewMessage.Event, содержащее входящее сообщение.
    :return: None
    """
    if event.raw_text.startswith("/"):
        return

    key = await build_storage_key(event)
    memory_storage = MemoryStorage()
    current_state = await memory_storage.get_state(key)

    if current_state == State.WAITING_FOR_TAGS:
        tags = event.raw_text.split()
        data = await memory_storage.get_data(key)
        data["tags"] = tags
        await memory_storage.set_data(key, data)
        await memory_storage.set_state(key, State.WAITING_FOR_FILTERS)
        await event.respond(
            "Введите фильтры (опционально, формат key:value, разделённые пробелами):",
        )

    elif current_state == State.WAITING_FOR_FILTERS:
        filters_input = event.raw_text.split()
        filters = {}
        for f in filters_input:
            if ":" in f:
                key_val = f.split(":", 1)
                if len(key_val) == EXPECTED_TRACK_PARTS:
                    filters[key_val[0]] = key_val[1]
        data = await memory_storage.get_data(key)
        data["filters"] = filters
        await memory_storage.set_data(key, data)

        url = data.get("url")
        tags = data.get("tags", [])
        subscription = Subscription(url=url, tags=tags, filters=filters)
        repository = Repository()
        if await repository.add_subscription(event.sender_id, subscription):
            await event.respond(f"Ссылка {url} добавлена для отслеживания.")
        else:
            await event.respond(f"Ссылка {url} уже отслеживается.")
        await memory_storage.clear(key)
