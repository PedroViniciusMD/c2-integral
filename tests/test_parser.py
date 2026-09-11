import pytest
import sympy as sp

from src.core.parser import (
    normalizar_expressao,
    parse_expressao,
)

x = sp.Symbol("x")

# Normalização -----------------------------
def test_normalizar_potencia():
    assert normalizar_expressao("xˆ2") == "x^2"


def test_normalizar_raiz():
    assert normalizar_expressao("raiz(x)") == "sqrt(x)"


def test_normalizar_seno():
    assert normalizar_expressao("sen(x)") == "sin(x)"


def test_normalizar_tangente():
    assert normalizar_expressao("tg(x)") == "tan(x)"


def test_normalizar_ln():
    assert normalizar_expressao("ln(x)") == "log(x)"


def test_normalizar_maiusculas():
    assert normalizar_expressao("SEN(X)") == "sin(x)"

# Parse -------------------------------------
def test_parse_polinomio():
    resultado = parse_expressao("3x^3 - 5x^2 + x - 7")
    esperado = 3*x**3 - 5*x**2 + x - 7

    assert resultado == esperado


def test_parse_fracao():
    resultado = parse_expressao("(x+1)/(x-3)")
    esperado = (x + 1) / (x - 3)

    assert resultado == esperado


def test_parse_raiz():
    resultado = parse_expressao("raiz(x^2 + 4)")
    esperado = sp.sqrt(x**2 + 4)

    assert resultado == esperado


def test_parse_trigonometrica():
    resultado = parse_expressao("2*sen(x) + cos(x)")
    esperado = 2*sp.sin(x) + sp.cos(x)

    assert resultado == esperado


def test_parse_divisoes():
    resultado = parse_expressao("5/x + x/5")
    esperado = 5/x + x/5

    assert resultado == esperado


def test_parse_expoentes_fracionarios():
    resultado = parse_expressao("x^(1/2) + x^(1/3)")
    esperado = x**sp.Rational(1, 2) + x**sp.Rational(1, 3)

    assert resultado == esperado


def test_parse_multiplicacao_implicita():
    resultado = parse_expressao("(2x - 1) * (x + 4)")
    esperado = (2*x - 1) * (x + 4)

    assert resultado == esperado


def test_parse_logaritmos():
    resultado = parse_expressao("log(x) + ln(x^2)")
    esperado = sp.log(x) + sp.log(x**2)

    assert resultado == esperado


def test_parse_funcao_racional():
    resultado = parse_expressao("1/(x^2 - 4)")
    esperado = 1 / (x**2 - 4)

    assert resultado == esperado


def test_parse_raiz_com_multiplicacao_implicita():
    resultado = parse_expressao("raiz(3x + 1) / 2")
    esperado = sp.sqrt(3*x + 1) / 2

    assert resultado == esperado


def test_parse_produto():
    resultado = parse_expressao("x^2 * (x - 1)")
    esperado = x**2 * (x - 1)

    assert resultado == esperado


def test_parse_fracao_polinomial():
    resultado = parse_expressao("(3x^2 + 2x - 1)/(x+2)")
    esperado = (3*x**2 + 2*x - 1) / (x + 2)

    assert resultado == esperado


def test_parse_exponencial():
    resultado = parse_expressao("e^x + e^(-x)")
    esperado = sp.E**x + sp.E**(-x)

    assert resultado == esperado


def test_parse_tangente():
    resultado = parse_expressao("tg(x)/(1 + x^2)")
    esperado = sp.tan(x) / (1 + x**2)

    assert resultado == esperado
    

def test_parse_log10():
    resultado = parse_expressao("log10(x)")
    esperado = sp.log(x, 10)

    assert sp.simplify(resultado - esperado) == 0
    
    
# Erros -------------------------------------
def test_expressao_vazia():
    with pytest.raises(ValueError):
        parse_expressao("")


def test_expressao_so_com_espacos():
    with pytest.raises(ValueError):
        parse_expressao("   ")


def test_expressao_invalida():
    with pytest.raises(ValueError):
        parse_expressao("x^^2")


def test_parenteses_incompletos():
    with pytest.raises(ValueError):
        parse_expressao("(x + 2")
