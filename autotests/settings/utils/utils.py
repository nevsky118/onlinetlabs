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
    Utility class for generating random numbers, strings and UUIDs.
    """

    @staticmethod
    def int_between(low: int, high: int) -> int:
        """
        Generates a random integer within the given range.

        :param low: Minimum possible value (inclusive).
        :param high: Maximum possible value (inclusive).
        :return: A random integer.
        """
        return random.randint(low, high)

    @staticmethod
    def random_string(length: int) -> str:
        """
        Builds a random string made of Latin letters and digits.

        :param length: Length of the resulting string.
        :return: A random string.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(random.choices(alphabet, k=length))

    @staticmethod
    def random_email() -> str:
        """
        Generates a random test email.

        :return: An email in the 'test_XXXXXXXX@autotest.local' format.
        """
        return f"test_{Randomizer.random_string(8)}@autotest.local"

    @staticmethod
    def uuid() -> str:
        """
        Returns a new unique identifier in UUID4 format.

        :return: A string holding the UUID.
        """
        return str(uuid.uuid4())


def get_path_file(path, name: str = "", ext: str = "") -> str:
    """
    Gets the path to a file.

    :param path: Path to the folder the test is run from.
    :param name: File name, searched for recursively relative to path.
    :param ext: File extension or an extension pattern, for example json or [jJ][sS][oO][nN].
    :return: Path to the file.
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
    Gets the path to a folder.

    :param path: Path to the folder the test is run from.
    :param name: Folder name, searched for recursively relative to path.
    :return: Path to the folder.
    """
    if isinstance(path, str):
        return os.path.abspath(path)

    if isinstance(path, (pathlib.Path, pathlib.WindowsPath, pathlib.PosixPath)):
        return str(list(path.rglob(f"{name}"))[0])

    system_logger.error("Value is not of the correct type, current type: %s", type(path).__name__)

    raise TypeError(f"Value is not of the correct type, current type: {type(path)}")


def get_current_test_name() -> str | None:
    """
    Gets the name of the currently running test (if a test is already running).

    :return: The test name as a string, or None if no test has started yet.
    """
    if os.environ.get('PYTEST_CURRENT_TEST') is not None:
        return os.environ.get('PYTEST_CURRENT_TEST').split(':')[-1].split(' ')[0]
    return None


def check_response_status(response, expected_status: int) -> None:
    """
    Checks that the HTTP response status code matches the expected one.

    :param response: HTTP response object (httpx.Response).
    :param expected_status: Expected HTTP status code.
    :raises AssertionError: If the actual status does not match the expected one.
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
    Checks that the actual data matches the expected data. Dictionaries and lists are supported.

    :param actual_data: Actual data (dict or list).
    :param expected_data: Expected data (dict or list).
    :param verified_fields: List of keys that must be checked in the dictionary (None by default).
    :param unverified_fields: List of keys to exclude from the dictionary check (None by default).
    :param msg_option: Additional message giving context for the error (empty string by default).
    :raises AssertionError: If the data does not match.
    :raises TypeError: If the data types are unsupported or do not match.
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
    Checks that the number of entities in the list matches the expected one.

    :param actual_data: List of entities.
    :param expected_count: Expected number of entities.
    :param msg_option: Additional message giving context for the error (empty string by default).
    :raises AssertionError: If the count does not match.
    :raises TypeError: If the argument passed is not a list.
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
