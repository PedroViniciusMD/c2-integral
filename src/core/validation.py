import sympy as sp


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
