import sympy as sp
from sympy.calculus.util import continuous_domain, singularities


def validar_variaveis(expressao):
    variaveis = expressao.free_symbols

    x = sp.Symbol("x")

    if not variaveis.issubset({x}):
        raise ValueError(
            "A expressão deve conter apenas a variável x.")

def validar_expressao(expressao):
    if not isinstance(expressao, sp.Basic):
        raise TypeError(
            "A expressão deve ser uma expressão matemática válida.")

    validar_variaveis(expressao)
    
def validar_limite(limite):
    if not isinstance(limite, sp.Basic):
        raise TypeError(
            "O limite deve ser um valor matemático válido."
        )

    if limite.free_symbols:
        raise ValueError(
            "O limite não pode conter variáveis."
        )

    if limite.is_finite is not True:
        raise ValueError(
            "O limite deve ser um número finito."
        )

    if limite.is_real is not True:
        raise ValueError(
            "O limite deve ser um número real."
        )

def validar_limites(limite_inferior, limite_superior):
    validar_limite(limite_inferior)
    validar_limite(limite_superior)


def validar_ponto_comum(expressao, limite_inferior, limite_superior):
    """Exige que a expressão esteja definida em limites iguais."""
    if limite_inferior != limite_superior:
        return

    valor = expressao.subs(sp.Symbol("x"), limite_inferior)
    if valor.is_real is not True or valor.is_finite is not True:
        raise ValueError("A expressão é singular no limite informado.")


def validar_dominio_real(expressao, limite_inferior, limite_superior):
    """Rejeita trechos comprovadamente complexos no intervalo."""
    if limite_inferior == limite_superior:
        return

    x = sp.Symbol("x")
    inferior, superior = sorted((limite_inferior, limite_superior))
    intervalo = sp.Interval(inferior, superior)
    singularidades = singularities(expressao, x)
    variavel_real = sp.Symbol("x", real=True)
    parte_imaginaria = sp.simplify(
        sp.im(expressao.xreplace({x: variavel_real}))
    )
    try:
        pontos_reais = sp.solveset(parte_imaginaria, variavel_real, intervalo)
    except NotImplementedError:
        pontos_reais = None
    if pontos_reais is not None:
        if (intervalo - pontos_reais - singularidades).is_empty is False:
            raise ValueError("A expressão está fora do domínio real no intervalo.")

    try:
        dominio = continuous_domain(expressao, x, intervalo)
    except NotImplementedError:
        dominio = intervalo

    fora = intervalo - dominio - singularidades
    partes = fora.args if isinstance(fora, sp.Union) else (fora,)
    amostras = []
    for parte in partes:
        if isinstance(parte, sp.Interval):
            amostras.append((parte.inf + parte.sup) / 2)
        elif isinstance(parte, sp.FiniteSet):
            amostras.extend(parte)

    if any(expressao.subs(x, ponto).is_real is False for ponto in amostras):
        raise ValueError("A expressão está fora do domínio real no intervalo.")
