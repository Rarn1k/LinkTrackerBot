from typing import Any, ClassVar, Dict, Tuple, Type, TypeVar

T = TypeVar("T")


class SingletonMeta(type):
    """Метакласс, реализующий шаблон Singleton.

    Гарантирует, что для каждого класса, использующего этот метакласс,
    будет создан только один экземпляр. Экземпляры хранятся в словаре `_instances`,
    где ключом является сам класс, a значением — экземпляр этого класса.
    """

    _instances: ClassVar[dict[Type[Any], Any]] = {}

    def __call__(cls: Type[T], *args: Tuple[Any, ...], **kwargs: Dict[str, Any]) -> T:
        """Переопределяет создание экземпляра класса.

        Проверяет, существует ли уже экземпляр класса в `_instances`. Если нет,
        создаёт новый экземпляр c помощью метода `__call__` родительского
        метакласса (`type`) и сохраняет этот экземпляр. Если экземпляр уже существует,
        возвращает этот экземпляр.

        :param cls: Класс, для которого создаётся экземпляр.
        :param args: Позиционные аргументы для инициализации экземпляра.
        :param kwargs: Именованные аргументы для инициализации экземпляра.
        :return: Единственный экземпляр класса.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
