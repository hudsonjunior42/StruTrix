
-----

# StruTrix: Análise Estrutural 2D (Pórticos Planos)

O StruTrix é um software para análise de estruturas reticuladas planas utilizando o Método dos Elementos Finitos (MEF). Construído com Python e PyQt5, oferece uma interface gráfica (GUI) completa para definição de geometria, carregamentos e visualização de resultados.

-----

## Sobre e Funcionalidades

O objetivo principal do StruTrix é fornecer uma ferramenta acessível e prática para modelar e solucionar problemas de estática estrutural em duas dimensões.

| Categoria | Funcionalidade | Descrição |
| :--- | :--- | :--- |
| **Modelagem** | Criação de Nós e Barras | Definição de coordenadas ($X, Y$) e conectividade da estrutura. |
| **Propriedades** | Materiais e Seção | Entrada de dados para Módulo de Elasticidade ($E$), Área ($A$) e Momento de Inércia ($I$). |
| **Condições** | Apoios e Rótulas | Definição de restrições de deslocamento ($X, Y, R_z$) e liberação de rotação nas extremidades das barras. |
| **Carregamento** | Nodal e Distribuído | Aplicação de forças nodais ($F_x, F_y, M_z$) e cargas uniformemente distribuídas ($Q$). |
| **Cálculo** | Motor MEF | Execução da análise estrutural, montagem das matrizes de rigidez e solução do sistema global. |
| **Visualização** | Diagramas e Deformada | Plotagem interativa da estrutura deformada e dos diagramas de Esforços Normais, Cisalhantes e Momento Fletor. |
| **IO** | Arquivos de Projeto | Salvar e carregar modelos em formato proprietário (`.stx`). |

-----

## Tecnologias Utilizadas

O projeto é desenvolvido puramente em Python e utiliza as seguintes bibliotecas-chave:

| Tecnologia | Função no Projeto |
| :--- | :--- |
| **Python 3.x** | Linguagem principal de desenvolvimento. |
| **PyQt5** | Construção da **Interface Gráfica de Utilizador (GUI)**, fornecendo os *widgets* de entrada e exibição. |
| **Pandas & NumPy** | **Core de Cálculo e Dados.** Manipulação eficiente de matrizes e DataFrames para o MEF. |
| **Matplotlib** | **Engine de Plotagem.** Responsável por desenhar a estrutura e os resultados no *canvas* interativo. |
| **JSON** | Formato de arquivo usado para persistência dos dados (`.stx`). |

-----

## Estrutura do Projeto

A organização do código separa claramente a interface de usuário (`main_window.py`) da lógica de domínio (`core/`) e da lógica de visualização (`graphics/`).

| Arquivo/Diretório | Módulo Principal | Responsabilidade |
| :--- | :--- | :--- |
| `main.py` | - | Ponto de entrada da aplicação e configurações iniciais do sistema operacional. |
| `main_window.py` | `StruTrixMainWindow` | **Gerenciamento da GUI (Views).** Define o layout, constrói as abas e trata os eventos do usuário (clicks, seleções). |
| `core/` | - | **Módulos da Lógica de Domínio e Cálculo.** |
| ├── `data_handler.py` | `DataHandler` | Gerencia e valida o estado do modelo (DataFrames de Nós e Barras). |
| ├── `solver.py` | `StructuralSolver` | Implementa o algoritmo do **MEF**, realizando o cálculo estrutural. |
| └── `file_manager.py` | `FileManager` | Funções estáticas para Salvar/Carregar arquivos (`.stx`). |
| `graphics/` | - | **Módulos de Plotagem e Visualização.** |
| ├── `plotter.py` | `StructuralPlotter` | Lógica Matplotlib para desenhar a geometria, apoios, cargas e diagramas. |
| └── `MatplotlibCanvas` | `MatplotlibCanvas` | Integração do ambiente Matplotlib como um *widget* dentro do PyQt5. |

-----

## Instalação e Execução

### Pré-requisitos

Certifique-se de ter o **Python 3** instalado no seu sistema.

### 1\. Instalar Dependências

Todas as dependências necessárias (PyQt5, numpy, pandas, matplotlib) podem ser instaladas via `pip`:

```bash
pip install PyQt5 numpy pandas matplotlib
```

### 2\. Clonar/Baixar o Projeto

Baixe o código-fonte e garanta que todos os arquivos estejam na estrutura de diretórios esperada (especialmente `core/` e `graphics/`).

### 3\. Executar o Aplicativo

Para iniciar a GUI, execute o arquivo principal:

```bash
python main.py
```

-----

## Guia de Uso Rápido

O fluxo de trabalho no StruTrix é sequencial e baseado nas abas de entrada de dados no painel esquerdo:

1.  **Modelagem (Abas "Nós" e "Barras"):**
      * Comece definindo os nós com suas coordenadas $X$ e $Y$.
      * Conecte os nós para formar as barras, atribuindo as propriedades $E, A, I$.
2.  **Condições de Contorno (Aba "Apoios"):**
      * Aplique as restrições aos nós (ex: engaste, apoio de 2º gênero).
3.  **Carregamento (Abas "Cargas..."):**
      * Defina as forças e momentos aplicados nos nós ou as cargas distribuídas nas barras.
5.  **Deslocamentos Prescritos:
     * Aplique deslocamentos prescritos (X, Y ou Rotação) nos nós.
4.  **Cálculo:**
      * Clique no botão **"Calcular"**  para rodar a análise.
5.  **Visualização:**
      * Use o painel **"Controle de Visualização"** para alternar entre a geometria, a **Forma Deformada** e os **Diagramas de Esforços** (Normal, Cisalhante, Momento Fletor).

-----

## Contato e Status

  * **Status do Projeto:** Versão 0.76 (Em Desenvolvimento)
  * **Autor:** Hudson Santos Menezes Júnior (Mencionado na caixa 'Sobre')

Sinta-se à vontade para entrar em contato para sugestões ou dúvidas.
