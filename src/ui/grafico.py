"""Prepara a visualização numérica da função de uma integral."""

from dataclasses import dataclass

import numpy as np
import sympy as sp
from matplotlib.figure import Figure
from sympy.calculus.util import continuous_domain, singularities

from src.core.parser import parse_limite
from src.core.validation import validar_limite


@dataclass(frozen=True)
class DadosGrafico:
    """Transporta amostras prontas para desenhar na thread da interface."""

    esquerda: float
    direita: float
    trechos: tuple
    limites: tuple | None
    orientacao_invertida: bool


def validar_faixa(esquerda_texto, direita_texto):
    """Converte e valida extremos textuais da visualização indefinida."""
    esquerda = parse_limite(esquerda_texto)
    direita = parse_limite(direita_texto)
    validar_limite(esquerda)
    validar_limite(direita)
    if (direita - esquerda).is_positive is not True:
        raise ValueError("O extremo esquerdo deve ser menor que o direito.")
    return esquerda, direita


def faixa_definida(resultado):
    """Enquadra os limites validados com uma margem horizontal."""
    esquerda, direita = _extremos_definidos(resultado)
    if not np.isfinite([esquerda, direita]).all():
        raise ValueError("Os limites não cabem na faixa do gráfico.")
    margem = (direita - esquerda) * 0.1 if esquerda != direita else 1.0
    return esquerda - margem, direita + margem


def _extremos_definidos(resultado):
    return sorted(
        (float(resultado.limite_inferior), float(resultado.limite_superior))
    )


def _amostrar(funcao, amostras_x):
    with np.errstate(all="ignore"):
        valores = np.asarray(funcao(amostras_x), dtype=complex)
        valores = np.broadcast_to(valores, amostras_x.shape)
    return np.where(
        np.isreal(valores) & np.isfinite(valores), valores.real, np.nan
    )


def _intervalos_continuos(expressao, esquerda, direita):
    x = sp.Symbol("x")
    faixa = sp.Interval(esquerda, direita)
    dominio = faixa
    analise_completa = True
    try:
        dominio = continuous_domain(expressao, x, faixa)
    except Exception:
        analise_completa = False
    try:
        dominio -= singularities(expressao, x).intersect(faixa)
    except Exception:
        analise_completa = False
    if dominio is sp.EmptySet:
        return [], analise_completa
    intervalos = dominio.args if isinstance(dominio, sp.Union) else (dominio,)
    if not all(isinstance(intervalo, sp.Interval) for intervalo in intervalos):
        return [faixa], False
    return (
        sorted(intervalos, key=lambda intervalo: float(intervalo.start)),
        analise_completa,
    )


def _polo_suspeito(funcao, esquerda, direita, valor_esquerdo, valor_direito):
    # Sem apoio simbólico, polos sem troca de sinal ou detalhes menores que a
    # resolução desta sondagem ainda podem escapar ou parecer descontinuidades.
    if not (valor_esquerdo and valor_direito):
        return False
    if np.signbit(valor_esquerdo) == np.signbit(valor_direito):
        return False
    referencia = max(abs(valor_esquerdo), abs(valor_direito))
    pico_esquerdo = abs(valor_esquerdo)
    pico_direito = abs(valor_direito)
    for _ in range(30):
        meio = esquerda + (direita - esquerda) / 2
        if meio == esquerda or meio == direita:
            return False
        valor_meio = _amostrar(funcao, np.array([meio]))[0]
        if not np.isfinite(valor_meio):
            return True
        if valor_meio == 0:
            return False
        if np.signbit(valor_meio) == np.signbit(valor_esquerdo):
            esquerda, valor_esquerdo = meio, valor_meio
            pico_esquerdo = max(pico_esquerdo, abs(valor_meio))
        else:
            direita, valor_direito = meio, valor_meio
            pico_direito = max(pico_direito, abs(valor_meio))
    # Uma transição contínua muito estreita também cresce antes de voltar a
    # zero; cortar apenas quando os dois lados ainda crescem ao refinar.
    return (
        abs(valor_esquerdo) > 2 * referencia
        and abs(valor_direito) > 2 * referencia
        and abs(valor_esquerdo) >= 0.8 * pico_esquerdo
        and abs(valor_direito) >= 0.8 * pico_direito
    )


def _trechos_numericos(funcao, pontos, sondar_polos=False):
    if not len(pontos):
        return []
    valores = _amostrar(funcao, pontos)
    meios = (pontos[:-1] + pontos[1:]) / 2
    valores_meios = _amostrar(funcao, meios)
    trechos = []
    inicio = None
    for indice, valor in enumerate(valores):
        if not np.isfinite(valor):
            if inicio is not None:
                trechos.append((pontos[inicio:indice], valores[inicio:indice]))
                inicio = None
        elif inicio is None:
            inicio = indice
        elif (
            not np.isfinite(valores_meios[indice - 1])
            or (
                sondar_polos
                and _polo_suspeito(
                    funcao, pontos[indice - 1], pontos[indice],
                    valores[indice - 1], valor,
                )
            )
        ):
            trechos.append((pontos[inicio:indice], valores[inicio:indice]))
            inicio = indice
    if inicio is not None:
        trechos.append((pontos[inicio:], valores[inicio:]))
    return trechos


def preparar_dados_grafico(resultado, faixa=None):
    """Amostra a função original sem criar recursos Matplotlib."""
    if faixa is None:
        faixa = faixa_definida(resultado)
    esquerda, direita = map(float, faixa)
    if not np.isfinite([esquerda, direita]).all() or esquerda >= direita:
        raise ValueError("A faixa do gráfico deve ser finita e crescente.")

    intervalos, analise_completa = _intervalos_continuos(
        resultado.expressao, esquerda, direita
    )
    malhas = [np.linspace(esquerda, direita, 401)]
    limites = None
    if resultado.limite_inferior is not None:
        limites = _extremos_definidos(resultado)
        if limites[0] < limites[1]:
            malhas.append(np.linspace(*limites, 401))
    for intervalo in intervalos:
        malhas.append(np.linspace(
            float(intervalo.start), float(intervalo.end), 401
        ))
    malha = np.unique(np.concatenate(malhas))
    funcao = sp.lambdify(
        sp.Symbol("x"), resultado.expressao, modules="numpy"
    )
    trechos = []
    for intervalo in intervalos:
        inicio, fim = float(intervalo.start), float(intervalo.end)
        dentro = (
            (malha > inicio if intervalo.left_open else malha >= inicio)
            & (malha < fim if intervalo.right_open else malha <= fim)
        )
        trechos.extend(_trechos_numericos(
            funcao, malha[dentro], sondar_polos=not analise_completa
        ))
    if not any(len(pontos) for pontos, _valores in trechos):
        raise ValueError("Não há valores reais finitos nessa faixa.")
    return DadosGrafico(
        esquerda, direita, tuple(trechos), limites,
        resultado.limite_inferior is not None
        and resultado.limite_inferior > resultado.limite_superior,
    )


def montar_figura(dados):
    """Monta a figura Matplotlib a partir de amostras já preparadas."""
    figura = Figure(figsize=(5, 3), dpi=100)
    try:
        eixo = figura.add_subplot(111)
        trechos = dados.trechos
        for pontos, valores in trechos:
            eixo.plot(pontos, valores)
        eixo.set_xlim(dados.esquerda, dados.direita)
        limites = dados.limites
        if limites is not None:
            limite_esquerdo, limite_direito = limites
            if limite_esquerdo < limite_direito:
                partes_integracao = []
                for pontos, valores in trechos:
                    dentro = (pontos >= limite_esquerdo) & (
                        pontos <= limite_direito
                    )
                    x_integracao = pontos[dentro]
                    y_integracao = valores[dentro]
                    if len(x_integracao) < 2:
                        continue
                    partes_integracao.append(x_integracao)
                    for mascara, cor in (
                        (y_integracao > 0, "tab:blue"),
                        (y_integracao < 0, "tab:orange"),
                    ):
                        if mascara.any():
                            eixo.fill_between(
                                x_integracao, y_integracao, 0,
                                where=mascara, interpolate=True,
                                color=cor, alpha=0.35,
                            )
                if (
                    len(partes_integracao) != 1
                    or partes_integracao[0][0] > limite_esquerdo
                    or partes_integracao[0][-1] < limite_direito
                ):
                    eixo.text(
                        0.02, 0.02,
                        "Sombreado aproximado: trechos finitos",
                        transform=eixo.transAxes, fontsize=8,
                        color="dimgray", va="bottom",
                    )
            if dados.orientacao_invertida:
                eixo.set_title(
                    "Integração: direita para a esquerda", fontsize=10
                )
        eixo.set_xlabel("x")
        eixo.set_ylabel("f(x)")
        eixo.grid(True)
        figura.tight_layout()
        return figura
    except Exception:
        figura.clear()
        raise


def criar_figura(resultado, faixa=None):
    """Desenha a função original sem depender de Tkinter."""
    return montar_figura(preparar_dados_grafico(resultado, faixa))
