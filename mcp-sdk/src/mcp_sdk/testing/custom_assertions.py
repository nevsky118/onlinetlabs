def assert_equal(actual, expected, message=None):
    """
    Проверяет, что фактическое значение равно ожидаемому

    Args:
        actual: Фактическое значение
        expected: Ожидаемое значение
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если значения не равны
    """
    if actual != expected:
        raise AssertionError(message or f"{actual} != {expected}")


def assert_not_equal(actual, expected, message=None):
    """
    Проверяет, что фактическое значение не равно ожидаемому

    Args:
        actual: Фактическое значение
        expected: Значение, которое не должно совпадать
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если значения совпадают
    """
    if actual == expected:
        raise AssertionError(message or f"{actual} == {expected}")


def assert_true(value, message=None):
    """
    Проверяет, что значение является True

    Args:
        value: Проверяемое значение
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если значение не True
    """
    if not value:
        raise AssertionError(message or f"Expected True, but got {value}")


def assert_false(value, message=None):
    """
    Проверяет, что значение является False.

    Args:
        value: Проверяемое значение
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если значение не False
    """
    if value:
        raise AssertionError(message or f"Expected False, but got {value}")


def assert_is_none(value, message=None):
    """
    Проверяет, что значение является None

    Args:
        value: Проверяемое значение
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если значение не None
    """
    if value is not None:
        raise AssertionError(message or f"Expected None, but got {value}")


def assert_is_not_none(value, message=None):
    """
    Проверяет, что значение не является None

    Args:
        value: Проверяемое значение
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если значение является None
    """
    if value is None:
        raise AssertionError(message or "Expected value to be not None")


def assert_is_instance(obj, cls, message=None):
    """
    Проверяет, что объект является экземпляром класса.

    Args:
        obj: Проверяемый объект
        cls: Ожидаемый класс
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если объект не является экземпляром класса
    """
    if not isinstance(obj, cls):
        raise AssertionError(message or f"Expected {cls.__name__}, got {type(obj).__name__}")


def assert_greater(actual, expected, message=None):
    """
    Проверяет, что фактическое значение больше ожидаемого

    Args:
        actual: Фактическое значение
        expected: Ожидаемое значение для сравнения
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если фактическое значение не больше ожидаемого
    """
    if not actual > expected:
        raise AssertionError(message or f"{actual} > {expected} is not True")


def assert_greater_equal(actual, expected, message=None):
    """
    Проверяет, что фактическое значение больше или равно ожидаемому

    Args:
        actual: Фактическое значение
        expected: Ожидаемое значение для сравнения
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если фактическое значение меньше ожидаемого
    """
    if not actual >= expected:
        raise AssertionError(message or f"{actual} >= {expected} is not True")


def assert_less(actual, expected, message=None):
    """
    Проверяет, что фактическое значение меньше ожидаемого

    Args:
        actual: Фактическое значение
        expected: Ожидаемое значение для сравнения
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если фактическое значение не меньше ожидаемого
    """
    if not actual < expected:
        raise AssertionError(message or f"{actual} < {expected} is not True")


def assert_less_equal(actual, expected, message=None):
    """
    Проверяет, что фактическое значение меньше или равно ожидаемому

    Args:
        actual: Фактическое значение
        expected: Ожидаемое значение для сравнения
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если фактическое значение больше ожидаемого
    """
    if not actual <= expected:
        raise AssertionError(message or f"{actual} <= {expected} is not True")


def assert_in(item, container, message=None):
    """
    Проверяет, что элемент содержится в коллекции.

    Args:
        item: Проверяемый элемент
        container: Коллекция для поиска
        message: Необязательное пользовательское сообщение об ошибке
    Raises:
        AssertionError: Если элемент не найден в коллекции.
    """
    if item not in container:
        raise AssertionError(message or f"{item} not found in {container}")
