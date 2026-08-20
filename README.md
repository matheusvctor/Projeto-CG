# Repositório de Computação Gráfica

Ambiente integrado com implementações de algoritmos fundamentais e avançados de **Computação Gráfica** e **Processamento Digital de Imagens (PDI)** desenvolvidos em Python.

---

## 📂 Estrutura do Repositório

```
Computacao-grafica-main/
│
├── Projeto 1 - Computação Gráfica/           # Projeto da Unidade 1
│   └── Projeto_CG_Final/
│       ├── main_menu.py                      # Menu Principal da Unidade 1
│       ├── mod_primitivas/Questao1/          # DDA, Bresenham e Transformações 2D
│       ├── mod_recortes/Questao2/            # Cohen-Sutherland e Sutherland-Hodgman
│       ├── mod_3d/Questao3/                  # Modelagem e Transformações 3D
│       └── mod_imagens/Questao4/             # Transformações afins em imagens PGM
│
├── Projeto - Processamento de Imagens/       # Projeto de Processamento de Imagens
│   └── PI/
│       ├── executar_projeto.py               # Ponto de entrada do Projeto
│       ├── dist/
│       │   └── Projeto Processamento de Imagem.exe # Executável standalone independente
│       ├── assets/                           # Imagens de teste (.pgm, .pbm)
│       └── src/laboratorio_imagens/          # Módulos matemáticos e Interface com Menu Lateral
│
└── CG/                                       # Laboratórios e scripts práticos auxiliares
```

---

## 🔬 Destaques dos Projetos

### ◈ Projeto de Processamento de Imagens
- **Interface com Menu Lateral**: Navegação intuitiva entre todas as ferramentas.
- **Filtros Espaciais**: Média, Mediana, Laplaciano Passa-Altas, Roberts, Roberts Cruzado, Prewitt, Sobel (eixos e magnitude) e High-Boost.
- **Operações Pixel a Pixel**: Soma, Subtração, Multiplicação, Divisão, AND, OR, XOR e NOT (com truncamento e normalização dinâmica).
- **Intensidade & Histograma**: Negativo, Gamma ($\gamma$), Logaritmo, Função Sigmóide, Faixa Dinâmica, Transferência Linear e Equalização de Histograma via CDF.
- **Morfologia Matemática**: Erosão, Dilatação, Abertura, Fechamento, Contornos, Gradiente Morfológico, Top/Bottom-Hat e Hit-or-Miss (binário e tons de cinza).
- **Transformações Geométricas**: Escala, Translação, Rotação (mapeamento inverso cartesiano), Reflexão e Cisalhamento.
- **Deformação e Morfismo Temporal**: Triangulação de Delaunay e interpolação afim por triângulos ($t \in [0, 1]$) com exportação para GIF animado.
- **Parser NetPBM**: Suporte estrito a NetPBM PGM (`.pgm` P2/P5) e PBM (`.pbm` P1).

### ◈ Projeto 1 - Computação Gráfica (Unidade 1)
- **Questão 1 & 5**: Rasterização de primitivas (DDA, Bresenham), cônicas e Splines de Bézier cúbicas com 4 pontos de controle.
- **Questão 2**: Algoritmos de recorte de retas (**Cohen-Sutherland**) com animação contínua e recorte de polígonos (**Sutherland-Hodgman**).
- **Questão 3**: Modelagem tridimensional, transformações homogêneas 3D e projeção isométrica com viewport.
- **Questão 4**: Manipulação afim com mapeamento inverso sobre matrizes de imagem PGM.

---

## 🚀 Como Executar

### Projeto de Processamento de Imagens:
```powershell
# Execução direta via Python:
python ".\Projeto - Processamento de Imagens\PI\executar_projeto.py"

# Ou via executável independente (.exe):
& ".\Projeto - Processamento de Imagens\PI\dist\Projeto Processamento de Imagem.exe"
```

### Projeto 1 (Unidade 1):
```powershell
python ".\Projeto 1 - Computação Gráfica\Projeto_CG_Final\main_menu.py"
```
