from src.core.integral import calcular_integral_indefinida
from src.core.parser import parse_expressao
from src.core.validation import validar_expressao
from src.ui.interface import calcular_integral_definida


def calcular(expressao_texto):
    expressao = parse_expressao(expressao_texto)

    validar_expressao(expressao)

    return calcular_integral_indefinida(expressao)


integrais_indefinidas = [
    "raiz(2)",
    "3*raiz(x) - 2*xˆ(1/3)",
    "1/5 - 2/x",
    "(1 + x + xˆ2)/raiz(x)",
    "(1/cos(x))*tg(x) - 2e^x",
    "2sen(x) - 1/(cos(x)^2)",
    "2raiz(x) + 6cos(x)",
    "(2 + x^2)/(1 + x^2)",
]


integrais_definidas = [
    ("4 - 2x", "2", "5"),
    ("x^2 + x", "-2", "0"),
    ("2x - x^3", "0", "2"),
    ("x^3 - 3x^2", "0", "1"),
]


print("=" * 50)
print("INTEGRAIS INDEFINIDAS")
print("=" * 50)

for integral in integrais_indefinidas:
    try:
        expressao = parse_expressao(integral)

        validar_expressao(expressao)

        resultado = calcular_integral_indefinida(expressao)

        print(f"Entrada: {integral}")
        print(f"Interpretada: {expressao}")
        print(f"Resultado: {resultado} + C")
        print("-" * 50)

    except (ValueError, TypeError) as erro:
        print(f"Erro em '{integral}': {erro}")
        print("-" * 50)


print()
print("=" * 50)
print("INTEGRAIS DEFINIDAS")
print("=" * 50)

for expressao, limite_inferior, limite_superior in integrais_definidas:
    try:
        resultado = calcular_integral_definida(
            expressao,
            limite_inferior,
            limite_superior
        )

        print(f"Entrada: {expressao}")
        print(f"Limites: [{limite_inferior}, {limite_superior}]")
        print(f"Resultado: {resultado}")
        print("-" * 50)

    except (ValueError, TypeError) as erro:
        print(
            f"Erro em '{expressao}' "
            f"[{limite_inferior}, {limite_superior}]: {erro}"
        )
        print("-" * 50)