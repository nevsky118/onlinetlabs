def assert_equal(actual, expected, message=None):
    """Raise AssertionError if actual != expected."""
    if actual != expected:
        raise AssertionError(message or f"{actual} != {expected}")


def assert_not_equal(actual, expected, message=None):
    """Raise AssertionError if actual == expected."""
    if actual == expected:
        raise AssertionError(message or f"{actual} == {expected}")


def assert_true(value, message=None):
    """Raise AssertionError if value is falsy."""
    if not value:
        raise AssertionError(message or f"Expected True, but got {value}")


def assert_false(value, message=None):
    """Raise AssertionError if value is truthy."""
    if value:
        raise AssertionError(message or f"Expected False, but got {value}")


def assert_is_none(value, message=None):
    """Raise AssertionError if value is not None."""
    if value is not None:
        raise AssertionError(message or f"Expected None, but got {value}")


def assert_is_not_none(value, message=None):
    """Raise AssertionError if value is None."""
    if value is None:
        raise AssertionError(message or "Expected value to be not None")


def assert_is_instance(obj, cls, message=None):
    """Raise AssertionError if obj is not an instance of cls."""
    if not isinstance(obj, cls):
        raise AssertionError(message or f"Expected {cls.__name__}, got {type(obj).__name__}")


def assert_greater(actual, expected, message=None):
    """Raise AssertionError if actual is not greater than expected."""
    if not actual > expected:
        raise AssertionError(message or f"{actual} > {expected} is not True")


def assert_greater_equal(actual, expected, message=None):
    """Raise AssertionError if actual is not greater than or equal to expected."""
    if not actual >= expected:
        raise AssertionError(message or f"{actual} >= {expected} is not True")


def assert_less(actual, expected, message=None):
    """Raise AssertionError if actual is not less than expected."""
    if not actual < expected:
        raise AssertionError(message or f"{actual} < {expected} is not True")


def assert_less_equal(actual, expected, message=None):
    """Raise AssertionError if actual is not less than or equal to expected."""
    if not actual <= expected:
        raise AssertionError(message or f"{actual} <= {expected} is not True")


def assert_in(item, container, message=None):
    """Raise AssertionError if item is not found in container."""
    if item not in container:
        raise AssertionError(message or f"{item} not found in {container}")
