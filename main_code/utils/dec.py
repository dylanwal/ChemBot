from functools import wraps


def wrapper(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        # do something before
        value = func(*args, **kwargs)
        # do something after
        return value
    return _wrapper


def use_unit(unit):
    ...
 