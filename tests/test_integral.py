import sympy as sp

from src.core.integral import calcular_integral_indefinida

x = sp.Symbol("x")

#polinomial
def test_integral_polinomial():
    expressao = x**2 + 2*x

    resultado = calcular_integral_indefinida(expressao)

    esperado = x**3 / 3 + x**2

    assert sp.simplify(resultado - esperado) == 0
    
def test_integral_polinomial_completa():
    expressao = 3*x**3 - 5*x**2 + x - 7

    resultado = calcular_integral_indefinida(expressao)

    esperado = (
        3*x**4 / 4
        - 5*x**3 / 3
        + x**2 / 2
        - 7*x
    )

    assert sp.simplify(resultado - esperado) == 0
    

#constante
def test_integral_constante():
    expressao = sp.Integer(5)

    resultado = calcular_integral_indefinida(expressao)

    esperado = 5*x

    assert sp.simplify(resultado - esperado) == 0


#trigonométrica 
def test_integral_seno():
    expressao = sp.sin(x)

    resultado = calcular_integral_indefinida(expressao)

    esperado = -sp.cos(x)

    assert sp.simplify(resultado - esperado) == 0
    
def test_integral_cosseno():
    expressao = sp.cos(x)

    resultado = calcular_integral_indefinida(expressao)

    esperado = sp.sin(x)

    assert sp.simplify(resultado - esperado) == 0
    

#exponencial
def test_integral_exponencial():
    expressao = sp.exp(x)

    resultado = calcular_integral_indefinida(expressao)

    esperado = sp.exp(x)

    assert sp.simplify(resultado - esperado) == 0
    
def test_integral_raiz():
    expressao = sp.sqrt(x)

    resultado = calcular_integral_indefinida(expressao)

    esperado = 2 * x**sp.Rational(3, 2) / 3

    assert sp.simplify(resultado - esperado) == 0
    
def test_integral_exponencial_composta():
    expressao = sp.exp(2*x)

    resultado = calcular_integral_indefinida(expressao)

    esperado = sp.exp(2*x) / 2

    assert sp.simplify(resultado - esperado) == 0

    
#racional
def test_integral_um_sobre_x():
    expressao = 1 / x

    resultado = calcular_integral_indefinida(expressao)

    esperado = sp.log(x)

    assert sp.simplify(resultado - esperado) == 0
