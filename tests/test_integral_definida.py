import re

import pytest
import sympy as sp

from src.core.integral import calcular_integral_definida as integrar
from src.ui.interface import calcular_integral_definida


def test_calculo_recebe_objetos_sympy():
    resultado = integrar(sp.Symbol("x")**2, sp.Integer(0), sp.Integer(2))

    assert sp.simplify(resultado - sp.Rational(8, 3)) == 0


@pytest.mark.parametrize(
    ("expressao", "inferior", "superior", "esperado"),
    [
        ("x^2", "0", "2", sp.Rational(8, 3)),
        ("x", "-2", "1", sp.Rational(-3, 2)),
        ("x", "0", "1/2", sp.Rational(1, 8)),
        ("x", "0", "pi", sp.pi**2 / 2),
        ("x", "0", "e", sp.E**2 / 2),
        ("x", "0", "raiz(2)", sp.Integer(1)),
        ("pi*x", "0", "1", sp.pi / 2),
        ("x", "0", "0.5", sp.Rational(1, 8)),
        ("0.5x", "0", "1", sp.Rational(1, 4)),
        ("x^2", "2", "0", sp.Rational(-8, 3)),
        ("x^2", "2", "2", sp.Integer(0)),
    ],
)
def test_calcular_integral_definida_regular(
    expressao, inferior, superior, esperado
):
    resultado = calcular_integral_definida(expressao, inferior, superior)

    assert isinstance(resultado, sp.Basic)
    assert not resultado.has(sp.Float)
    assert sp.simplify(resultado - esperado) == 0


@pytest.mark.parametrize(
    ("expressao", "inferior", "superior", "mensagem"),
    [
        ("", "0", "1", "expressão"),
        ("x^^2", "0", "1", "expressão"),
        ("y", "0", "1", "variável x"),
        ("x", "", "1", "limite"),
        ("x", "0", "1+", "limite"),
        ("x", "x", "1", "variáveis"),
        ("x", "0", "y", "variáveis"),
        ("x", "0", "raiz(-1)", "real"),
        ("x", "0", "1/0", "finito"),
    ],
)
def test_rejeitar_entrada_invalida(
    expressao, inferior, superior, mensagem
):
    with pytest.raises((ValueError, TypeError), match=f"(?i){re.escape(mensagem)}"):
        calcular_integral_definida(expressao, inferior, superior)


def test_singularidade_convergente():
    resultado = calcular_integral_definida("1/raiz(x)", "0", "1")

    assert sp.simplify(resultado - sp.Integer(2)) == 0


@pytest.mark.parametrize(
    ("expressao", "inferior", "superior", "esperado"),
    [
        ("1/raiz(1-x)", "0", "1", sp.Integer(2)),
        ("1/raiz(raiz(x^2))", "-1", "1", sp.Integer(4)),
        ("1/raiz(x)", "1", "0", sp.Integer(-2)),
    ],
)
def test_singularidades_convergentes_em_outros_intervalos(
    expressao, inferior, superior, esperado
):
    resultado = calcular_integral_definida(expressao, inferior, superior)

    assert isinstance(resultado, sp.Basic)
    assert not resultado.has(sp.Float)
    assert sp.simplify(resultado - esperado) == 0


@pytest.mark.parametrize(
    ("expressao", "inferior", "superior"),
    [
        ("1/x", "-1", "1"),
        ("1/x", "0", "0"),
        ("1/x", "0", "1"),
        ("1/x", "1", "-1"),
    ],
)
def test_rejeitar_singularidade_divergente(expressao, inferior, superior):
    with pytest.raises(ValueError, match="(?i)singular|divergente"):
        calcular_integral_definida(expressao, inferior, superior)


def test_rejeitar_cancelamento_entre_trechos_divergentes():
    # Cada lado de x=1 diverge, apesar de o valor principal ser zero.
    with pytest.raises(ValueError, match="(?i)divergente"):
        calcular_integral_definida("1/(x-1)", "0", "2")


def test_limites_iguais_em_ponto_regular_continuam_zero():
    assert calcular_integral_definida("1/x", "1", "1") == 0
