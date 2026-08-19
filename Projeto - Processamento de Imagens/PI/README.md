# Projeto de Computação Gráfica — Processamento Digital de Imagens

Sistema integrado de processamento, análise e manipulação digital de imagens em níveis de cinza (`.pgm`), binárias (`.pbm`) e formatos universais (`.png`, `.jpg`), desenvolvido em Python com interface moderna e processamento matricial de alto desempenho com NumPy, SciPy e Pillow.

---

## 📑 Sumário

- [Visão Geral](#-visão-geral)
- [Módulos e Fundamentação](#-módulos-e-fundamentação)
  - [1. Filtros Espaciais e Realce](#1-filtros-espaciais-e-realce)
  - [2. Operações Aritméticas e Lógicas](#2-operações-aritméticas-e-lógicas)
  - [3. Intensidade e Histograma](#3-intensidade-e-histograma)
  - [4. Morfologia Matemática](#4-morfologia-matemática)
  - [5. Transformações Geométricas](#5-transformações-geométricas)
  - [6. Morfismo Temporal (Morphing)](#6-morfismo-temporal-morphing)
- [Recursos da Interface](#-recursos-da-interface)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Como Executar](#-como-executar)
  - [Via Interpretador Python](#via-interpretador-python)
  - [Via Executável Standalone (.exe)](#via-executável-standalone-exe)
- [Formatos Suportados](#-formatos-suportados)

---

## 👁️ Visão Geral

Este **projeto de computação gráfica** foi desenvolvido para fornecer um laboratório visual completo para experimentação de algoritmos clássicos e avançados de Processamento Digital de Imagens (PDI). 

O sistema conta com leitura e escrita nativa de arquivos no formato **NetPBM** (sem depender de bibliotecas externas para o parsing matricial), garantindo precisão matemática pixel a pixel.

---

## 🔬 Módulos e Fundamentação

### 1. Filtros Espaciais e Realce
Aplica operações de convolução e filtragem não linear sobre a vizinhança $3 \times 3$:
- **Filtro da Média**: Suavização espacial uniforme através de máscara normalizada $\frac{1}{9} \mathbf{1}_{3\times3}$.
- **Filtro da Mediana**: Redução eficiente de ruído impulsivo (sal e pimenta) preservando bordas.
- **Passa-Altas Básico**: Realce de transições e detalhes finos via operador Laplaciano.
- **Operador de Roberts**: Gradiente por diferenças simples nos eixos $X$, $Y$ e magnitude combinada.
- **Operador de Roberts Cruzado**: Gradiente diagonal cruzado com máscaras $2\times2$ centralizadas.
- **Operador de Prewitt**: Detecção de bordas direcionais e magnitude $G = \sqrt{G_x^2 + G_y^2}$.
- **Operador de Sobel**: Gradiente de bordas com ponderação de suavização central ($X$, $Y$ e magnitude).
- **Filtragem High-Boost**: Realce de alto reforço parametrizável pelo fator $A \ge 1.0$:
  $$\text{High-Boost} = A \cdot f(x,y) - f_{\text{passa-baixas}}(x,y)$$
- **Filtro Livre**: Matriz $3 \times 3$ editável diretamente na interface com visualização de coeficientes em tempo real.

---

### 2. Operações Aritméticas e Lógicas
Processamento pontual entre duas imagens com alinhamento automático de dimensões:
- **Aritméticas**:
  - **Soma** ($A + B$): Fusão e sobreposição de imagens.
  - **Subtração** ($A - B$): Detecção de diferenças e remoção de fundo.
  - **Multiplicação** ($A \times B$): Mascaramento e modulação de contraste.
  - **Divisão** ($A \div B$): Correção de iluminação não uniforme.
  - *Modos de pós-processamento*: Truncamento fixo $[0, 255]$ ou Normalização Dinâmica min-max.
- **Lógicas Bit a Bit**:
  - `AND`, `OR`, `XOR` e `NOT` aplicados em níveis de cinza ou imagens binárias.

---

### 3. Intensidade e Histograma
Mapeamento de tons de cinza e equalização radiométrica:
- **Negativo da Imagem**: $S = 255 - r$.
- **Transformação Gamma (Lei de Potência)**: $S = c \cdot r^\gamma$, permitindo expansão de tons escuros ($\gamma < 1$) ou claros ($\gamma > 1$).
- **Transformação Logarítmica**: $S = a \cdot \log(1 + r)$, ideal para expansão de faixas dinâmicas comprimidas.
- **Função de Transferência Geral (Sigmóide)**: Curva em S configurável por centro $w_0$ e largura de transição.
- **Faixa Dinâmica (Stretching)**: Expansão linear do intervalo $[\min, \max]$ para a faixa total $[0, 255]$.
- **Transferência Linear**: $S = a \cdot r + b$ com controle direto de ganho e offset.
- **Equalização de Histograma**: Redistribuição uniforme baseada na Função de Distribuição Acumulada (CDF):
  $$s_k = T(r_k) = (L-1) \sum_{j=0}^{k} p_r(r_j)$$
- **Visualizador Gráfico de Histograma**: Gráficos com grade, eixos graduados, contagem de pixels e janela de ampliação (Zoom) para apresentações.

---

### 4. Morfologia Matemática
Processamento não linear baseado na teoria dos conjuntos e geometria de formas (suporta imagens binárias e em níveis de cinza):
- **Erosão & Dilatação**: Operadores fundamentais com elemento estruturante configurável (Quadrado $3\times3$, Cruz $3\times3$, Quadrado $5\times5$).
- **Abertura** (Erosão seguida de Dilatação): Eliminação de ruídos externos e saliências finas.
- **Fechamento** (Dilatação seguida de Erosão): Preenchimento de pequenos buracos e união de descontinuidades.
- **Contorno Interno**: $f - (f \ominus b)$
- **Contorno Externo**: $(f \oplus b) - f$
- **Gradiente Morfológico**: $(f \oplus b) - (f \ominus b)$
- **Top-Hat & Bottom-Hat**: Realce de detalhes claros/escuros em relação ao fundo.
- **Hit-or-Miss**: Detecção de padrões e cantos específicos.

---

### 5. Transformações Geométricas
Mapeamento inverso com interpolação para evitar lacunas (aliasing):
- **Escala**: Ampliação e redução nos eixos $S_x$ e $S_y$.
- **Translação**: Deslocamento espacial $(t_x, t_y)$ com preservação dimensional.
- **Rotação**: Rotação euclidiana por qualquer ângulo $\theta$ com convenção cartesiana anti-horária.
- **Reflexão**: Espelhamento horizontal, vertical e diagonal.
- **Cisalhamento (Shear)**: Deformação angular nos eixos $X$ e $Y$.

---

### 6. Morfismo Temporal (Morphing)
Implementação de deformação contínua baseada no método descrito em **Anton & Rorres (Álgebra Linear com Aplicações, Seção 11.21)**:
- **Triangulação de Delaunay**: Geração automática de malha triangular sobre os pontos de controle marcados.
- **Mapeamento Afim por Triângulo**: Interpolação das coordenadas e níveis de cinza para o parâmetro de tempo $t \in [0, 1]$.
- **Recursos Interativos**:
  - Marcação visual de pontos correspondentes com clique.
  - Pré-visualização instantânea ao deslizar a barra de tempo $t$.
  - Exportação para animação em **GIF** com controle de quadros intermediários e taxa de atualização (fps/ms).
  - Exportação da sequência completa de frames `.pgm`.
  - Amostras de teste demonstrativas pré-configuradas.

---

## 🖥️ Recursos da Interface

- **Sidebar Navigation**: Menu lateral moderno e intuitivo agrupando todos os módulos do sistema.
- **Inspetor Matricial de Pixels**: Tabela dinâmica de pixels em tempo real com opções de janela (`10x10`, `12x12`, `20x20`, `30x30`, `40x40`), fixação com botão esquerdo e liberação com botão direito.
- **Sincronização de Painéis**: Espelhamento das coordenadas do inspetor entre os painéis de origem e resultado.
- **Toasts de Status**: Notificações contextuais animadas para sucesso, avisos e validações.
- **Tema Obsidian & Cyan Pro**: Interface escura de alto contraste e legibilidade, projetada para visualização técnica e apresentações.

---

## 📁 Estrutura do Projeto

```
PI/
├── executar_projeto.py              # Ponto de entrada da aplicação
├── requirements.txt                 # Dependências do projeto
├── dist/
│   └── LaboratorioProcessamentoImagens.exe  # Executável standalone compilado
├── assets/                          # Imagens de exemplo e testes
│   ├── exemplos/                    # lena.pgm, airplane.pgm, lenasalp.pgm, etc.
│   └── morfismo/                    # Amostras para deformação temporal
└── src/
    └── laboratorio_imagens/
        ├── aplicacao.py             # Inicializador do loop da interface
        ├── tema.py                  # Definições de paleta de cores e tipografia
        ├── core/                    # Núcleo matemático e de processamento
        │   ├── io_netpbm.py         # Leitor/escritor NetPBM (.pgm, .pbm)
        │   ├── utilidades_matriz.py # Funções auxiliares e de convolução
        │   ├── filtros_espaciais.py # Máscaras e filtros da Aula 9
        │   ├── operacoes_pixel.py   # Operações aritméticas e lógicas
        │   ├── transformacoes_intensidade.py # Mapeamento de tons de cinza
        │   ├── histograma.py        # Cálculo e equalização de histograma
        │   ├── operacoes_morfologicas.py # Morfologia matemática
        │   ├── transformacoes_geometricas.py # Transformações afins
        │   └── morfismo.py          # Triangulação e interpolação temporal
        └── ui/                      # Camada de interface gráfica
            ├── janela_principal.py  # Janela principal com Sidebar
            ├── widgets.py           # Painéis de imagem, grade de pixels e histogramas
            ├── abas_processamento.py # Telas de filtros, operações e histograma
            └── abas_avancadas.py    # Telas de morfologia, geometria e morfismo
```

---

## 🚀 Como Executar

### Via Interpretador Python

1. Certifique-se de possuir o Python 3.10+ instalado.
2. Instale as dependências:
   ```powershell
   pip install -r requirements.txt
   ```
3. Execute o inicializador:
   ```powershell
   python .\executar_projeto.py
   ```

### Via Executável Standalone (.exe)

O projeto inclui um executável compilado independente em `dist/`:
- Basta executar com dois cliques o arquivo:
  ```
  PI\dist\LaboratorioProcessamentoImagens.exe
  ```
- *Não requer Python ou bibliotecas instaladas na máquina de destino.*

---

## 📄 Formatos Suportados

- **PGM (Portable Graymap)**: Formatos ASCII (`P2`) e Binário (`P5`) para imagens em níveis de cinza (8 bits, 0–255).
- **PBM (Portable Bitmap)**: Formatos ASCII (`P1`) e Binário (`P4`) para imagens monocromáticas binárias (0 e 1).
- **GIF**: Exportação de sequências animadas no módulo de morfismo.

