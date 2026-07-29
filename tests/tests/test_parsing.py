from __future__ import annotations

import pytest

from collector.core.parsing import Br


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("501.000,00", 501000.00),
        ("1.234.567,89", 1234567.89),
        ("0.00", 0.0),
        ("16,50", 16.5),
        ("  250.000,00 ", 250000.00),
        ("", None),
        (None, None),
        ("abc", None),
        (42, 42.0),
    ],
)
def test_numero(entrada, esperado):
    assert Br.numero(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("R$ 86.063,06", 86063.06),
        ("59,47%", 59.47),
        (150000.0, 150000.0),
        (None, None),
    ],
)
def test_moeda(entrada, esperado):
    assert Br.moeda(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Sim", True),
        ("sim", True),
        ("N\u00e3o", False),
        ("nao", False),
        (True, True),
        (False, False),
        ("talvez", None),
        (None, None),
    ],
)
def test_booleano(entrada, esperado):
    assert Br.booleano(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("2 quartos", 2), ("10", 10), ("sem numero", None), (None, None), (3, 3)],
)
def test_inteiro(entrada, esperado):
    assert Br.inteiro(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("47,75 m?", 47.75), ("140.00 de ?rea", 140.0), ("", None), (None, None)],
)
def test_area(entrada, esperado):
    assert Br.area(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("  a   b  ", "a b"), ("texto", "texto"), ("", None), (None, None)],
)
def test_texto(entrada, esperado):
    assert Br.texto(entrada) == esperado
