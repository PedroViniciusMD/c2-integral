import sympy as sp
from tokenize import TokenError
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

variaveis_permitidas = {
    "x": sp.Symbol("x"),
    "e": sp.E,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "log": sp.log,
    "log10": lambda x: sp.log(x, 10),
    "sqrt": sp.sqrt,
}

transformacoes = standard_transformations + (convert_xor, implicit_multiplication_application)


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
    limite = limite.strip().lower()

    constantes_permitidas = {
        "pi": sp.pi,
        "e": sp.E,
        "sqrt": sp.sqrt,
    }

    try:
        return parse_expr(
            limite,
            local_dict=constantes_permitidas,
            transformations=transformacoes
        )

    except (SyntaxError, TypeError, ValueError, TokenError) as erro:
        raise ValueError("Limite inválido.") from erro
