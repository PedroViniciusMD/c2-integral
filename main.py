from src.core.integral import calcular_integral_indefinida
from src.core.parser import parse_expressao
from src.core.validation import validar_expressao


def calcular(expressao_texto):
    """Calcula a integral indefinida de uma entrada textual."""
    expressao = parse_expressao(expressao_texto)
    validar_expressao(expressao)
    return calcular_integral_indefinida(expressao)


if __name__ == "__main__":
    from src.ui.janela import abrir_janela

    abrir_janela()
