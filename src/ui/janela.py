"""Janela principal da calculadora de integrais."""

import tkinter as tk

import sympy as sp

from src.ui.interface import (
    processar_integral_definida,
    processar_integral_indefinida,
)
from src.ui.grafico import criar_figura, validar_faixa


def texto_para_copia(resultado):
    """Produz texto simples do resultado sem alterar o valor simbólico."""
    texto = sp.sstr(resultado.resultado)
    return texto if resultado.limite_inferior is not None else f"{texto} + C"


def mathtext_resultado(resultado):
    """Produz notação matemática para a área de resultado."""
    expressao = sp.latex(resultado.resultado)
    if resultado.limite_inferior is None:
        expressao += " + C"
    return f"${expressao}$"


def _renderizar_resultado(area, formula):
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    figura = Figure(figsize=(4.5, 1), dpi=100)
    figura.text(0.02, 0.5, formula, ha="left", va="center", fontsize=18)
    canvas = FigureCanvasTkAgg(figura, master=area)
    widget = canvas.get_tk_widget()
    try:
        canvas.draw()
        widget.grid(row=1, column=0, sticky="ew")
    except Exception:
        widget.destroy()
        raise
    return widget


def _incorporar_grafico(area, figura):
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    recipiente = tk.Frame(area)
    try:
        canvas = FigureCanvasTkAgg(figura, master=recipiente)
        widget = canvas.get_tk_widget()
        canvas.draw()
        widget.grid(row=0, column=0, sticky="nsew")
        recipiente.columnconfigure(0, weight=1)
        recipiente.rowconfigure(0, weight=1)
        recipiente.grid(row=0, column=0, sticky="nsew")
        return recipiente
    except Exception:
        try:
            recipiente.destroy()
        finally:
            figura.clear()
        raise


def criar_janela(raiz):
    """Monta a interface inicial em uma raiz Tkinter existente."""
    raiz.title("Calculadora de integrais")
    raiz.columnconfigure(0, weight=1)
    raiz.rowconfigure(0, weight=1)

    conteudo = tk.Frame(raiz)
    conteudo.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
    conteudo.columnconfigure(0, weight=1)
    conteudo.rowconfigure(5, weight=1)

    selecao = tk.Frame(conteudo)
    selecao.grid(row=0, column=0, sticky="w")
    tipo_integral = tk.StringVar(master=raiz, value="indefinida")
    expressao_texto = tk.StringVar(master=raiz)
    inferior_texto = tk.StringVar(master=raiz)
    superior_texto = tk.StringVar(master=raiz)
    faixa_esquerda_texto = tk.StringVar(master=raiz, value="-10")
    faixa_direita_texto = tk.StringVar(master=raiz, value="10")

    campo_expressao = tk.Frame(conteudo)
    campo_expressao.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    campo_expressao.columnconfigure(0, weight=1)
    tk.Label(campo_expressao, text="Expressão").grid(
        row=0, column=0, sticky="w"
    )
    tk.Entry(
        campo_expressao, name="entrada_expressao",
        textvariable=expressao_texto,
    ).grid(
        row=1, column=0, sticky="ew"
    )
    erro_expressao = tk.Label(
        campo_expressao, name="erro_expressao", text="", fg="red"
    )
    erro_expressao.grid(row=2, column=0, sticky="w")

    campos_limites = tk.Frame(conteudo)
    campos_limites.grid(row=2, column=0, sticky="ew", pady=(12, 0))
    campos_limites.columnconfigure(0, weight=1)
    campos_limites.columnconfigure(1, weight=1)

    campo_inferior = tk.Frame(campos_limites)
    campo_inferior.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    campo_inferior.columnconfigure(0, weight=1)
    tk.Label(campo_inferior, text="Limite inferior").grid(
        row=0, column=0, sticky="w"
    )
    tk.Entry(
        campo_inferior, name="entrada_inferior", textvariable=inferior_texto
    ).grid(
        row=1, column=0, sticky="ew"
    )
    erro_inferior = tk.Label(
        campo_inferior, name="erro_inferior", text="", fg="red"
    )
    erro_inferior.grid(row=2, column=0, sticky="w")

    campo_superior = tk.Frame(campos_limites)
    campo_superior.grid(row=0, column=1, sticky="ew")
    campo_superior.columnconfigure(0, weight=1)
    tk.Label(campo_superior, text="Limite superior").grid(
        row=0, column=0, sticky="w"
    )
    tk.Entry(
        campo_superior, name="entrada_superior", textvariable=superior_texto
    ).grid(
        row=1, column=0, sticky="ew"
    )
    erro_superior = tk.Label(
        campo_superior, name="erro_superior", text="", fg="red"
    )
    erro_superior.grid(row=2, column=0, sticky="w")

    def atualizar_campos_limites():
        if tipo_integral.get() == "definida":
            campos_limites.grid()
        else:
            campos_limites.grid_remove()

    atualizar_campos_limites()

    acoes = tk.Frame(conteudo)
    acoes.grid(row=3, column=0, sticky="w", pady=(12, 0))

    saida = tk.Frame(conteudo)
    saida.grid(row=4, column=0, sticky="ew", pady=(16, 0))
    saida.columnconfigure(0, weight=1)
    tk.Label(saida, text="Mensagens").grid(row=0, column=0, sticky="w")
    mensagem_geral = tk.Label(
        saida, name="mensagem_geral", text="", fg="red"
    )
    mensagem_geral.grid(row=1, column=0, sticky="w")
    tk.Label(saida, text="Resultado").grid(row=2, column=0, sticky="w")
    area_resultado = tk.Frame(saida)
    area_resultado.grid(row=3, column=0, sticky="ew")
    area_resultado.columnconfigure(0, weight=1)
    resultado_textual = tk.Text(
        area_resultado,
        name="resultado_textual",
        height=2,
        width=40,
        wrap="char",
        relief="flat",
        state="disabled",
    )
    resultado_textual.grid(row=0, column=0, sticky="ew")
    barra_resultado = tk.Scrollbar(
        area_resultado, orient="vertical", command=resultado_textual.yview
    )
    barra_resultado.grid(row=0, column=1, sticky="ns")
    resultado_textual.config(yscrollcommand=barra_resultado.set)
    resultado_textual.grid_remove()
    barra_resultado.grid_remove()

    grafico = tk.Frame(conteudo, relief="groove", borderwidth=1)
    grafico.grid(row=5, column=0, sticky="nsew", pady=(16, 0))
    grafico.columnconfigure(0, weight=1)
    grafico.rowconfigure(3, weight=1)
    tk.Label(grafico, text="Gráfico").grid(row=0, column=0, sticky="w")

    campos_faixa = tk.Frame(grafico)
    campos_faixa.grid(row=1, column=0, sticky="ew")
    tk.Label(campos_faixa, text="Faixa de x").grid(row=0, column=0, sticky="w")
    tk.Entry(
        campos_faixa, name="faixa_esquerda", width=12,
        textvariable=faixa_esquerda_texto,
    ).grid(row=0, column=1, padx=(8, 4))
    tk.Label(campos_faixa, text="até").grid(row=0, column=2)
    tk.Entry(
        campos_faixa, name="faixa_direita", width=12,
        textvariable=faixa_direita_texto,
    ).grid(row=0, column=3, padx=(4, 8))
    erro_faixa = tk.Label(
        grafico, name="erro_faixa", text="", fg="red"
    )
    erro_faixa.grid(row=2, column=0, sticky="w")
    area_grafico = tk.Frame(grafico)
    area_grafico.grid(row=3, column=0, sticky="nsew")
    area_grafico.columnconfigure(0, weight=1)
    area_grafico.rowconfigure(0, weight=1)

    texto_copia = None
    visualizacao = None
    resultado_atual = None
    figura_grafico = None
    widget_grafico = None

    def limpar_grafico():
        nonlocal figura_grafico, widget_grafico
        if widget_grafico is not None:
            try:
                widget_grafico.destroy()
            finally:
                widget_grafico = None
                if figura_grafico is not None:
                    figura_grafico.clear()
                    figura_grafico = None
        elif figura_grafico is not None:
            figura_grafico.clear()
            figura_grafico = None
        erro_faixa.config(text="")

    def atualizar_grafico():
        nonlocal figura_grafico, widget_grafico
        limpar_grafico()
        if resultado_atual is None:
            return
        try:
            faixa = None
            if tipo_integral.get() == "indefinida":
                faixa = validar_faixa(
                    faixa_esquerda_texto.get(), faixa_direita_texto.get()
                )
            figura = criar_figura(resultado_atual, faixa)
            try:
                widget = _incorporar_grafico(area_grafico, figura)
            except Exception:
                figura.clear()
                raise
            figura_grafico = figura
            widget_grafico = widget
        except (ValueError, TypeError) as erro:
            erro_faixa.config(text=f"Não foi possível mostrar o gráfico: {erro}")
        except Exception:
            erro_faixa.config(text="Não foi possível mostrar o gráfico.")

    tk.Button(
        campos_faixa, text="Atualizar gráfico", command=atualizar_grafico
    ).grid(row=0, column=4)

    def atualizar_resultado_textual(texto):
        resultado_textual.config(state="normal")
        resultado_textual.delete("1.0", "end")
        if texto:
            resultado_textual.insert("1.0", texto)
        resultado_textual.config(state="disabled")
        resultado_textual.yview_moveto(0)
        if texto:
            resultado_textual.grid()
            barra_resultado.grid()
        else:
            resultado_textual.grid_remove()
            barra_resultado.grid_remove()

    def limpar_saida(*_argumentos):
        nonlocal texto_copia, visualizacao, resultado_atual
        texto_copia = None
        resultado_atual = None
        limpar_grafico()
        if visualizacao is not None:
            visualizacao.destroy()
            visualizacao = None
        atualizar_resultado_textual("")
        for rotulo in (
            erro_expressao, erro_inferior, erro_superior, mensagem_geral
        ):
            rotulo.config(text="")
        botao_copiar.config(state="disabled")

    def calcular():
        nonlocal texto_copia, visualizacao, resultado_atual
        limpar_saida()
        try:
            if tipo_integral.get() == "definida":
                resultado = processar_integral_definida(
                    expressao_texto.get(),
                    inferior_texto.get(),
                    superior_texto.get(),
                )
            else:
                resultado = processar_integral_indefinida(
                    expressao_texto.get()
                )
            texto_copia = texto_para_copia(resultado)
        except (ValueError, TypeError) as erro:
            rotulos_de_erro = {
                "expressao": erro_expressao,
                "limite_inferior": erro_inferior,
                "limite_superior": erro_superior,
            }
            rotulo = rotulos_de_erro.get(
                getattr(erro, "campo_entrada", None), mensagem_geral
            )
            rotulo.config(text=str(erro))
            return
        except Exception:
            mensagem_geral.config(text="Não foi possível calcular a integral.")
            return

        atualizar_resultado_textual(texto_copia)
        botao_copiar.config(state="normal")
        resultado_atual = resultado
        try:
            visualizacao = _renderizar_resultado(
                area_resultado, mathtext_resultado(resultado)
            )
        except Exception:
            pass
        atualizar_grafico()

    def copiar():
        if texto_copia is None:
            return
        try:
            raiz.clipboard_clear()
            raiz.clipboard_append(texto_copia)
        except Exception:
            mensagem_geral.config(text="Não foi possível copiar o resultado.")

    def alternar_tipo():
        atualizar_campos_limites()
        if tipo_integral.get() == "definida":
            campos_faixa.grid_remove()
        else:
            campos_faixa.grid()
        limpar_saida()

    tk.Radiobutton(
        selecao,
        text="Indefinida",
        variable=tipo_integral,
        value="indefinida",
        command=alternar_tipo,
    ).grid(row=0, column=0, sticky="w")
    tk.Radiobutton(
        selecao,
        text="Definida",
        variable=tipo_integral,
        value="definida",
        command=alternar_tipo,
    ).grid(row=0, column=1, sticky="w", padx=(12, 0))
    tk.Button(acoes, text="Calcular", command=calcular).grid(
        row=0, column=0, sticky="w"
    )
    botao_copiar = tk.Button(
        acoes, text="Copiar", command=copiar, state="disabled"
    )
    botao_copiar.grid(row=0, column=1, sticky="w", padx=(8, 0))

    expressao_texto.trace_add("write", limpar_saida)

    def invalidar_limite(*_argumentos):
        if tipo_integral.get() == "definida":
            limpar_saida()

    inferior_texto.trace_add("write", invalidar_limite)
    superior_texto.trace_add("write", invalidar_limite)

    def invalidar_faixa(*_argumentos):
        if tipo_integral.get() == "indefinida":
            limpar_grafico()

    faixa_esquerda_texto.trace_add("write", invalidar_faixa)
    faixa_direita_texto.trace_add("write", invalidar_faixa)


def abrir_janela():
    """Abre a janela principal e inicia o ciclo de eventos do Tkinter."""
    raiz = tk.Tk()
    criar_janela(raiz)
    raiz.mainloop()
