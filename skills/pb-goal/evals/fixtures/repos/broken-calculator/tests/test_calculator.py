import pytest
from calculator import add, multiply, power, subtract


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 2) == 3


def test_multiply():
    assert multiply(3, 4) == 12


def test_power_non_negative():
    assert power(2, 10) == 1024


def test_power_zero():
    assert power(0, 0) == 1


def test_power_negative_raises():
    with pytest.raises(ValueError):
        power(2, -1)
