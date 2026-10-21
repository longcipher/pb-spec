"""Calculator package."""


def add(a: int, b: int) -> int:
    return a + b


def subtract(a: int, b: int) -> int:
    return a - b


def multiply(a: int, b: int) -> int:
    return a * b


def power(base: int, exponent: int) -> int:
    if exponent < 0:
        raise ValueError("exponent must be non-negative")
    return base**exponent
