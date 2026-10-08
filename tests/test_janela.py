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


@pytest.mark.parametrize(
    ("modo", "texto_copia", "formula"),
    [
        ("indefinida", "x**3/3 + C", r"$\frac{x^{3}}{3} + C$"),
        ("definida", "8/3", r"$\frac{8}{3}$"),
    ],
)
def test_resultado_tem_mathtext_e_copia_independentes(
    modo, texto_copia, formula
):
    from matplotlib.mathtext import MathTextParser

    from src.ui.interface import (
        processar_integral_definida,
        processar_integral_indefinida,
    )
    from src.ui.janela import mathtext_resultado, texto_para_copia

    if modo == "definida":
        resultado = processar_integral_definida("x^2", "0", "2")
    else:
        resultado = processar_integral_indefinida("x^2")

    assert texto_para_copia(resultado) == texto_copia
    assert mathtext_resultado(resultado) == formula
    MathTextParser("agg").parse(formula)


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

    def destroy(self):
        self.visivel = False

    def pack(self, **_opcoes):
        self.visivel = True

    def columnconfigure(self, *_args, **_opcoes):
        pass

    def rowconfigure(self, *_args, **_opcoes):
        pass

    def config(self, **opcoes):
        self.opcoes.update(opcoes)

    configure = config

    def bind(self, *_args, **_opcoes):
        pass

    def invoke(self):
        self.opcoes["variable"].set(self.opcoes["value"])
        self.opcoes["command"]()


class RaizFalsa(WidgetFalso):
    def clipboard_clear(self):
        self.area_transferencia = ""

    def clipboard_append(self, texto):
        self.area_transferencia += texto

    def clipboard_get(self):
        return self.area_transferencia

    def title(self, _titulo):
        pass

    def mainloop(self):
        pass


class EntradaFalsa(WidgetFalso):
    def insert(self, _indice, texto):
        variavel = self.opcoes.get("textvariable")
        if variavel is None:
            self.texto = texto
        else:
            variavel.set(texto)

    def get(self):
        variavel = self.opcoes.get("textvariable")
        return self.texto if variavel is None else variavel.get()


class TextoFalso(WidgetFalso):
    def delete(self, _inicio, _fim):
        if self.opcoes.get("state") == "disabled":
            raise AssertionError("O texto deve ser habilitado antes da edição")
        self.texto = ""

    def insert(self, _indice, texto):
        if self.opcoes.get("state") == "disabled":
            raise AssertionError("O texto deve ser habilitado antes da edição")
        self.texto = texto

    def get(self, _inicio, _fim):
        return self.texto

    def yview(self, *_args):
        pass

    def yview_moveto(self, _fracao):
        pass


class BarraRolagemFalsa(WidgetFalso):
    def set(self, *_args):
        pass


class BotaoFalso(WidgetFalso):
    def invoke(self):
        if self.opcoes.get("state") == "disabled":
            return
        self.opcoes["command"]()


class VariavelFalsa:
    def __init__(self, value="", **_opcoes):
        self.valor = value
        self.observadores = []

    def get(self):
        return self.valor

    def set(self, valor):
        self.valor = valor
        for observador in self.observadores:
            observador("", "", "write")

    def trace_add(self, _modo, observador):
        self.observadores.append(observador)


def descendentes(widget):
    for filho in widget.filhos:
        yield filho
        yield from descendentes(filho)


def visivel(widget):
    return widget.visivel and (
        widget.parent is None or visivel(widget.parent)
    )


def encontrar_texto(raiz, texto):
    return next(
        widget for widget in descendentes(raiz)
        if widget.opcoes.get("text") == texto
    )


def encontrar_nome(raiz, nome):
    return next(
        widget for widget in descendentes(raiz)
        if widget.opcoes.get("name") == nome
    )


def resultado_textual(raiz):
    return encontrar_nome(raiz, "resultado_textual")


def entrada_do_campo(raiz, titulo):
    nomes = {
        "Expressão": "entrada_expressao",
        "Limite inferior": "entrada_inferior",
        "Limite superior": "entrada_superior",
    }
    return encontrar_nome(raiz, nomes[titulo])


def botao(raiz, texto):
    return next(
        widget for widget in descendentes(raiz)
        if isinstance(widget, BotaoFalso)
        and widget.opcoes.get("text") == texto
    )


def erro_do_campo(raiz, titulo):
    nomes = {
        "Expressão": "erro_expressao",
        "Limite inferior": "erro_inferior",
        "Limite superior": "erro_superior",
        "Mensagens": "mensagem_geral",
    }
    return encontrar_nome(raiz, nomes[titulo])


def texto_visivel(raiz, texto):
    return any(
        widget.opcoes.get("text") == texto and visivel(widget)
        for widget in descendentes(raiz)
    ) or any(
        isinstance(widget, TextoFalso)
        and widget.get("1.0", "end-1c") == texto
        and visivel(widget)
        for widget in descendentes(raiz)
    )


@pytest.fixture
def janela_sem_tela(monkeypatch):
    from src.ui import janela

    tk_falso = SimpleNamespace(
        Tk=RaizFalsa,
        Frame=WidgetFalso,
        Label=WidgetFalso,
        Entry=EntradaFalsa,
        Text=TextoFalso,
        Scrollbar=BarraRolagemFalsa,
        Button=BotaoFalso,
        Radiobutton=WidgetFalso,
        StringVar=VariavelFalsa,
    )
    monkeypatch.setattr(janela, "tk", tk_falso)
    raiz = RaizFalsa()
    raiz.visivel = True
    janela.criar_janela(raiz)
    return raiz


@pytest.fixture
def renderizacao_falha(monkeypatch):
    from src.ui import janela

    def falhar(_area, _formula):
        raise RuntimeError("falha do canvas")

    monkeypatch.setattr(janela, "_renderizar_resultado", falhar)


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

    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botoes["Definida"].invoke()
    assert visivel(rotulos["Limite inferior"])
    assert visivel(rotulos["Limite superior"])
    assert visivel(entrada_do_campo(janela_sem_tela, "Limite inferior"))
    assert visivel(entrada_do_campo(janela_sem_tela, "Limite superior"))

    entrada_do_campo(janela_sem_tela, "Limite inferior").insert(0, "1/2")
    entrada_do_campo(janela_sem_tela, "Limite superior").insert(0, "pi")
    botoes["Indefinida"].invoke()
    assert visivel(rotulos["Expressão"])
    assert not visivel(rotulos["Limite inferior"])
    assert not visivel(rotulos["Limite superior"])

    botoes["Definida"].invoke()
    assert entrada_do_campo(janela_sem_tela, "Expressão").get() == "x^2"
    assert entrada_do_campo(janela_sem_tela, "Limite inferior").get() == "1/2"
    assert entrada_do_campo(janela_sem_tela, "Limite superior").get() == "pi"


def test_executar_main_inicia_uma_janela(monkeypatch):
    from src.ui import janela

    aberturas = []
    monkeypatch.setattr(janela, "abrir_janela", lambda: aberturas.append(True))

    runpy.run_module("main", run_name="__main__")

    assert aberturas == [True]


def test_calcular_indefinida_mostra_resultado_e_permite_copiar(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela

    formulas = []
    monkeypatch.setattr(
        janela,
        "_renderizar_resultado",
        lambda _area, formula: formulas.append(formula) or WidgetFalso(),
    )
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()
    botao(janela_sem_tela, "Copiar").invoke()

    assert formulas == [r"$\frac{x^{3}}{3} + C$"]
    assert resultado_textual(janela_sem_tela).get("1.0", "end-1c") == (
        "x**3/3 + C"
    )
    assert visivel(resultado_textual(janela_sem_tela))
    assert resultado_textual(janela_sem_tela).opcoes["state"] == "disabled"
    assert janela_sem_tela.clipboard_get() == "x**3/3 + C"


@pytest.mark.parametrize(
    ("expressao", "inferior", "superior", "formula", "copia"),
    [
        ("x^2", "0", "2", r"$\frac{8}{3}$", "8/3"),
        ("1/raiz(x)", "0", "1", "$2$", "2"),
    ],
)
def test_calcular_definida_exibe_resultado_exato_e_copia(
    janela_sem_tela, monkeypatch, expressao, inferior, superior, formula, copia
):
    from src.ui import janela

    formulas = []
    monkeypatch.setattr(
        janela,
        "_renderizar_resultado",
        lambda _area, valor: formulas.append(valor) or WidgetFalso(),
    )
    encontrar_texto(janela_sem_tela, "Definida").invoke()
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, expressao)
    entrada_do_campo(janela_sem_tela, "Limite inferior").insert(0, inferior)
    entrada_do_campo(janela_sem_tela, "Limite superior").insert(0, superior)

    botao(janela_sem_tela, "Calcular").invoke()
    botao(janela_sem_tela, "Copiar").invoke()

    assert formulas == [formula]
    assert janela_sem_tela.clipboard_get() == copia


def test_falha_de_renderizacao_preserva_resultado_textual_e_copia(
    janela_sem_tela, renderizacao_falha
):
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")

    botao(janela_sem_tela, "Calcular").invoke()
    botao(janela_sem_tela, "Copiar").invoke()

    assert texto_visivel(janela_sem_tela, "x**3/3 + C")
    assert janela_sem_tela.clipboard_get() == "x**3/3 + C"


def test_resultado_extenso_permanece_completo_apos_renderizacao(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela
    from src.ui.interface import processar_integral_indefinida

    expressao = "+".join(f"x^{potencia}" for potencia in range(2, 20))
    esperado = janela.texto_para_copia(
        processar_integral_indefinida(expressao)
    )
    formulas = []
    monkeypatch.setattr(
        janela,
        "_renderizar_resultado",
        lambda _area, formula: formulas.append(formula) or WidgetFalso(),
    )
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, expressao)

    botao(janela_sem_tela, "Calcular").invoke()

    campo = resultado_textual(janela_sem_tela)
    assert len(esperado) > 100
    assert len(formulas) == 1
    assert campo.get("1.0", "end-1c") == esperado
    assert campo.opcoes["state"] == "disabled"
    assert campo.opcoes["wrap"] == "char"
    assert visivel(campo)
    assert callable(campo.opcoes["yscrollcommand"])
    assert any(
        isinstance(widget, BarraRolagemFalsa) and visivel(widget)
        for widget in descendentes(janela_sem_tela)
    )


@pytest.mark.parametrize(
    ("modo", "expressao", "inferior", "superior", "campo", "mensagem"),
    [
        ("indefinida", "x^^2", "", "", "Expressão", "Expressão"),
        ("definida", "x", "1+", "2", "Limite inferior", "Limite inválido"),
        ("definida", "x", "0", "1+", "Limite superior", "Limite inválido"),
        ("definida", "raiz(x)", "-1", "1", "Mensagens", "domínio real"),
        ("definida", "1/x", "-1", "1", "Mensagens", "divergente"),
        ("indefinida", "e^(x^x)", "", "", "Mensagens", "não resolvida"),
    ],
)
def test_erro_aparece_no_local_adequado_sem_apagar_entradas(
    janela_sem_tela, modo, expressao, inferior, superior, campo, mensagem
):
    if modo == "definida":
        encontrar_texto(janela_sem_tela, "Definida").invoke()
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, expressao)
    if modo == "definida":
        entrada_do_campo(janela_sem_tela, "Limite inferior").insert(
            0, inferior
        )
        entrada_do_campo(janela_sem_tela, "Limite superior").insert(
            0, superior
        )

    botao(janela_sem_tela, "Calcular").invoke()

    assert mensagem in erro_do_campo(janela_sem_tela, campo).opcoes["text"]
    assert entrada_do_campo(janela_sem_tela, "Expressão").get() == expressao
    if modo == "definida":
        assert (
            entrada_do_campo(janela_sem_tela, "Limite inferior").get()
            == inferior
        )
        assert (
            entrada_do_campo(janela_sem_tela, "Limite superior").get()
            == superior
        )
    assert botao(janela_sem_tela, "Copiar").opcoes["state"] == "disabled"


def test_editar_entrada_ou_mudar_modo_limpa_resultado_anterior(
    janela_sem_tela, renderizacao_falha
):
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()
    assert texto_visivel(janela_sem_tela, "x**3/3 + C")

    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x")
    assert not texto_visivel(janela_sem_tela, "x**3/3 + C")
    assert resultado_textual(janela_sem_tela).get("1.0", "end-1c") == ""
    assert botao(janela_sem_tela, "Copiar").opcoes["state"] == "disabled"

    botao(janela_sem_tela, "Calcular").invoke()
    assert texto_visivel(janela_sem_tela, "x**2/2 + C")
    encontrar_texto(janela_sem_tela, "Definida").invoke()
    assert not texto_visivel(janela_sem_tela, "x**2/2 + C")
    assert resultado_textual(janela_sem_tela).get("1.0", "end-1c") == ""
    assert botao(janela_sem_tela, "Copiar").opcoes["state"] == "disabled"


def test_editar_limite_limpa_resultado_definido(
    janela_sem_tela, renderizacao_falha
):
    encontrar_texto(janela_sem_tela, "Definida").invoke()
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    entrada_do_campo(janela_sem_tela, "Limite inferior").insert(0, "0")
    entrada_do_campo(janela_sem_tela, "Limite superior").insert(0, "2")
    botao(janela_sem_tela, "Calcular").invoke()
    assert texto_visivel(janela_sem_tela, "8/3")

    entrada_do_campo(janela_sem_tela, "Limite superior").insert(0, "3")

    assert not texto_visivel(janela_sem_tela, "8/3")
    assert botao(janela_sem_tela, "Copiar").opcoes["state"] == "disabled"


def test_editar_entrada_limpa_mensagem_de_erro(janela_sem_tela):
    entrada = entrada_do_campo(janela_sem_tela, "Expressão")
    entrada.insert(0, "x^^2")
    botao(janela_sem_tela, "Calcular").invoke()
    assert erro_do_campo(janela_sem_tela, "Expressão").opcoes["text"]

    entrada.insert(0, "x^2")

    assert erro_do_campo(janela_sem_tela, "Expressão").opcoes["text"] == ""
