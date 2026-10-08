import numpy as np
import pytest
import sympy as sp

from src.ui.interface import (
    ResultadoIntegral,
    processar_integral_definida,
    processar_integral_indefinida,
)
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


def test_integral_definida_positiva_sombreia_somente_entre_limites():
    resultado = processar_integral_definida("x^2", "0", "2")

    figura = criar_figura(resultado)
    regioes = figura.axes[0].collections
    vertices = np.concatenate(
        [caminho.vertices for caminho in regioes[0].get_paths()]
    )

    assert len(regioes) == 1
    assert np.min(vertices[:, 0]) >= 0
    assert np.max(vertices[:, 0]) <= 2
    assert np.min(vertices[:, 1]) >= 0
    assert np.max(vertices[:, 1]) > 0
    assert sp.simplify(resultado.resultado - sp.Rational(8, 3)) == 0
    figura.clear()


def test_integral_definida_negativa_sombreia_abaixo_do_eixo():
    resultado = processar_integral_definida("-x^2", "0", "2")

    figura = criar_figura(resultado)
    regioes = figura.axes[0].collections
    vertices = np.concatenate(
        [caminho.vertices for caminho in regioes[0].get_paths()]
    )

    assert len(regioes) == 1
    assert np.min(vertices[:, 0]) >= 0
    assert np.max(vertices[:, 0]) <= 2
    assert np.max(vertices[:, 1]) <= 0
    assert np.min(vertices[:, 1]) < 0
    assert sp.simplify(resultado.resultado + sp.Rational(8, 3)) == 0
    figura.clear()


def test_cruzamento_do_eixo_distingue_contribuicoes():
    resultado = processar_integral_definida("x", "-1", "1")

    figura = criar_figura(resultado)
    regioes = figura.axes[0].collections
    vertices = [
        np.concatenate([caminho.vertices for caminho in regiao.get_paths()])
        for regiao in regioes
    ]

    assert len(regioes) == 2
    assert not np.array_equal(
        regioes[0].get_facecolor(), regioes[1].get_facecolor()
    )
    assert any(
        np.min(pontos[:, 1]) >= 0 and np.max(pontos[:, 0]) > 0
        for pontos in vertices
    )
    assert any(
        np.max(pontos[:, 1]) <= 0 and np.min(pontos[:, 0]) < 0
        for pontos in vertices
    )
    assert all(np.min(pontos[:, 0]) >= -1 for pontos in vertices)
    assert all(np.max(pontos[:, 0]) <= 1 for pontos in vertices)
    assert sp.simplify(resultado.resultado) == 0
    figura.clear()


def test_limites_invertidos_preservam_regiao_e_indicam_orientacao():
    direto = processar_integral_definida("x^2", "0", "2")
    invertido = processar_integral_definida("x^2", "2", "0")

    figura_direta = criar_figura(direto)
    figura_invertida = criar_figura(invertido)
    caminho_direto = figura_direta.axes[0].collections[0].get_paths()[0]
    caminho_invertido = figura_invertida.axes[0].collections[0].get_paths()[0]

    assert np.array_equal(caminho_direto.vertices, caminho_invertido.vertices)
    assert "direita para a esquerda" in figura_invertida.axes[0].get_title()
    assert sp.simplify(direto.resultado + invertido.resultado) == 0
    assert sp.simplify(invertido.resultado + sp.Rational(8, 3)) == 0
    figura_direta.clear()
    figura_invertida.clear()


def test_limites_iguais_nao_criam_sombreado_artificial():
    resultado = processar_integral_definida("x^2", "1", "1")

    figura = criar_figura(resultado)

    assert len(figura.axes[0].collections) == 0
    assert sp.simplify(resultado.resultado) == 0
    figura.clear()


def test_integral_indefinida_nao_recebe_sombreado():
    resultado = processar_integral_indefinida("x^2")

    figura = criar_figura(resultado, validar_faixa("-10", "10"))

    assert len(figura.axes[0].collections) == 0
    assert figura.axes[0].get_title() == ""
    figura.clear()


def test_amostra_invalida_interrompe_sombreado():
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(
        sp.sin(x) / x, 2 * sp.Si(1), sp.Integer(-1), sp.Integer(1)
    )

    figura = criar_figura(resultado)
    regioes = figura.axes[0].collections
    caminhos = regioes[0].get_paths()

    assert len(regioes) == 1
    assert len(caminhos) == 2
    assert all(np.isfinite(caminho.vertices).all() for caminho in caminhos)
    assert any(np.min(caminho.vertices[:, 0]) < 0 for caminho in caminhos)
    assert any(np.max(caminho.vertices[:, 0]) > 0 for caminho in caminhos)
    assert all(
        np.max(caminho.vertices[:, 0]) <= 0
        or np.min(caminho.vertices[:, 0]) >= 0
        for caminho in caminhos
    )
    figura.clear()
