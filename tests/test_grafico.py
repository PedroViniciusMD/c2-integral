import numpy as np
import pytest
import sympy as sp

from src.ui.interface import ResultadoIntegral
from src.ui.grafico import criar_figura, faixa_definida, validar_faixa


def test_grafico_indefinido_usa_funcao_original_e_faixa_inicial():
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(x**2, x**3 / 3)

    figura = criar_figura(resultado, validar_faixa("-10", "10"))
    linha = figura.axes[0].lines[0]

    assert figura.axes[0].get_xlim() == (-10, 10)
    assert np.isclose(linha.get_ydata()[0], 100)
    assert np.isclose(linha.get_ydata()[-1], 100)
    figura.clear()


def test_faixa_editada_aceita_constantes_exatas():
    esquerda, direita = validar_faixa("-pi", "1/2")

    assert esquerda == -sp.pi
    assert direita == sp.Rational(1, 2)


@pytest.mark.parametrize("esquerda,direita", [
    ("2", "1"), ("1", "1"), ("x", "2"), ("oo", "2"),
    ("1+", "2"),
])
def test_faixa_invalida_e_rejeitada(esquerda, direita):
    with pytest.raises(ValueError):
        validar_faixa(esquerda, direita)


def test_grafico_de_funcao_constante_tem_amostras_em_toda_faixa():
    figura = criar_figura(ResultadoIntegral(sp.Integer(3), 3 * sp.Symbol("x")),
                          validar_faixa("-2", "2"))
    linha = figura.axes[0].lines[0]

    assert len(linha.get_xdata()) == len(linha.get_ydata())
    assert np.all(linha.get_ydata() == 3)
    figura.clear()


def test_amostras_complexas_nao_sao_convertidas_em_reais():
    x = sp.Symbol("x")
    figura = criar_figura(ResultadoIntegral(sp.sqrt(x), 2 * x**sp.Rational(3, 2) / 3),
                          validar_faixa("-1", "1"))
    linha = figura.axes[0].lines[0]
    valores_x = np.asarray(linha.get_xdata())
    valores_y = np.asarray(linha.get_ydata())

    assert np.isnan(valores_y[valores_x < 0]).all()
    assert np.isfinite(valores_y[valores_x > 0]).all()
    figura.clear()


def test_amostra_infinita_nao_e_desenhada_como_ponto_valido():
    x = sp.Symbol("x")
    figura = criar_figura(
        ResultadoIntegral(1 / x, sp.log(sp.Abs(x))),
        validar_faixa("-1", "1"),
    )
    linha = figura.axes[0].lines[0]
    amostras_x = np.asarray(linha.get_xdata())
    amostras_y = np.asarray(linha.get_ydata())
    indice_zero = np.flatnonzero(amostras_x == 0)

    assert len(indice_zero) == 1
    assert np.isnan(amostras_y[indice_zero[0]])
    assert np.isfinite(amostras_y[indice_zero[0] - 1])
    assert np.isfinite(amostras_y[indice_zero[0] + 1])
    figura.clear()


def test_faixa_definida_tem_margem_e_trata_limites_iguais():
    x = sp.Symbol("x")
    invertida = ResultadoIntegral(x, sp.Integer(-2), sp.Integer(2), sp.Integer(0))
    igual = ResultadoIntegral(x, sp.Integer(0), sp.Integer(1), sp.Integer(1))

    assert faixa_definida(invertida) == (-0.2, 2.2)
    esquerda, direita = faixa_definida(igual)
    assert esquerda < 1 < direita
    assert np.isfinite([esquerda, direita]).all()
