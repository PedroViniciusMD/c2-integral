import numpy as np
import pytest
import sympy as sp

from src.ui.grafico import (
    criar_figura,
    faixa_definida,
    montar_figura,
    preparar_dados_grafico,
    validar_faixa,
)
from src.ui.interface import (
    ResultadoIntegral,
    processar_integral_definida,
    processar_integral_indefinida,
)


def test_preparacao_numerica_nao_cria_figura(monkeypatch):
    from src.ui import grafico

    x = sp.Symbol("x")
    resultado = ResultadoIntegral(x**2, x**3 / 3)
    with monkeypatch.context() as alteracoes:
        alteracoes.setattr(
            grafico,
            "Figure",
            lambda *_argumentos, **_opcoes: (_ for _ in ()).throw(
                AssertionError("A preparação criou uma figura")
            ),
        )
        dados = preparar_dados_grafico(resultado, (-2, 2))

    figura = montar_figura(dados)

    assert figura.axes[0].get_xlim() == (-2, 2)
    assert np.allclose(
        figura.axes[0].lines[0].get_ydata(),
        figura.axes[0].lines[0].get_xdata() ** 2,
    )
    figura.clear()


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


@pytest.mark.parametrize(
    "esquerda,direita",
    [
        ("2", "1"),
        ("1", "1"),
        ("x", "2"),
        ("oo", "2"),
        ("1+", "2"),
    ],
)
def test_faixa_invalida_e_rejeitada(esquerda, direita):
    with pytest.raises(ValueError):
        validar_faixa(esquerda, direita)


def test_grafico_de_funcao_constante_tem_amostras_em_toda_faixa():
    figura = criar_figura(
        ResultadoIntegral(sp.Integer(3), 3 * sp.Symbol("x")), validar_faixa("-2", "2")
    )
    linha = figura.axes[0].lines[0]

    assert len(linha.get_xdata()) == len(linha.get_ydata())
    assert np.all(linha.get_ydata() == 3)
    figura.clear()


def test_amostras_complexas_nao_sao_convertidas_em_reais():
    x = sp.Symbol("x")
    figura = criar_figura(
        ResultadoIntegral(sp.sqrt(x), 2 * x ** sp.Rational(3, 2) / 3),
        validar_faixa("-1", "1"),
    )
    linha = figura.axes[0].lines[0]
    valores_x = np.asarray(linha.get_xdata())
    valores_y = np.asarray(linha.get_ydata())

    assert np.min(valores_x) == 0
    assert np.isfinite(valores_y).all()
    figura.clear()


def test_amostra_infinita_nao_e_desenhada_como_ponto_valido():
    x = sp.Symbol("x")
    figura = criar_figura(
        ResultadoIntegral(1 / x, sp.log(sp.Abs(x))),
        validar_faixa("-1", "1"),
    )
    trechos = figura.axes[0].lines

    assert len(trechos) == 2
    assert all(np.isfinite(linha.get_ydata()).all() for linha in trechos)
    assert np.max(trechos[0].get_xdata()) < 0
    assert np.min(trechos[1].get_xdata()) > 0
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
    vertices = np.concatenate([caminho.vertices for caminho in regioes[0].get_paths()])

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
    vertices = np.concatenate([caminho.vertices for caminho in regioes[0].get_paths()])

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
    assert not np.array_equal(regioes[0].get_facecolor(), regioes[1].get_facecolor())
    assert any(
        np.min(pontos[:, 1]) >= 0 and np.max(pontos[:, 0]) > 0 for pontos in vertices
    )
    assert any(
        np.max(pontos[:, 1]) <= 0 and np.min(pontos[:, 0]) < 0 for pontos in vertices
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
    caminhos = [caminho for regiao in regioes for caminho in regiao.get_paths()]

    assert len(caminhos) == 2
    assert all(np.isfinite(caminho.vertices).all() for caminho in caminhos)
    assert any(np.min(caminho.vertices[:, 0]) < 0 for caminho in caminhos)
    assert any(np.max(caminho.vertices[:, 0]) > 0 for caminho in caminhos)
    assert all(
        np.max(caminho.vertices[:, 0]) <= 0 or np.min(caminho.vertices[:, 0]) >= 0
        for caminho in caminhos
    )
    figura.clear()


def test_polo_fora_da_malha_nao_liga_lados_da_curva():
    x = sp.Symbol("x")
    polo = sp.Rational(1, 3)
    resultado = ResultadoIntegral(1 / (x - polo), sp.log(sp.Abs(x - polo)))

    figura = criar_figura(resultado, validar_faixa("0", "1"))
    trechos = [np.asarray(linha.get_xdata()) for linha in figura.axes[0].lines]

    assert len(trechos) == 2
    assert all(
        np.max(trecho) < float(polo) or np.min(trecho) > float(polo)
        for trecho in trechos
    )
    figura.clear()


@pytest.mark.parametrize(
    ("expressao", "esquerda", "direita", "polo"),
    [
        (lambda x: 1 / x, "-1", "1", 0),
        (lambda x: 1 / x**2, "-1", "1", 0),
        (lambda x: 1 / (x - 1), "0", "2", 1),
    ],
)
def test_assintotas_conhecidas_separam_a_curva(expressao, esquerda, direita, polo):
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(expressao(x), sp.Integer(0))

    figura = criar_figura(resultado, validar_faixa(esquerda, direita))
    trechos = [np.asarray(linha.get_xdata()) for linha in figura.axes[0].lines]

    assert len(trechos) == 2
    assert np.max(trechos[0]) < polo
    assert np.min(trechos[1]) > polo
    figura.clear()


@pytest.mark.parametrize(
    ("expressao", "inicio_valido"),
    [(sp.log, False), (sp.sqrt, True)],
)
def test_dominio_parcial_nao_desenha_x_negativo(expressao, inicio_valido):
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(expressao(x), sp.Integer(0))

    figura = criar_figura(resultado, validar_faixa("-2", "2"))
    trechos = figura.axes[0].lines
    amostras_x = np.asarray(trechos[0].get_xdata())

    assert len(trechos) == 1
    if inicio_valido:
        assert np.min(amostras_x) == 0
    else:
        assert np.min(amostras_x) > 0
    assert np.isfinite(trechos[0].get_ydata()).all()
    figura.clear()


@pytest.mark.parametrize(
    "expressao", [sp.sin, lambda x: x**2, lambda x: sp.exp(100 * x)]
)
def test_funcoes_continuas_nao_recebem_cortes_artificiais(expressao):
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(expressao(x), sp.Integer(0))

    figura = criar_figura(resultado, validar_faixa("-1", "1"))

    assert len(figura.axes[0].lines) == 1
    assert np.min(figura.axes[0].lines[0].get_xdata()) == -1
    assert np.max(figura.axes[0].lines[0].get_xdata()) == 1
    figura.clear()


def test_singularidade_convergente_na_extremidade_sombreia_trecho_finito():
    resultado = processar_integral_definida("1/raiz(x)", "0", "1")

    figura = criar_figura(resultado)
    eixo = figura.axes[0]
    pontos_curva = np.asarray(eixo.lines[0].get_xdata())
    caminhos = [
        caminho for regiao in eixo.collections for caminho in regiao.get_paths()
    ]

    assert sp.simplify(resultado.resultado - 2) == 0
    assert np.min(pontos_curva) > 0
    assert len(caminhos) >= 1
    assert all(np.min(caminho.vertices[:, 0]) > 0 for caminho in caminhos)
    assert all(np.isfinite(caminho.vertices).all() for caminho in caminhos)
    assert any("aproximado" in texto.get_text() for texto in eixo.texts)
    figura.clear()


@pytest.fixture
def sem_analise_simbolica(monkeypatch):
    from src.ui import grafico

    def analise_indisponivel(*_argumentos):
        raise NotImplementedError

    monkeypatch.setattr(grafico, "continuous_domain", analise_indisponivel)
    monkeypatch.setattr(grafico, "singularities", analise_indisponivel)


@pytest.mark.parametrize("polo", [sp.Rational(1, 800), sp.Rational(1, 3)])
def test_falha_da_analise_simbolica_usa_sondagem_numerica(sem_analise_simbolica, polo):
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(1 / (x - polo), sp.Integer(0))

    figura = criar_figura(resultado, validar_faixa("0", "1"))
    trechos = [np.asarray(linha.get_xdata()) for linha in figura.axes[0].lines]

    assert len(trechos) == 2
    assert np.max(trechos[0]) < float(polo)
    assert np.min(trechos[1]) > float(polo)
    figura.clear()


@pytest.mark.parametrize(
    ("expressao", "esquerda", "direita", "polo"),
    [
        (lambda x: 1 / x, "-1", "1", 0),
        (lambda x: 1 / x**2, "-1", "1", 0),
        (lambda x: 1 / (x - 1), "0", "2", 1),
    ],
)
def test_falha_simbolica_mantem_polos_amostrados_separados(
    sem_analise_simbolica, expressao, esquerda, direita, polo
):
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(expressao(x), sp.Integer(0))

    figura = criar_figura(resultado, validar_faixa(esquerda, direita))
    trechos = [np.asarray(linha.get_xdata()) for linha in figura.axes[0].lines]

    assert len(trechos) == 2
    assert np.max(trechos[0]) < polo
    assert np.min(trechos[1]) > polo
    figura.clear()


def test_sondagem_conservadora_preserva_crescimento_continuo(sem_analise_simbolica):
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(
        (x - sp.Rational(1, 3)) * sp.exp(100 * x), sp.Integer(0)
    )

    figura = criar_figura(resultado, validar_faixa("-1", "1"))

    assert len(figura.axes[0].lines) == 1
    figura.clear()


def test_sondagem_nao_corta_transicao_continua_estreita(sem_analise_simbolica):
    x = sp.Symbol("x")
    centro = sp.Rational(33337, 100000)
    deslocamento = x - centro
    expressao = deslocamento / (deslocamento**2 + sp.Rational(1, 10**18))
    resultado = ResultadoIntegral(expressao, sp.Integer(0))

    figura = criar_figura(resultado, validar_faixa("0", "1"))

    assert len(figura.axes[0].lines) == 1
    assert np.min(figura.axes[0].lines[0].get_xdata()) == 0
    assert np.max(figura.axes[0].lines[0].get_xdata()) == 1
    figura.clear()


def test_sondagem_numerica_descarta_amostras_complexas(sem_analise_simbolica):
    x = sp.Symbol("x")
    resultado = ResultadoIntegral(sp.sqrt(x), sp.Integer(0))

    figura = criar_figura(resultado, validar_faixa("-1", "1"))
    trechos = figura.axes[0].lines

    assert len(trechos) == 1
    assert np.min(trechos[0].get_xdata()) == 0
    assert np.isfinite(trechos[0].get_ydata()).all()
    figura.clear()


def test_singularidade_integravel_fora_da_malha_separa_curva_e_sombreado():
    x = sp.Symbol("x")
    polo = sp.Rational(1, 3)
    expressao = 1 / sp.sqrt(sp.Abs(x - polo))
    resultado = ResultadoIntegral(
        expressao,
        2 * (sp.sqrt(polo) + sp.sqrt(1 - polo)),
        sp.Integer(0),
        sp.Integer(1),
    )

    figura = criar_figura(resultado)
    eixo = figura.axes[0]
    trechos_curva = [np.asarray(linha.get_xdata()) for linha in eixo.lines]
    caminhos = [
        caminho for regiao in eixo.collections for caminho in regiao.get_paths()
    ]

    assert len(trechos_curva) == 2
    assert len(caminhos) == 2
    assert all(
        np.max(trecho) < float(polo) or np.min(trecho) > float(polo)
        for trecho in trechos_curva
    )
    assert all(
        np.max(caminho.vertices[:, 0]) < float(polo)
        or np.min(caminho.vertices[:, 0]) > float(polo)
        for caminho in caminhos
    )
    figura.clear()
