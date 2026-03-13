import logging
import os
import pathlib
import random
import string
import uuid

from autotests.settings.utils.custom_assertions import assert_equal

system_logger = logging.getLogger(__name__)


class Randomizer:
    """
    Утилитный класс для генерации случайных чисел, строк и UUID.
    """

    @staticmethod
    def int_between(low: int, high: int) -> int:
        """
        Генерирует случайное целое число в заданном диапазоне.

        :param low: Минимальное возможное значение (включительно).
        :param high: Максимальное возможное значение (включительно).
        :return: Случайное целое число.
        """
        return random.randint(low, high)

    @staticmethod
    def random_string(length: int) -> str:
        """
        Формирует случайную строку из букв латиницы и цифр.

        :param length: Длина результирующей строки.
        :return: Случайная строка.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(random.choices(alphabet, k=length))

    @staticmethod
    def random_email() -> str:
        """
        Генерирует случайный тестовый email.

        :return: Email в формате 'test_XXXXXXXX@autotest.local'.
        """
        return f"test_{Randomizer.random_string(8)}@autotest.local"

    @staticmethod
    def uuid() -> str:
        """
        Возвращает новый уникальный идентификатор в формате UUID4.

        :return: Строка с UUID.
        """
        return str(uuid.uuid4())


def get_path_file(path, name: str = "", ext: str = "") -> str:
    """
    Получает путь до файла.

    :param path: Путь до папки в которой запущен тест.
    :param name: Имя файла, ищется перебором рекурсивно, относительно path.
    :param ext: Расширение файла или правило на расширение, например: json или [jJ][sS][oO][nN].
    :return: Путь до файла.
    """
    if isinstance(path, str):
        return os.path.abspath(os.path.join(path, name, ext))

    if isinstance(path, (pathlib.Path, pathlib.WindowsPath, pathlib.PosixPath)):
        if ext:
            return str(list(path.rglob(f"{name}.{ext}"))[0])

        return str(list(path.rglob(f"{name}"))[0])

    system_logger.error("Value is not of the correct type, current type: %s", type(path).__name__)

    raise TypeError(f"Value is not of the correct type, current type: {type(path)}")


def get_path_folder(path, name: str = "") -> str:
    """
    Получает путь до папки.

    :param path: Путь до папки в которой запущен тест.
    :param name: Имя папки, ищется перебором рекурсивно, относительно path.
    :return: Путь до папки.
    """
    if isinstance(path, str):
        return os.path.abspath(path)

    if isinstance(path, (pathlib.Path, pathlib.WindowsPath, pathlib.PosixPath)):
        return str(list(path.rglob(f"{name}"))[0])

    system_logger.error("Value is not of the correct type, current type: %s", type(path).__name__)

    raise TypeError(f"Value is not of the correct type, current type: {type(path)}")


def get_current_test_name() -> str | None:
    """
    Получает имя текущего выполняемого теста (если тест уже запущен).

    :return: Имя теста в виде строки или None, если тест ещё не запущен.
    """
    if os.environ.get('PYTEST_CURRENT_TEST') is not None:
        return os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]
    return None


def check_response_status(response, expected_status: int) -> None:
    """
    Проверяет, что статус-код HTTP-ответа соответствует ожидаемому.

    :param response: Объект HTTP-ответа (httpx.Response).
    :param expected_status: Ожидаемый HTTP статус-код.
    :raises AssertionError: Если фактический статус не совпадает с ожидаемым.
    """
    actual_status = response.status_code
    request_url = getattr(response.request, 'url', 'unknown') if response.request else 'unknown'
    response_text = response.text

    error_message = (
        f"Ошибка статуса ответа:\n"
        f"Ожидался статус: {expected_status}, фактически получен: {actual_status}\n"
        f"URL запроса: {request_url}\n"
        f"Тело ответа: {response_text}"
    )

    assert_equal(actual_status, expected_status, error_message)


def verify_data(
    actual_data,
    expected_data,
    verified_fields: list = None,
    unverified_fields: list = None,
    msg_option: str = "",
) -> None:
    """
    Проверяет, что фактические данные соответствуют ожидаемым. Поддерживаются словари и списки.

    :param actual_data: Фактические данные (dict или list).
    :param expected_data: Ожидаемые данные (dict или list).
    :param verified_fields: Список ключей, которые необходимо проверить в словаре (по умолчанию None).
    :param unverified_fields: Список ключей, которые нужно исключить из проверки в словаре (по умолчанию None).
    :param msg_option: Дополнительное сообщение для контекста ошибки (по умолчанию пустая строка).
    :raises AssertionError: Если данные не совпадают.
    :raises TypeError: Если типы данных не поддерживаются или не совпадают.
    """
    if isinstance(expected_data, dict) and isinstance(actual_data, dict):
        verified_keys = expected_data.keys()
        if verified_fields is not None:
            verified_keys = verified_fields
        elif unverified_fields is not None:
            verified_keys = set(expected_data.keys()) - set(unverified_fields)

        for key in verified_keys:
            actual_value = actual_data.get(key)
            expected_value = expected_data.get(key)
            assert_equal(
                actual_value,
                expected_value,
                f"Ошибка! Несовпадение в поле '{key}' {msg_option}.\n"
                f"Фактическое значение = '{actual_value}', Ожидаемое значение = '{expected_value}'.",
            )

    elif isinstance(expected_data, list) and isinstance(actual_data, list):
        assert_equal(
            len(actual_data),
            len(expected_data),
            f"Ошибка! Несовпадение длины списка {msg_option}.\n"
            f"Фактическая длина = {len(actual_data)}, Ожидаемая длина = {len(expected_data)}.",
        )

        for index, (actual_item, expected_item) in enumerate(zip(actual_data, expected_data)):
            assert_equal(
                actual_item,
                expected_item,
                f"Ошибка! Несовпадение элемента списка по индексу {index} {msg_option}.\n"
                f"Фактический элемент = {actual_item}, Ожидаемый элемент = {expected_item}.",
            )

    else:
        raise TypeError(
            f"Неподдерживаемые типы данных для проверки {msg_option}.\n"
            f"Фактический тип = {type(actual_data)}, Ожидаемый тип = {type(expected_data)}.",
        )


def verify_entity_count(
    actual_data,
    expected_count: int,
    msg_option: str = "",
) -> None:
    """
    Проверяет, что количество сущностей в списке соответствует ожидаемому.

    :param actual_data: Список сущностей.
    :param expected_count: Ожидаемое количество сущностей.
    :param msg_option: Дополнительное сообщение для контекста ошибки (по умолчанию пустая строка).
    :raises AssertionError: Если количество не совпадает.
    :raises TypeError: Если передан не список.
    """
    if not isinstance(actual_data, list):
        raise TypeError(
            f"Ошибка! Для проверки количества сущностей ожидался список {msg_option}.\n"
            f"Фактический тип = {type(actual_data)}.",
        )

    actual_count = len(actual_data)
    assert_equal(
        actual_count,
        expected_count,
        f"Ошибка! Несовпадение количества сущностей {msg_option}.\n"
        f"Фактическое количество = {actual_count}, Ожидаемое количество = {expected_count}.",
    )
