import sympy as sp
from sympy.calculus.util import singularities


# Indefinida
def calcular_integral_indefinida(expressao):
    x = sp.Symbol("x")
    resultado = sp.integrate(expressao, x)
    return resultado


# Definida
def calcular_integral_definida(expressao, limite_inferior, limite_superior):
    """Calcula uma integral definida de objetos SymPy em relação a x."""
    x = sp.Symbol("x")
    if limite_inferior == limite_superior:
        return sp.Integer(0)

    inferior, superior = sorted((limite_inferior, limite_superior))
    pontos = singularities(expressao, x).intersect(sp.Interval(inferior, superior))
    if not pontos.is_FiniteSet:
        raise ValueError("Não foi possível verificar a convergência da integral.")

    limites = [inferior, *sorted(pontos - {inferior, superior}), superior]
    resultado = sp.Integer(0)
    for inicio, fim in zip(limites, limites[1:]):
        trecho = sp.integrate(expressao, (x, inicio, fim))
        if trecho.has(sp.Integral):
            raise ValueError("Integral não resolvida pelo cálculo simbólico.")
        if (
            trecho.has(sp.nan, sp.zoo, sp.oo, -sp.oo)
            or trecho.is_finite is False
            or trecho.is_real is False
        ):
            raise ValueError("A integral é divergente ou tem resultado inválido.")
        resultado += trecho

    if resultado.has(sp.Integral):
        raise ValueError("Integral não resolvida pelo cálculo simbólico.")
    if resultado.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
        raise ValueError("A integral é divergente ou tem resultado inválido.")
    return resultado if limite_inferior == inferior else -resultado
