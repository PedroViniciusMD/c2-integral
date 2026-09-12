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

    if limite.is_real is False:
        raise ValueError(
            "O limite deve ser um número real."
        )

def validar_limites(limite_inferior, limite_superior):
    validar_limite(limite_inferior)
    validar_limite(limite_superior)
