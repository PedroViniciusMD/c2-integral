import sympy as sp


#Indefinida
def calcular_integral_indefinida(expressao):
    x = sp.Symbol("x")
    resultado = sp.integrate(expressao, x)
    return resultado

#Definida
def calcular_integral_definida(expressao, limite_inferior, limite_superior):
    """Calcula uma integral definida de objetos SymPy em relação a x."""
    x = sp.Symbol("x")
    return sp.integrate(expressao, (x, limite_inferior, limite_superior))
