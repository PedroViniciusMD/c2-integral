# c2-integral

Calculadora de integrais em Python com interface gráfica. O projeto recebe uma expressão matemática em função de `x`, calcula sua integral com SymPy e apresenta o resultado e o gráfico da função informada.

## 1. Objetivo e funcionalidades

O projeto tem finalidade acadêmica: facilitar a experimentação com integrais definidas e indefinidas por meio de entradas próximas da escrita matemática habitual.

- Calcula integrais indefinidas e apresenta a constante de integração `+ C` na interface.
- Calcula integrais definidas entre limites reais e finitos, inclusive quando a ordem dos limites é invertida.
- Exibe o resultado em texto, permite copiá-lo e, quando possível, mostra a fórmula formatada.
- Desenha a função original e, nas integrais definidas, destaca a região entre os limites.
- Informa erros de entrada, de domínio e de integrais não resolvidas simbolicamente.


## 3. Pré-requisitos

- Python 3.14. e um ambiente capaz de abrir janelas gráficas Tkinter.

## 4. Instalação e ambiente virtual

Abra um terminal na raiz do projeto, onde estão `main.py` e `requirements.txt`.

No macOS ou Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows, com PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

O arquivo `requirements.txt` instala **SymPy, NumPy e Matplotlib**, usados pela aplicação, e **pytest**, usado nos testes. Tkinter é fornecido pela instalação de Python ou pelo sistema operacional.

Para sair do ambiente virtual depois de usar o projeto, execute `deactivate`.

## 5. Como executar a interface gráfica

Com o ambiente virtual ativo e a partir da raiz do projeto:

```bash
python main.py
```

O comando abre a janela **Calculadora de integrais**. A opção **Indefinida** é selecionada ao iniciar.

## 6. Como utilizar a calculadora

### Integral indefinida

1. Selecione **Indefinida**.
2. No campo **Expressão**, digite `x^2`.
3. Clique em **Calcular**. O resultado textual será `x**3/3 + C`.

Esse exemplo corresponde a ∫x² dx = x³/3 + C. O botão **Copiar** copia o resultado textual. A faixa inicial do gráfico vai de `-10` a `10`; para alterá-la, preencha os dois campos de **Faixa de x** e clique em **Atualizar gráfico**. O extremo esquerdo deve ser menor que o direito.

Outro exemplo: ao digitar `sen(x)` no campo **Expressão**, o resultado textual será `-cos(x) + C`.

### Integral definida

1. Selecione **Definida**. Os campos dos limites serão exibidos.
2. Em **Expressão**, digite `x^2`.
3. Em **Limite inferior**, digite `0`; em **Limite superior**, digite `2`.
4. Clique em **Calcular**. O resultado textual será `8/3`.

Esse exemplo corresponde a ∫₀² x² dx = 8/3. A ordem dos limites é mantida no cálculo: com os mesmos campos preenchidos como `2` e `0`, respectivamente, o resultado será `-8/3`.

Para experimentar uma singularidade integrável, informe **Expressão** `1/raiz(x)`, **Limite inferior** `0` e **Limite superior** `1`. O resultado será `2`.

## 7. Dicionário de entradas matemáticas

Digite as expressões no campo **Expressão** usando as formas abaixo. Os exemplos da última coluna podem ser copiados diretamente para a calculadora. A coluna de notação convencional serve para leitura; use a coluna de sintaxe para digitar.

| Operação ou função matemática | Notação matemática convencional | Sintaxe aceita pela calculadora | Exemplo de entrada |
|---|---|---|---|
| Potenciação | x² | `x**2`, `x^2` ou `xˆ2` | `x^2 + 1` |
| Multiplicação | 2x | `2x` ou `2*x` | `2x + 3` |
| Raiz quadrada | √x | `raiz(x)` ou `sqrt(x)` | `raiz(x^2 + 4)` |
| Seno | sen(x) | `sen(x)` ou `sin(x)` | `2*sen(x)` |
| Cosseno | cos(x) | `cos(x)` | `cos(x) + 1` |
| Tangente | tg(x) | `tg(x)` ou `tan(x)` | `tg(x)` |
| Logaritmo natural | ln(x) | `ln(x)` ou `log(x)` | `ln(x)` |
| Logaritmo na base 10 | log₁₀(x) | `log10(x)` | `log10(x)` |
| Exponencial de base e | eˣ | `e^x` ou `e**x` | `e^x + e^(-x)` |
| Constante π | π | `pi` | `pi*x` |
| Constante e | e | `e` | `e*x` |
| Frações | ½, ¾ | `1/2`, `3/4` | `x^(1/2) + 3/4` |
| Expressão composta | (x + 1)(2x − 1) | Parênteses e `*`; `2x` também é aceito | `(x+1)*(2x-1)` |

Os mesmos formatos de números e constantes podem ser usados nos campos de limite, por exemplo `1/2`, `pi` e `raiz(2)`. Os limites precisam representar números reais e finitos, sem a variável `x`.

### Limitações conhecidas

- A única variável matemática permitida nas expressões é `x`. Outras variáveis são rejeitadas na validação.
- Uma expressão vazia ou malformada gera erro. O cálculo simbólico também pode não encontrar uma antiderivada ou um resultado definido para certas expressões.
- Integrais definidas em trechos comprovadamente fora do domínio real são rejeitadas. Singularidades integráveis podem ser calculadas; integrais divergentes são rejeitadas.
- Os limites de uma integral definida devem ser números reais e finitos. Para a faixa de visualização da integral indefinida, também é necessário que o extremo esquerdo seja menor que o direito.


## Testes automatizados

Com o ambiente virtual ativo e na raiz do projeto, execute:

```bash
python -m pytest -v
```

Os testes ficam em `tests/` e cobrem a interpretação das entradas, os cálculos, as validações feitas pelo fluxo da interface, a janela e os gráficos. O comando também pode ser executado como `python3 -m pytest -v` quando `python3` aponta para o ambiente desejado.
