import os
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest
import sympy as sp


@pytest.mark.parametrize("modulo", ["main", "src.ui.janela"])
def test_importar_modulo_nao_abre_janela_nem_executa_exemplos(modulo):
    ambiente = os.environ.copy()
    ambiente.pop("DISPLAY", None)

    processo = subprocess.run(
        [sys.executable, "-c", f"import {modulo}"],
        capture_output=True,
        text=True,
        env=ambiente,
        check=False,
    )

    assert processo.returncode == 0
    assert processo.stdout == ""
    assert processo.stderr == ""


def test_main_preserva_calculo_python_indefinido():
    from main import calcular

    resultado = calcular("x^2")

    assert sp.simplify(resultado - sp.Symbol("x") ** 3 / 3) == 0


class WidgetFalso:
    def __init__(self, parent=None, **opcoes):
        self.parent = parent
        self.opcoes = opcoes
        self.filhos = []
        self.visivel = False
        self.texto = ""
        if parent is not None:
            parent.filhos.append(self)

    def grid(self, **_opcoes):
        self.visivel = True

    def grid_remove(self):
        self.visivel = False

    def pack(self, **_opcoes):
        self.visivel = True

    def columnconfigure(self, *_args, **_opcoes):
        pass

    def rowconfigure(self, *_args, **_opcoes):
        pass

    def insert(self, _indice, texto):
        self.texto = texto

    def get(self):
        return self.texto

    def invoke(self):
        self.opcoes["variable"].set(self.opcoes["value"])
        self.opcoes["command"]()


class RaizFalsa(WidgetFalso):
    def title(self, _titulo):
        pass

    def mainloop(self):
        pass


class EntradaFalsa(WidgetFalso):
    pass


class VariavelFalsa:
    def __init__(self, value="", **_opcoes):
        self.valor = value

    def get(self):
        return self.valor

    def set(self, valor):
        self.valor = valor


def descendentes(widget):
    for filho in widget.filhos:
        yield filho
        yield from descendentes(filho)


def visivel(widget):
    return widget.visivel and (
        widget.parent is None or visivel(widget.parent)
    )


@pytest.fixture
def janela_sem_tela(monkeypatch):
    from src.ui import janela

    tk_falso = SimpleNamespace(
        Tk=RaizFalsa,
        Frame=WidgetFalso,
        Label=WidgetFalso,
        Entry=EntradaFalsa,
        Radiobutton=WidgetFalso,
        StringVar=VariavelFalsa,
    )
    monkeypatch.setattr(janela, "tk", tk_falso)
    raiz = RaizFalsa()
    raiz.visivel = True
    janela.criar_janela(raiz)
    return raiz


def test_janela_inicia_indefinida_com_expressao_e_sem_limites(janela_sem_tela):
    widgets = list(descendentes(janela_sem_tela))
    rotulos = {
        widget.opcoes.get("text"): widget
        for widget in widgets
        if "text" in widget.opcoes
    }
    botoes = [
        widget for widget in widgets if "value" in widget.opcoes
    ]

    assert visivel(rotulos["Expressão"])
    assert not visivel(rotulos["Limite inferior"])
    assert not visivel(rotulos["Limite superior"])
    assert visivel(rotulos["Mensagens"])
    assert visivel(rotulos["Resultado"])
    assert visivel(rotulos["Gráfico"])
    assert next(
        botao for botao in botoes if botao.opcoes["text"] == "Indefinida"
    ).opcoes["variable"].get() == "indefinida"


def test_alternar_tipo_preserva_expressao_e_limites_digitados(janela_sem_tela):
    widgets = list(descendentes(janela_sem_tela))
    rotulos = {
        widget.opcoes.get("text"): widget
        for widget in widgets
        if "text" in widget.opcoes
    }
    botoes = {
        widget.opcoes["text"]: widget
        for widget in widgets
        if "value" in widget.opcoes
    }

    def entrada_de(rotulo):
        campo = rotulos[rotulo].parent
        return next(
            widget for widget in campo.filhos
            if isinstance(widget, EntradaFalsa)
        )

    entrada_de("Expressão").insert(0, "x^2")
    botoes["Definida"].invoke()
    assert visivel(rotulos["Limite inferior"])
    assert visivel(rotulos["Limite superior"])
    assert visivel(entrada_de("Limite inferior"))
    assert visivel(entrada_de("Limite superior"))

    entrada_de("Limite inferior").insert(0, "1/2")
    entrada_de("Limite superior").insert(0, "pi")
    botoes["Indefinida"].invoke()
    assert visivel(rotulos["Expressão"])
    assert not visivel(rotulos["Limite inferior"])
    assert not visivel(rotulos["Limite superior"])

    botoes["Definida"].invoke()
    assert entrada_de("Expressão").get() == "x^2"
    assert entrada_de("Limite inferior").get() == "1/2"
    assert entrada_de("Limite superior").get() == "pi"


def test_executar_main_inicia_uma_janela(monkeypatch):
    from src.ui import janela

    aberturas = []
    monkeypatch.setattr(janela, "abrir_janela", lambda: aberturas.append(True))

    runpy.run_module("main", run_name="__main__")

    assert aberturas == [True]
