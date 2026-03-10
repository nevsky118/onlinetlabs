def assert_equal(actual, expected, message=None):
    if actual != expected:
        raise AssertionError(message or f"{actual} != {expected}")


def assert_not_equal(actual, expected, message=None):
    if actual == expected:
        raise AssertionError(message or f"{actual} == {expected}")


def assert_true(value, message=None):
    if not value:
        raise AssertionError(message or f"Expected True, but got {value}")


def assert_false(value, message=None):
    if value:
        raise AssertionError(message or f"Expected False, but got {value}")


def assert_is_none(value, message=None):
    if value is not None:
        raise AssertionError(message or f"Expected None, but got {value}")


def assert_is_not_none(value, message=None):
    if value is None:
        raise AssertionError(message or "Expected value to be not None")


def assert_greater(actual, expected, message=None):
    if not actual > expected:
        raise AssertionError(message or f"{actual} > {expected} is not True")


def assert_greater_equal(actual, expected, message=None):
    if not actual >= expected:
        raise AssertionError(message or f"{actual} >= {expected} is not True")


def assert_less(actual, expected, message=None):
    if not actual < expected:
        raise AssertionError(message or f"{actual} < {expected} is not True")


def assert_less_equal(actual, expected, message=None):
    if not actual <= expected:
        raise AssertionError(message or f"{actual} <= {expected} is not True")


def assert_in(item, container, message=None):
    if item not in container:
        raise AssertionError(message or f"{item} not found in {container}")
