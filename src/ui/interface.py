from src.core.integral import calcular_integral_definida as integrar
from src.core.parser import parse_expressao, parse_limite
from src.core.validation import (
    validar_dominio_real,
    validar_expressao,
    validar_limites,
    validar_ponto_comum,
)


def calcular_integral_definida(
    expressao_texto, limite_inferior_texto, limite_superior_texto
):
    """Calcula a integral definida a partir de três entradas textuais."""
    expressao = parse_expressao(expressao_texto)
    limite_inferior = parse_limite(limite_inferior_texto)
    limite_superior = parse_limite(limite_superior_texto)

    validar_expressao(expressao)
    validar_limites(limite_inferior, limite_superior)
    validar_ponto_comum(expressao, limite_inferior, limite_superior)
    validar_dominio_real(expressao, limite_inferior, limite_superior)

    return integrar(expressao, limite_inferior, limite_superior)
