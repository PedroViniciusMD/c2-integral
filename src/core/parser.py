from tokenize import TokenError

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    rationalize,
    standard_transformations,
)

variaveis_permitidas = {
    "x": sp.Symbol("x"),
    "e": sp.E,
    "pi": sp.pi,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "log": sp.log,
    "log10": lambda x: sp.log(x, 10),
    "sqrt": sp.sqrt,
}

transformacoes = standard_transformations + (
    rationalize,
    convert_xor,
    implicit_multiplication_application,
)


def normalizar_expressao(expressao: str) -> str:
    expressao = expressao.replace("\xa0", " ")
    expressao = expressao.strip()
    expressao = expressao.lower()
    
    expressao = expressao.replace("ˆ", "^")
    expressao = expressao.replace("raiz", "sqrt")
    expressao = expressao.replace("sen", "sin")
    expressao = expressao.replace("tg", "tan")
    expressao = expressao.replace("ln", "log")
    
    return expressao


def parse_expressao(expressao: str):
    expressao = normalizar_expressao(expressao)

    if not expressao:
        raise ValueError("A expressão não deve estar vazia")
    
    try:
        return parse_expr(
            expressao,
            local_dict=variaveis_permitidas,
            transformations=transformacoes
        )

    except (SyntaxError, TypeError, ValueError, TokenError):
        raise ValueError("Expressão matemática inválida.")
    
def parse_limite(limite: str):
    """Converte o texto de um limite em uma expressão SymPy."""
    limite = normalizar_expressao(limite)

    if not limite:
        raise ValueError("Limite inválido: informe um valor.")

    constantes_permitidas = {
        nome: valor for nome, valor in variaveis_permitidas.items()
        if nome != "x"
    }

    try:
        return parse_expr(
            limite,
            local_dict=constantes_permitidas,
            transformations=transformacoes
        )

    except (SyntaxError, TypeError, ValueError, TokenError) as erro:
        raise ValueError("Limite inválido.") from erro
