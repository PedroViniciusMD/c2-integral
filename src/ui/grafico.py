"""Prepara a visualização numérica da função de uma integral."""

import numpy as np
import sympy as sp
from matplotlib.figure import Figure

from src.core.parser import parse_limite
from src.core.validation import validar_limite


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
    esquerda, direita = sorted((
        float(resultado.limite_inferior),
        float(resultado.limite_superior),
    ))
    if not np.isfinite([esquerda, direita]).all():
        raise ValueError("Os limites não cabem na faixa do gráfico.")
    margem = (direita - esquerda) * 0.1 if esquerda != direita else 1.0
    return esquerda - margem, direita + margem


def criar_figura(resultado, faixa=None):
    """Desenha a função original em uma figura sem dependência de Tkinter."""
    if faixa is None:
        faixa = faixa_definida(resultado)
    esquerda, direita = map(float, faixa)
    if not np.isfinite([esquerda, direita]).all() or esquerda >= direita:
        raise ValueError("A faixa do gráfico deve ser finita e crescente.")

    figura = Figure(figsize=(5, 3), dpi=100)
    try:
        eixo = figura.add_subplot(111)
        amostras_x = np.linspace(esquerda, direita, 401)
        funcao = sp.lambdify(sp.Symbol("x"), resultado.expressao, modules="numpy")
        with np.errstate(all="ignore"):
            valores = np.asarray(funcao(amostras_x), dtype=complex)
            valores = np.broadcast_to(valores, amostras_x.shape)
        amostras_y = np.where(
            np.isreal(valores) & np.isfinite(valores), valores.real, np.nan
        )
        if not np.isfinite(amostras_y).any():
            raise ValueError("Não há valores reais finitos nessa faixa.")
        eixo.plot(amostras_x, amostras_y)
        eixo.set_xlim(esquerda, direita)
        eixo.set_xlabel("x")
        eixo.set_ylabel("f(x)")
        eixo.grid(True)
        figura.tight_layout()
        return figura
    except Exception:
        figura.clear()
        raise
