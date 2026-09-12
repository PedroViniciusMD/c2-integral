from src.core.integral import calcular_integral_indefinida
from src.core.parser import parse_expressao
from src.core.validation import validar_expressao


def calcular(expressao_texto):
    expressao = parse_expressao(expressao_texto)

    validar_expressao(expressao)

    return calcular_integral_indefinida(expressao)


integrais = [
    "x - 3",
    "1/2 + 3/4*x^2 - 4/5*x^3",
    "(x + 1)*(2*x - 1)",
    "7*x^(2/5) + 8*x^(-4/5)",
    "e^2",
    "x^(2/3) + x*raiz(x)",
]


# for integral in integrais:
#     try:
#         resultado = calcular(integral)

#         print(f"∫ ({integral}) dx = {resultado} + C")

#     except (ValueError, TypeError) as erro:
#         print(f"{integral} -> ERRO: {erro}")


for integral in integrais:
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
