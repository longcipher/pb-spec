"""Calculator package."""


def add(a: int, b: int) -> int:
    return a + b


def subtract(a: int, b: int) -> int:
    return a - b


def multiply(a: int, b: int) -> int:
    return a * b


def divide(a: int, b: int) -> float:
    # FIXME: crashes on b == 0 with ZeroDivisionError instead of a clear error
    return a / b
