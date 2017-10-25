"""VALIDATORS"""

from functools import wraps

from polyIntersect.routes.api.v1 import error


def validate_greeting(func):
    """Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if False:
            return error(status=400, detail='middleware validation failed')
        return func(*args, **kwargs)
    return wrapper
