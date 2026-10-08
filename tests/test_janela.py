import os
import runpy
import subprocess
import sys
from queue import Queue
from threading import Event, get_ident
from types import SimpleNamespace

import pytest
import sympy as sp


@pytest.mark.parametrize("modulo", ["main", "src.ui.janela"])
def test_importar_modulo_nao_abre_janela_nem_executa_exemplos(
    modulo, tmp_path
):
    ambiente = os.environ.copy()
    ambiente.pop("DISPLAY", None)
    ambiente["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    ambiente["XDG_CACHE_HOME"] = str(tmp_path / "cache")

    processo = subprocess.run(
        [sys.executable, "-c", f"import {modulo}"],
        capture_output=True,
        text=True,
        env=ambiente,
        check=False,
    )

    assert processo.returncode == 0
    assert processo.stdout == ""
    aviso_fontes = (
        "Matplotlib is building the font cache; this may take a moment.\n"
    )
    assert processo.stderr.replace(aviso_fontes, "") == ""


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
        self.destruido = True
        for filho in self.filhos:
            filho.destroy()

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
    def __init__(self, *argumentos, **opcoes):
        super().__init__(*argumentos, **opcoes)
        self.agendados = []
        self.protocolos = {}

    def after(self, _atraso, funcao):
        identificador = object()
        self.agendados.append((identificador, funcao))
        return identificador

    def after_cancel(self, identificador):
        self.agendados = [
            agendado for agendado in self.agendados
            if agendado[0] is not identificador
        ]

    def executar_agendado(self):
        if self.agendados:
            _identificador, funcao = self.agendados.pop(0)
            funcao()

    def protocol(self, nome, funcao):
        self.protocolos[nome] = funcao

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
        raiz = self
        while raiz.parent is not None:
            raiz = raiz.parent
        raiz.executar_agendado()


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


class DespachanteFalso:
    automatico = True
    instancia = None

    def __init__(self):
        self.respostas = Queue()
        self.versoes = {"calculo": 0, "grafico": 0}
        self.tarefas = []
        self.encerrado = False
        type(self).instancia = self

    def invalidar(self, *tipos):
        for tipo in tipos:
            self.versoes[tipo] += 1
        self.tarefas = [
            tarefa for tarefa in self.tarefas
            if tarefa[1] == self.versoes[tarefa[0]]
        ]

    def enviar(self, tipo, operacao, argumentos, invalidar=()):
        self.invalidar(*invalidar, tipo)
        identificador = self.versoes[tipo]
        self.tarefas.append((tipo, identificador, operacao, argumentos))
        if self.automatico:
            self.executar_proxima()
        return identificador

    def executar_proxima(self):
        self.concluir(self.tarefas.pop(0))

    def concluir(self, tarefa):
        tipo, identificador, operacao, argumentos = tarefa
        try:
            resposta = operacao(*argumentos)
            erro = None
        except (ValueError, TypeError) as excecao:
            resposta = None
            erro = (str(excecao), getattr(excecao, "campo_entrada", None))
        except Exception:
            resposta = None
            erro = (None, None)
        self.respostas.put((tipo, identificador, resposta, erro))

    def atual(self, tipo, identificador):
        return not self.encerrado and self.versoes[tipo] == identificador

    def tem_trabalho(self):
        return bool(self.tarefas or not self.respostas.empty())

    def fechar(self):
        self.encerrado = True
        self.tarefas.clear()


class DespachanteControlado(DespachanteFalso):
    automatico = False


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


def estado_calculo(raiz):
    return encontrar_nome(raiz, "estado_calculo").opcoes["text"]


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


def montar_janela_falsa(monkeypatch, classe_despachante):
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
    monkeypatch.setattr(janela, "_Despachante", classe_despachante)
    raiz = RaizFalsa()
    raiz.visivel = True
    janela.criar_janela(raiz)
    raiz.despachante = classe_despachante.instancia
    return raiz


@pytest.fixture
def janela_sem_tela(monkeypatch):
    return montar_janela_falsa(monkeypatch, DespachanteFalso)


@pytest.fixture
def janela_controlada(monkeypatch):
    return montar_janela_falsa(monkeypatch, DespachanteControlado)


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


def test_faixa_indefinida_pode_ser_atualizada_sem_recalcular(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela

    graficos = []
    monkeypatch.setattr(janela, "_renderizar_resultado", lambda *_: WidgetFalso())
    monkeypatch.setattr(
        janela, "_incorporar_grafico",
        lambda _area, figura: graficos.append(figura) or WidgetFalso(),
    )
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()

    assert graficos[-1].axes[0].get_xlim() == (-10, 10)
    encontrar_nome(janela_sem_tela, "faixa_esquerda").insert(0, "-2")
    encontrar_nome(janela_sem_tela, "faixa_direita").insert(0, "2")
    assert texto_visivel(janela_sem_tela, "x**3/3 + C")
    botao(janela_sem_tela, "Atualizar gráfico").invoke()

    assert graficos[-1].axes[0].get_xlim() == (-2, 2)
    assert len(graficos) == 2


def test_faixa_invalida_preserva_resultado_e_copia(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela

    monkeypatch.setattr(
        janela, "_renderizar_resultado", lambda *_: WidgetFalso()
    )
    monkeypatch.setattr(
        janela, "_incorporar_grafico", lambda *_: WidgetFalso()
    )
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()
    encontrar_nome(janela_sem_tela, "faixa_esquerda").insert(0, "3")
    encontrar_nome(janela_sem_tela, "faixa_direita").insert(0, "2")
    botao(janela_sem_tela, "Atualizar gráfico").invoke()
    botao(janela_sem_tela, "Copiar").invoke()

    assert encontrar_nome(janela_sem_tela, "erro_faixa").opcoes["text"]
    assert texto_visivel(janela_sem_tela, "x**3/3 + C")
    assert janela_sem_tela.clipboard_get() == "x**3/3 + C"


def test_atualizar_faixa_nao_repete_calculo_da_integral(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela

    original = janela.processar_integral_indefinida
    chamadas = []

    def processar(texto):
        chamadas.append(texto)
        return original(texto)

    monkeypatch.setattr(janela, "processar_integral_indefinida", processar)
    monkeypatch.setattr(janela, "_renderizar_resultado", lambda *_: WidgetFalso())
    monkeypatch.setattr(janela, "_incorporar_grafico", lambda *_: WidgetFalso())
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()
    encontrar_nome(janela_sem_tela, "faixa_esquerda").insert(0, "-2")
    botao(janela_sem_tela, "Atualizar gráfico").invoke()

    assert chamadas == ["x^2"]


def test_grafico_definido_usa_limites_e_oculta_faixa_editavel(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela

    figuras = []
    monkeypatch.setattr(janela, "_renderizar_resultado", lambda *_: WidgetFalso())
    monkeypatch.setattr(
        janela, "_incorporar_grafico",
        lambda _area, figura: figuras.append(figura) or WidgetFalso(),
    )
    encontrar_texto(janela_sem_tela, "Definida").invoke()
    assert not visivel(encontrar_nome(janela_sem_tela, "faixa_esquerda"))
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    entrada_do_campo(janela_sem_tela, "Limite inferior").insert(0, "2")
    entrada_do_campo(janela_sem_tela, "Limite superior").insert(0, "0")
    botao(janela_sem_tela, "Calcular").invoke()

    assert figuras[-1].axes[0].get_xlim() == (-0.2, 2.2)
    assert texto_visivel(janela_sem_tela, "-8/3")


def test_falha_grafica_preserva_resultado_mathtext_e_copia(
    janela_sem_tela, monkeypatch
):
    from matplotlib.figure import Figure
    from src.ui import janela

    formulas = []
    figura = Figure()
    figura.add_subplot(111)
    monkeypatch.setattr(
        janela, "_renderizar_resultado",
        lambda _area, formula: formulas.append(formula) or WidgetFalso(),
    )
    monkeypatch.setattr(janela, "montar_figura", lambda *_: figura)
    monkeypatch.setattr(
        janela, "_incorporar_grafico",
        lambda *_: (_ for _ in ()).throw(RuntimeError("canvas falhou")),
    )
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()
    botao(janela_sem_tela, "Copiar").invoke()

    assert formulas == [r"$\frac{x^{3}}{3} + C$"]
    assert texto_visivel(janela_sem_tela, "x**3/3 + C")
    assert janela_sem_tela.clipboard_get() == "x**3/3 + C"
    assert encontrar_nome(janela_sem_tela, "erro_faixa").opcoes["text"]
    assert not figura.axes


def test_editar_entrada_descarta_grafico_anterior(janela_sem_tela, monkeypatch):
    from src.ui import janela

    criados = []

    def incorporar(_area, figura):
        widget = WidgetFalso()
        criados.append((figura, widget))
        return widget

    monkeypatch.setattr(janela, "_renderizar_resultado", lambda *_: WidgetFalso())
    monkeypatch.setattr(janela, "_incorporar_grafico", incorporar)
    entrada = entrada_do_campo(janela_sem_tela, "Expressão")
    entrada.insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()
    figura, widget = criados[-1]

    entrada.insert(0, "x")

    assert widget.destruido
    assert not figura.axes


def test_recalculos_consecutivos_descartam_canvases_e_figuras_anteriores(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela

    graficos = []

    def incorporar(_area, figura):
        canvas = WidgetFalso()
        graficos.append((figura, canvas))
        return canvas

    monkeypatch.setattr(janela, "_renderizar_resultado", lambda *_: WidgetFalso())
    monkeypatch.setattr(janela, "_incorporar_grafico", incorporar)
    entrada = entrada_do_campo(janela_sem_tela, "Expressão")
    entrada.insert(0, "x^2")

    for quantidade in range(1, 5):
        botao(janela_sem_tela, "Calcular").invoke()
        assert len(graficos) == quantidade
        assert all(
            getattr(canvas, "destruido", False) and not figura.axes
            for figura, canvas in graficos[:-1]
        )
        figura_atual, canvas_atual = graficos[-1]
        assert not getattr(canvas_atual, "destruido", False)
        assert figura_atual.axes

    entrada.insert(0, "x")
    assert all(
        canvas.destruido and not figura.axes
        for figura, canvas in graficos
    )


def test_falha_de_amostragem_nao_apaga_resultado(janela_sem_tela, monkeypatch):
    from src.ui import janela

    monkeypatch.setattr(janela, "_renderizar_resultado", lambda *_: WidgetFalso())
    monkeypatch.setattr(
        janela, "preparar_dados_grafico",
        lambda *_: (_ for _ in ()).throw(RuntimeError("amostragem falhou")),
    )
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "x^2")
    botao(janela_sem_tela, "Calcular").invoke()
    botao(janela_sem_tela, "Copiar").invoke()

    assert texto_visivel(janela_sem_tela, "x**3/3 + C")
    assert janela_sem_tela.clipboard_get() == "x**3/3 + C"
    assert encontrar_nome(janela_sem_tela, "erro_faixa").opcoes["text"]


def test_faixa_sem_dominio_real_preserva_resultado_e_copia(
    janela_sem_tela, monkeypatch
):
    from src.ui import janela

    monkeypatch.setattr(janela, "_renderizar_resultado", lambda *_: WidgetFalso())
    monkeypatch.setattr(janela, "_incorporar_grafico", lambda *_: WidgetFalso())
    entrada_do_campo(janela_sem_tela, "Expressão").insert(0, "ln(x)")
    botao(janela_sem_tela, "Calcular").invoke()
    texto = resultado_textual(janela_sem_tela).get("1.0", "end-1c")

    encontrar_nome(janela_sem_tela, "faixa_esquerda").insert(0, "-10")
    encontrar_nome(janela_sem_tela, "faixa_direita").insert(0, "-1")
    botao(janela_sem_tela, "Atualizar gráfico").invoke()
    botao(janela_sem_tela, "Copiar").invoke()

    assert encontrar_nome(janela_sem_tela, "erro_faixa").opcoes["text"]
    assert resultado_textual(janela_sem_tela).get("1.0", "end-1c") == texto
    assert janela_sem_tela.clipboard_get() == texto


def test_falha_ao_desenhar_canvas_descarta_widget_e_figura(monkeypatch):
    from matplotlib.backends import backend_tkagg
    from matplotlib.figure import Figure
    from src.ui.janela import _incorporar_grafico

    widgets = []

    class CanvasFalho:
        def __init__(self, _figura, master):
            self.widget = WidgetFalso(master)
            widgets.append(self.widget)

        def get_tk_widget(self):
            return self.widget

        def draw(self):
            raise RuntimeError("falha ao desenhar")

    from src.ui import janela

    monkeypatch.setattr(backend_tkagg, "FigureCanvasTkAgg", CanvasFalho)
    monkeypatch.setattr(janela.tk, "Frame", WidgetFalso)
    figura = Figure()
    figura.add_subplot(111)

    with pytest.raises(RuntimeError, match="falha ao desenhar"):
        _incorporar_grafico(WidgetFalso(), figura)

    assert widgets[0].destruido
    assert not figura.axes


def test_falha_ao_criar_canvas_descarta_filho_parcial(monkeypatch):
    from matplotlib.backends import backend_tkagg
    from matplotlib.figure import Figure
    from src.ui import janela

    filhos = []

    class CanvasFalho:
        def __init__(self, _figura, master):
            filhos.append(WidgetFalso(master))
            raise RuntimeError("falha ao criar canvas")

    monkeypatch.setattr(backend_tkagg, "FigureCanvasTkAgg", CanvasFalho)
    monkeypatch.setattr(janela.tk, "Frame", WidgetFalso)
    figura = Figure()
    figura.add_subplot(111)

    with pytest.raises(RuntimeError, match="falha ao criar canvas"):
        janela._incorporar_grafico(WidgetFalso(), figura)

    assert filhos[0].destruido
    assert not figura.axes


def test_falha_ao_desenhar_mathtext_descarta_figura_e_widget(monkeypatch):
    from matplotlib import figure as modulo_figura
    from matplotlib.backends import backend_tkagg
    from src.ui import janela

    figuras = []
    recipientes = []
    figura_original = modulo_figura.Figure

    def criar_figura(*argumentos, **opcoes):
        figura = figura_original(*argumentos, **opcoes)
        figuras.append(figura)
        return figura

    class CanvasFalho:
        def __init__(self, _figura, master):
            self.widget = WidgetFalso(master)
            recipientes.append(master)

        def get_tk_widget(self):
            return self.widget

        def draw(self):
            raise RuntimeError("falha do MathText")

    monkeypatch.setattr(modulo_figura, "Figure", criar_figura)
    monkeypatch.setattr(backend_tkagg, "FigureCanvasTkAgg", CanvasFalho)
    monkeypatch.setattr(janela.tk, "Frame", WidgetFalso)

    with pytest.raises(RuntimeError, match="falha do MathText"):
        janela._renderizar_resultado(WidgetFalso(), "$x$")

    assert recipientes[0].destruido
    assert not figuras[0].texts


def test_falha_ao_criar_recipiente_descarta_figuras(monkeypatch):
    from matplotlib import figure as modulo_figura
    from src.ui import janela

    figuras = []
    figura_original = modulo_figura.Figure

    class FiguraRastreada(figura_original):
        def __init__(self, *argumentos, **opcoes):
            super().__init__(*argumentos, **opcoes)
            self.descartada = False
            figuras.append(self)

        def clear(self, *argumentos, **opcoes):
            super().clear(*argumentos, **opcoes)
            self.descartada = True

    def falhar_ao_criar_recipiente(*_argumentos, **_opcoes):
        raise RuntimeError("falha do contêiner")

    monkeypatch.setattr(modulo_figura, "Figure", FiguraRastreada)
    monkeypatch.setattr(janela.tk, "Frame", falhar_ao_criar_recipiente)

    with pytest.raises(RuntimeError, match="falha do contêiner"):
        janela._renderizar_resultado(WidgetFalso(), "$x$")
    figura_grafico = figura_original()
    figura_grafico.add_subplot(111)
    with pytest.raises(RuntimeError, match="falha do contêiner"):
        janela._incorporar_grafico(WidgetFalso(), figura_grafico)

    assert figuras[0].descartada
    assert not figura_grafico.axes


def test_calculo_pendente_mostra_progresso_e_entrega_resultado(
    janela_controlada, monkeypatch
):
    from src.ui import janela

    monkeypatch.setattr(
        janela, "_renderizar_resultado", lambda *_: WidgetFalso()
    )
    monkeypatch.setattr(
        janela, "_incorporar_grafico", lambda *_: WidgetFalso()
    )
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")

    botao(janela_controlada, "Calcular").invoke()

    assert estado_calculo(janela_controlada) == "Calculando..."
    assert resultado_textual(janela_controlada).get("1.0", "end-1c") == ""
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()

    assert texto_visivel(janela_controlada, "x**3/3 + C")
    assert estado_calculo(janela_controlada)
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()

    assert estado_calculo(janela_controlada) == ""
    botao(janela_controlada, "Copiar").invoke()
    assert janela_controlada.clipboard_get() == "x**3/3 + C"


def test_consulta_da_fila_ativa_somente_enquanto_ha_trabalho(
    janela_controlada
):
    assert janela_controlada.agendados == []
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")
    assert janela_controlada.agendados == []

    botao(janela_controlada, "Calcular").invoke()
    assert len(janela_controlada.agendados) == 1
    assert estado_calculo(janela_controlada) == "Calculando..."

    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    assert len(janela_controlada.agendados) == 1

    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    assert janela_controlada.agendados == []
    assert estado_calculo(janela_controlada) == ""

    botao(janela_controlada, "Calcular").invoke()
    assert len(janela_controlada.agendados) == 1
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    assert janela_controlada.agendados == []


def test_fechar_com_consulta_ativa_cancela_agendamento(janela_controlada):
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    assert len(janela_controlada.agendados) == 1

    janela_controlada.protocolos["WM_DELETE_WINDOW"]()

    assert janela_controlada.agendados == []
    assert janela_controlada.destruido


def test_edicao_cancela_consulta_de_tarefa_descartada(janela_controlada):
    entrada = entrada_do_campo(janela_controlada, "Expressão")
    entrada.insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    assert len(janela_controlada.agendados) == 1

    entrada.insert(0, "x")

    assert janela_controlada.agendados == []
    assert estado_calculo(janela_controlada) == ""

    botao(janela_controlada, "Calcular").invoke()
    assert len(janela_controlada.agendados) == 1


def test_edicao_descarta_resposta_de_calculo_em_andamento(janela_controlada):
    entrada = entrada_do_campo(janela_controlada, "Expressão")
    entrada.insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    tarefa_antiga = janela_controlada.despachante.tarefas.pop(0)

    entrada.insert(0, "x")
    janela_controlada.despachante.concluir(tarefa_antiga)
    janela_controlada.executar_agendado()

    assert estado_calculo(janela_controlada) == ""
    assert resultado_textual(janela_controlada).get("1.0", "end-1c") == ""
    assert botao(janela_controlada, "Copiar").opcoes["state"] == "disabled"


def test_erro_assincrono_preserva_entrada_e_remove_progresso(
    janela_controlada
):
    entrada = entrada_do_campo(janela_controlada, "Expressão")
    entrada.insert(0, "x +")
    botao(janela_controlada, "Calcular").invoke()
    assert estado_calculo(janela_controlada)

    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()

    assert entrada.get() == "x +"
    assert erro_do_campo(janela_controlada, "Expressão").opcoes["text"]
    assert estado_calculo(janela_controlada) == ""


def test_troca_de_modo_invalida_calculo_pendente(janela_controlada):
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    tarefa_antiga = janela_controlada.despachante.tarefas.pop(0)
    encontrar_texto(janela_controlada, "Definida").invoke()

    janela_controlada.despachante.concluir(tarefa_antiga)
    janela_controlada.executar_agendado()

    assert resultado_textual(janela_controlada).get("1.0", "end-1c") == ""
    assert estado_calculo(janela_controlada) == ""
    assert visivel(entrada_do_campo(janela_controlada, "Limite inferior"))


def test_requisicao_mais_recente_vence_conclusao_fora_de_ordem(
    janela_controlada, monkeypatch
):
    from src.ui import janela

    monkeypatch.setattr(
        janela, "_renderizar_resultado", lambda *_: WidgetFalso()
    )
    monkeypatch.setattr(
        janela, "_incorporar_grafico", lambda *_: WidgetFalso()
    )
    entrada = entrada_do_campo(janela_controlada, "Expressão")
    entrada.insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    antiga = janela_controlada.despachante.tarefas.pop(0)
    entrada.insert(0, "x")
    botao(janela_controlada, "Calcular").invoke()

    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    janela_controlada.despachante.concluir(antiga)
    janela_controlada.executar_agendado()

    assert texto_visivel(janela_controlada, "x**2/2 + C")
    assert not texto_visivel(janela_controlada, "x**3/3 + C")
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    assert estado_calculo(janela_controlada) == ""


def test_faixa_descarta_grafico_antigo_sem_recalcular(
    janela_controlada, monkeypatch
):
    from src.ui import janela

    figuras = []
    monkeypatch.setattr(
        janela, "_renderizar_resultado", lambda *_: WidgetFalso()
    )
    monkeypatch.setattr(
        janela, "_incorporar_grafico",
        lambda _area, figura: figuras.append(figura) or WidgetFalso(),
    )
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    resultado_original = resultado_textual(janela_controlada).get(
        "1.0", "end-1c"
    )

    encontrar_nome(janela_controlada, "faixa_esquerda").insert(0, "-2")
    botao(janela_controlada, "Atualizar gráfico").invoke()
    antiga = janela_controlada.despachante.tarefas.pop(0)
    encontrar_nome(janela_controlada, "faixa_direita").insert(0, "2")
    botao(janela_controlada, "Atualizar gráfico").invoke()
    janela_controlada.despachante.concluir(antiga)
    janela_controlada.executar_agendado()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()

    assert len(figuras) == 2
    assert figuras[-1].axes[0].get_xlim() == (-2, 2)
    assert resultado_textual(janela_controlada).get(
        "1.0", "end-1c"
    ) == resultado_original
    assert estado_calculo(janela_controlada) == ""


def test_fechar_durante_calculo_descarta_saida_e_recursos(
    janela_controlada, monkeypatch
):
    from matplotlib.figure import Figure
    from src.ui import janela

    formulas = []
    graficos = []

    def renderizar(*_argumentos):
        widget = WidgetFalso()
        figura = Figure()
        figura.add_subplot(111)
        widget._figura_resultado = figura
        formulas.append((widget, figura))
        return widget

    def incorporar(_area, figura):
        widget = WidgetFalso()
        graficos.append((widget, figura))
        return widget

    monkeypatch.setattr(janela, "_renderizar_resultado", renderizar)
    monkeypatch.setattr(janela, "_incorporar_grafico", incorporar)
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    botao(janela_controlada, "Calcular").invoke()
    tarefa_em_andamento = janela_controlada.despachante.tarefas.pop(0)

    janela_controlada.protocolos["WM_DELETE_WINDOW"]()
    janela_controlada.despachante.concluir(tarefa_em_andamento)

    assert janela_controlada.destruido
    assert janela_controlada.agendados == []
    assert janela_controlada.despachante.encerrado
    assert all(widget.destruido and not figura.axes
               for widget, figura in formulas + graficos)


def test_despachante_descarta_trabalhos_pendentes_obsoletos():
    from src.ui.janela import _Despachante

    iniciados = Queue()
    liberar = Event()
    despachante = _Despachante()

    def tarefa(identificador):
        iniciados.put(identificador)
        if identificador in (1, 2):
            assert liberar.wait(timeout=10)
        return identificador

    try:
        despachante.enviar("calculo", tarefa, (1,))
        assert iniciados.get(timeout=10) == 1
        despachante.enviar("calculo", tarefa, (2,))
        assert iniciados.get(timeout=10) == 2
        for identificador in (3, 4, 5):
            despachante.enviar("calculo", tarefa, (identificador,))
        liberar.set()

        assert iniciados.get(timeout=10) == 5
        respostas = [despachante.respostas.get(timeout=10) for _ in range(3)]
        assert all(erro is None for _tipo, _id, _resposta, erro in respostas)
        assert despachante.atual("calculo", 5)
        assert iniciados.empty()
    finally:
        liberar.set()
        despachante.fechar()


@pytest.mark.parametrize("tipo", ["calculo", "grafico"])
def test_despachante_invalida_resposta_de_trabalho_em_execucao(tipo):
    from src.ui.janela import _Despachante

    iniciou = Event()
    liberar = Event()
    despachante = _Despachante()
    assert not despachante.tem_trabalho()

    def tarefa():
        iniciou.set()
        assert liberar.wait(timeout=10)
        return "resultado antigo"

    try:
        identificador = despachante.enviar(tipo, tarefa, ())
        assert iniciou.wait(timeout=10)
        assert despachante.tem_trabalho()
        despachante.invalidar(tipo)
        liberar.set()

        resposta = despachante.respostas.get(timeout=10)
        assert resposta == (tipo, identificador, "resultado antigo", None)
        assert not despachante.atual(tipo, identificador)
    finally:
        liberar.set()
        despachante.fechar()


def test_worker_real_nao_acessa_tk_e_eventos_continuam(monkeypatch):
    from src.ui import janela

    identificador_principal = get_ident()
    iniciou = Event()
    liberar = Event()
    processar = janela.processar_integral_indefinida
    obter_variavel = VariavelFalsa.get
    configurar_widget = WidgetFalso.config

    def obter_na_thread_principal(variavel):
        assert get_ident() == identificador_principal
        return obter_variavel(variavel)

    def configurar_na_thread_principal(widget, **opcoes):
        assert get_ident() == identificador_principal
        return configurar_widget(widget, **opcoes)

    def calculo_controlado(expressao):
        assert get_ident() != identificador_principal
        iniciou.set()
        assert liberar.wait(timeout=10)
        return processar(expressao)

    monkeypatch.setattr(VariavelFalsa, "get", obter_na_thread_principal)
    monkeypatch.setattr(WidgetFalso, "config", configurar_na_thread_principal)
    monkeypatch.setattr(
        janela, "processar_integral_indefinida", calculo_controlado
    )

    class DespachanteRealRastreado(janela._Despachante):
        instancia = None

        def __init__(self):
            super().__init__()
            type(self).instancia = self

    raiz = montar_janela_falsa(monkeypatch, DespachanteRealRastreado)
    monkeypatch.setattr(
        janela, "_renderizar_resultado", lambda *_: WidgetFalso()
    )
    monkeypatch.setattr(
        janela, "_incorporar_grafico", lambda *_: WidgetFalso()
    )
    try:
        entrada_do_campo(raiz, "Expressão").insert(0, "x^2")
        botao(raiz, "Calcular").invoke()
        assert iniciou.wait(timeout=10)
        raiz.executar_agendado()
        assert encontrar_nome(raiz, "estado_calculo").opcoes["text"] == (
            "Calculando..."
        )
        liberar.set()
        resposta = raiz.despachante.respostas.get(timeout=10)
        raiz.despachante.respostas.put(resposta)
        raiz.executar_agendado()
        assert texto_visivel(raiz, "x**3/3 + C")
    finally:
        liberar.set()
        raiz.protocolos["WM_DELETE_WINDOW"]()


def test_falha_grafica_assincrona_preserva_resultado_e_copia(
    janela_controlada, monkeypatch
):
    from src.ui import janela

    monkeypatch.setattr(
        janela, "_renderizar_resultado", lambda *_: WidgetFalso()
    )
    monkeypatch.setattr(
        janela, "preparar_dados_grafico",
        lambda *_: (_ for _ in ()).throw(
            ValueError("faixa sem domínio real")
        ),
    )
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    botao(janela_controlada, "Copiar").invoke()

    assert resultado_textual(janela_controlada).get(
        "1.0", "end-1c"
    ) == "x**3/3 + C"
    assert janela_controlada.clipboard_get() == "x**3/3 + C"
    assert "faixa sem domínio real" in encontrar_nome(
        janela_controlada, "erro_faixa"
    ).opcoes["text"]
    assert estado_calculo(janela_controlada) == ""


def test_fechar_descarta_figuras_ainda_visiveis(
    janela_controlada, monkeypatch
):
    from matplotlib.figure import Figure
    from src.ui import janela

    recursos = []

    def renderizar(*_argumentos):
        widget = WidgetFalso()
        figura = Figure()
        figura.add_subplot(111)
        widget._figura_resultado = figura
        recursos.append((widget, figura))
        return widget

    def incorporar(_area, figura):
        widget = WidgetFalso()
        recursos.append((widget, figura))
        return widget

    monkeypatch.setattr(janela, "_renderizar_resultado", renderizar)
    monkeypatch.setattr(janela, "_incorporar_grafico", incorporar)
    entrada_do_campo(janela_controlada, "Expressão").insert(0, "x^2")
    botao(janela_controlada, "Calcular").invoke()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    janela_controlada.despachante.executar_proxima()
    janela_controlada.executar_agendado()
    assert all(figura.axes for _widget, figura in recursos)

    janela_controlada.protocolos["WM_DELETE_WINDOW"]()

    assert all(widget.destruido and not figura.axes
               for widget, figura in recursos)
    assert janela_controlada.agendados == []
