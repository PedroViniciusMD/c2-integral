"""Janela principal da calculadora de integrais."""

import tkinter as tk


def criar_janela(raiz):
    """Monta a interface inicial em uma raiz Tkinter existente."""
    raiz.title("Calculadora de integrais")
    raiz.columnconfigure(0, weight=1)
    raiz.rowconfigure(0, weight=1)

    conteudo = tk.Frame(raiz)
    conteudo.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
    conteudo.columnconfigure(0, weight=1)
    conteudo.rowconfigure(4, weight=1)

    selecao = tk.Frame(conteudo)
    selecao.grid(row=0, column=0, sticky="w")
    tipo_integral = tk.StringVar(master=raiz, value="indefinida")

    campo_expressao = tk.Frame(conteudo)
    campo_expressao.grid(row=1, column=0, sticky="ew", pady=(12, 0))
    campo_expressao.columnconfigure(0, weight=1)
    tk.Label(campo_expressao, text="Expressão").grid(
        row=0, column=0, sticky="w"
    )
    tk.Entry(campo_expressao).grid(row=1, column=0, sticky="ew")

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
    tk.Entry(campo_inferior).grid(row=1, column=0, sticky="ew")

    campo_superior = tk.Frame(campos_limites)
    campo_superior.grid(row=0, column=1, sticky="ew")
    campo_superior.columnconfigure(0, weight=1)
    tk.Label(campo_superior, text="Limite superior").grid(
        row=0, column=0, sticky="w"
    )
    tk.Entry(campo_superior).grid(row=1, column=0, sticky="ew")

    def atualizar_campos_limites():
        if tipo_integral.get() == "definida":
            campos_limites.grid()
        else:
            campos_limites.grid_remove()

    tk.Radiobutton(
        selecao,
        text="Indefinida",
        variable=tipo_integral,
        value="indefinida",
        command=atualizar_campos_limites,
    ).grid(row=0, column=0, sticky="w")
    tk.Radiobutton(
        selecao,
        text="Definida",
        variable=tipo_integral,
        value="definida",
        command=atualizar_campos_limites,
    ).grid(row=0, column=1, sticky="w", padx=(12, 0))
    atualizar_campos_limites()

    saida = tk.Frame(conteudo)
    saida.grid(row=3, column=0, sticky="ew", pady=(16, 0))
    saida.columnconfigure(0, weight=1)
    tk.Label(saida, text="Mensagens").grid(row=0, column=0, sticky="w")
    tk.Label(saida, text="").grid(row=1, column=0, sticky="ew")
    tk.Label(saida, text="Resultado").grid(row=2, column=0, sticky="w")
    tk.Label(saida, text="").grid(row=3, column=0, sticky="ew")

    grafico = tk.Frame(conteudo, relief="groove", borderwidth=1)
    grafico.grid(row=4, column=0, sticky="nsew", pady=(16, 0))
    grafico.columnconfigure(0, weight=1)
    grafico.rowconfigure(1, weight=1)
    tk.Label(grafico, text="Gráfico").grid(row=0, column=0, sticky="w")


def abrir_janela():
    """Abre a janela principal e inicia o ciclo de eventos do Tkinter."""
    raiz = tk.Tk()
    criar_janela(raiz)
    raiz.mainloop()
