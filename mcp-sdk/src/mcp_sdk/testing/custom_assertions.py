def assert_equal(actual, expected, message=None):
    """
    Checks that the actual value equals the expected value

    Args:
        actual: Actual value
        expected: Expected value
        message: Optional custom error message
    Raises:
        AssertionError: If the values are not equal
    """
    if actual != expected:
        raise AssertionError(message or f"{actual} != {expected}")


def assert_not_equal(actual, expected, message=None):
    """
    Checks that the actual value does not equal the expected value

    Args:
        actual: Actual value
        expected: Value that must not match
        message: Optional custom error message
    Raises:
        AssertionError: If the values match
    """
    if actual == expected:
        raise AssertionError(message or f"{actual} == {expected}")


def assert_true(value, message=None):
    """
    Checks that the value is True

    Args:
        value: Value being checked
        message: Optional custom error message
    Raises:
        AssertionError: If the value is not True
    """
    if not value:
        raise AssertionError(message or f"Expected True, but got {value}")


def assert_false(value, message=None):
    """
    Checks that the value is False.

    Args:
        value: Value being checked
        message: Optional custom error message
    Raises:
        AssertionError: If the value is not False
    """
    if value:
        raise AssertionError(message or f"Expected False, but got {value}")


def assert_is_none(value, message=None):
    """
    Checks that the value is None

    Args:
        value: Value being checked
        message: Optional custom error message
    Raises:
        AssertionError: If the value is not None
    """
    if value is not None:
        raise AssertionError(message or f"Expected None, but got {value}")


def assert_is_not_none(value, message=None):
    """
    Checks that the value is not None

    Args:
        value: Value being checked
        message: Optional custom error message
    Raises:
        AssertionError: If the value is None
    """
    if value is None:
        raise AssertionError(message or "Expected value to be not None")


def assert_is_instance(obj, cls, message=None):
    """
    Checks that the object is an instance of the class.

    Args:
        obj: Object being checked
        cls: Expected class
        message: Optional custom error message
    Raises:
        AssertionError: If the object is not an instance of the class
    """
    if not isinstance(obj, cls):
        raise AssertionError(message or f"Expected {cls.__name__}, got {type(obj).__name__}")


def assert_greater(actual, expected, message=None):
    """
    Checks that the actual value is greater than the expected value

    Args:
        actual: Actual value
        expected: Expected value to compare against
        message: Optional custom error message
    Raises:
        AssertionError: If the actual value is not greater than the expected value
    """
    if not actual > expected:
        raise AssertionError(message or f"{actual} > {expected} is not True")


def assert_greater_equal(actual, expected, message=None):
    """
    Checks that the actual value is greater than or equal to the expected value

    Args:
        actual: Actual value
        expected: Expected value to compare against
        message: Optional custom error message
    Raises:
        AssertionError: If the actual value is less than the expected value
    """
    if not actual >= expected:
        raise AssertionError(message or f"{actual} >= {expected} is not True")


def assert_less(actual, expected, message=None):
    """
    Checks that the actual value is less than the expected value

    Args:
        actual: Actual value
        expected: Expected value to compare against
        message: Optional custom error message
    Raises:
        AssertionError: If the actual value is not less than the expected value
    """
    if not actual < expected:
        raise AssertionError(message or f"{actual} < {expected} is not True")


def assert_less_equal(actual, expected, message=None):
    """
    Checks that the actual value is less than or equal to the expected value

    Args:
        actual: Actual value
        expected: Expected value to compare against
        message: Optional custom error message
    Raises:
        AssertionError: If the actual value is greater than the expected value
    """
    if not actual <= expected:
        raise AssertionError(message or f"{actual} <= {expected} is not True")


def assert_in(item, container, message=None):
    """
    Checks that the item is contained in the collection.

    Args:
        item: Item being checked
        container: Collection to search
        message: Optional custom error message
    Raises:
        AssertionError: If the item is not found in the collection.
    """
    if item not in container:
        raise AssertionError(message or f"{item} not found in {container}")
