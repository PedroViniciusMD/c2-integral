from dataclasses import FrozenInstanceError

import pytest
import sympy as sp

from src.ui.interface import (
    ResultadoIntegral,
    calcular_integral_indefinida,
    processar_integral_definida,
    processar_integral_indefinida,
)


def test_resultado_estruturado_da_integral_definida_preserva_valores_exatos():
    resultado = processar_integral_definida("0.5x", "0", "1/2")

    assert isinstance(resultado, ResultadoIntegral)
    assert sp.simplify(resultado.expressao - sp.Symbol("x") / 2) == 0
    assert sp.simplify(resultado.resultado - sp.Rational(1, 16)) == 0
    assert resultado.limite_inferior == sp.Integer(0)
    assert resultado.limite_superior == sp.Rational(1, 2)
    assert not resultado.resultado.has(sp.Float)


def test_resultado_estruturado_da_integral_indefinida_nao_tem_limites():
    resultado = processar_integral_indefinida("x^2")

    assert isinstance(resultado, ResultadoIntegral)
    assert sp.simplify(resultado.expressao - sp.Symbol("x") ** 2) == 0
    assert sp.simplify(resultado.resultado - sp.Symbol("x") ** 3 / 3) == 0
    assert resultado.limite_inferior is None
    assert resultado.limite_superior is None

    with pytest.raises(FrozenInstanceError):
        resultado.resultado = sp.Integer(0)


def test_resultado_estruturado_preserva_a_ordem_dos_limites():
    resultado = processar_integral_definida("x^2", "2", "0")

    assert resultado.limite_inferior == sp.Integer(2)
    assert resultado.limite_superior == sp.Integer(0)
    assert sp.simplify(resultado.resultado + sp.Rational(8, 3)) == 0


def test_operacao_textual_indefinida_retorna_apenas_expressao_sympy():
    resultado = calcular_integral_indefinida("2x")

    assert isinstance(resultado, sp.Basic)
    assert sp.simplify(resultado - sp.Symbol("x") ** 2) == 0


@pytest.mark.parametrize("texto", ["", "x^^2", "y"])
def test_operacao_textual_indefinida_rejeita_entrada_invalida(texto):
    with pytest.raises(ValueError, match="(?i)expressão|variável"):
        calcular_integral_indefinida(texto)


def test_operacoes_indefinidas_rejeitam_integral_nao_resolvida():
    with pytest.raises(ValueError, match="(?i)não resolvida"):
        calcular_integral_indefinida("e^(x^x)")

    with pytest.raises(ValueError, match="(?i)não resolvida"):
        processar_integral_indefinida("e^(x^x)")


def test_operacao_indefinida_rejeita_integral_nao_resolvida_aninhada(
    monkeypatch,
):
    x = sp.Symbol("x")
    pendente = sp.Integral(sp.exp(x**x), x)
    monkeypatch.setattr(sp, "integrate", lambda *args: x + pendente)

    with pytest.raises(ValueError, match="(?i)não resolvida"):
        calcular_integral_indefinida("x")


def test_resultado_estruturado_da_definida_rejeita_dominio_invalido():
    with pytest.raises(ValueError, match="(?i)domínio real"):
        processar_integral_definida("raiz(x)", "-1", "1")


def test_resultado_estruturado_exige_o_par_completo_de_limites():
    with pytest.raises(ValueError, match="(?i)limites"):
        ResultadoIntegral(
            sp.Symbol("x"),
            sp.Symbol("x") ** 2 / 2,
            sp.Integer(0),
        )
