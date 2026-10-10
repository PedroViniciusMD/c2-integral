from dataclasses import dataclass

import sympy as sp

from src.core.integral import (
    calcular_integral_definida as integrar_definida,
)
from src.core.integral import (
    calcular_integral_indefinida as integrar_indefinida,
)
from src.core.parser import parse_expressao, parse_limite
from src.core.validation import (
    validar_dominio_real,
    validar_expressao,
    validar_limite,
    validar_ponto_comum,
)


@dataclass(frozen=True)
class ResultadoIntegral:
    """Reúne o resultado e os operandos SymPy validados."""

    expressao: sp.Basic
    resultado: sp.Basic
    limite_inferior: sp.Basic | None = None
    limite_superior: sp.Basic | None = None

    def __post_init__(self):
        if (self.limite_inferior is None) != (self.limite_superior is None):
            raise ValueError("Os limites devem ser informados em conjunto.")


def _executar_com_campo(operacao, valor, campo):
    try:
        return operacao(valor)
    except (ValueError, TypeError) as erro:
        erro.campo_entrada = campo
        raise


def processar_integral_definida(
    expressao_texto, limite_inferior_texto, limite_superior_texto
):
    """Calcula e devolve a integral definida com operandos validados."""
    expressao = _executar_com_campo(parse_expressao, expressao_texto, "expressao")
    limite_inferior = _executar_com_campo(
        parse_limite, limite_inferior_texto, "limite_inferior"
    )
    limite_superior = _executar_com_campo(
        parse_limite, limite_superior_texto, "limite_superior"
    )

    _executar_com_campo(validar_expressao, expressao, "expressao")
    _executar_com_campo(validar_limite, limite_inferior, "limite_inferior")
    _executar_com_campo(validar_limite, limite_superior, "limite_superior")
    validar_ponto_comum(expressao, limite_inferior, limite_superior)
    validar_dominio_real(expressao, limite_inferior, limite_superior)

    resultado = integrar_definida(expressao, limite_inferior, limite_superior)
    return ResultadoIntegral(expressao, resultado, limite_inferior, limite_superior)


def calcular_integral_definida(
    expressao_texto, limite_inferior_texto, limite_superior_texto
):
    """Calcula a integral definida a partir de três entradas textuais."""
    return processar_integral_definida(
        expressao_texto, limite_inferior_texto, limite_superior_texto
    ).resultado


def processar_integral_indefinida(expressao_texto):
    """Calcula e devolve a integral indefinida com a expressão validada."""
    expressao = _executar_com_campo(parse_expressao, expressao_texto, "expressao")
    _executar_com_campo(validar_expressao, expressao, "expressao")

    resultado = integrar_indefinida(expressao)
    if resultado.has(sp.Integral):
        raise ValueError("Integral não resolvida pelo cálculo simbólico.")

    return ResultadoIntegral(expressao, resultado)


def calcular_integral_indefinida(expressao_texto):
    """Calcula a integral indefinida a partir de uma entrada textual."""
    return processar_integral_indefinida(expressao_texto).resultado
