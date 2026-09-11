import sympy as sp


#Indefinida
def calcular_integral_indefinida(expressao):
    x = sp.Symbol("x")
    resultado = sp.integrate(expressao, x)
    return resultado

