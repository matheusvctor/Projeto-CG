# Repositório de Computação Gráfica & Processamento Digital de Imagens

Ambiente integrado com implementações de algoritmos fundamentais e avançados de **Computação Gráfica (CG)** e **Processamento Digital de Imagens (PDI)** desenvolvidos em Python.

---

## 📂 Estrutura Geral do Repositório

```
Computacao-grafica-main/
│
├── Projeto 1 - Computação Gráfica/           # Primeiro Projeto (Motor de CG e Primitivas)
│   └── Projeto_CG_Final/
│       ├── main_menu.py                      # Hub Principal de Computação Gráfica
│       ├── mod_primitivas/Questao1/          # DDA, Bresenham e Transformações 2D
│       ├── mod_recortes/Questao2/            # Cohen-Sutherland e Sutherland-Hodgman
│       ├── mod_3d/Questao3/                  # Transformações 3D e Projeções
│       └── mod_imagens/Questao4/             # Transformações afins em matrizes PGM
│
├── Projeto 2 - Processamento de Imagens/     # Segundo Projeto (Nexus PDI - Vision Studio)
│   └── PI/
│       ├── executar_projeto.py               # Ponto de entrada do Projeto 2
│       ├── dist/
│       │   └── LaboratorioProcessamentoImagens.exe # Executável standalone independente
│       ├── assets/                           # Imagens de teste (.pgm, .pbm)
│       └── src/laboratorio_imagens/          # Módulos matemáticos e Interface com Sidebar
│
└── CG/                                       # Laboratórios e scripts práticos auxiliares
```

---

## 🔬 Destaques dos Projetos

### ◈ Projeto 2: Nexus PDI — Processamento Digital de Imagens
- **Interface Moderna com Sidebar**: Navegação lateral dinâmica sem abas horizontais tradicionais.
- **Filtros Espaciais**: Média, Mediana, Laplaciano Passa-Altas, Roberts, Roberts Cruzado, Prewitt, Sobel (com componentes nos eixos e magnitude) e High-Boost.
- **Operações Pixel a Pixel**: Soma, Subtração, Multiplicação, Divisão, AND, OR, XOR e NOT com controle de truncamento/normalização.
- **Intensidade & Histograma**: Negativo, Gamma ($\gamma$), Logaritmo, Função Sigmóide, Faixa Dinâmica, Transferência Linear e Equalização de Histograma via CDF com visualizador e zoom de apresentação.
- **Morfologia Matemática**: Erosão, Dilatação, Abertura, Fechamento, Contornos, Gradiente Morfológico, Top/Bottom-Hat e Hit-or-Miss (binário e tons de cinza).
- **Transformações Geométricas**: Escala, Translação, Rotação (mapeamento inverso cartesiano), Reflexão e Cisalhamento.
- **Deformação e Morfismo Temporal**: Triangulação de Delaunay e interpolação afim por triângulos ($t \in [0, 1]$) com exportação para GIF animado e frames.
- **Inspetor Matricial de Pixels**: Visualização em tempo real de matrizes de pixels ($10\times10$ até $40\times40$).

### ◈ Projeto 1: Motor de Computação Gráfica
- **Questão 1**: Rasterização de primitivas (DDA, Bresenham) e transformações geométricas 2D.
- **Questão 2**: Algoritmos de recorte de retas (**Cohen-Sutherland**) e recorte de polígonos convexos (**Sutherland-Hodgman**).
- **Questão 3**: Modelagem tridimensional, rotações espaciais em múltiplos eixos e projeção geométrica.
- **Questão 4**: Manipulação e transformações espaciais sobre matrizes de imagem PGM.

---

## 🚀 Como Executar

### Projeto 2 (Processamento de Imagens):
```powershell
# Execução direta via Python:
python ".\Projeto 2 - Processamento de Imagens\PI\executar_projeto.py"

# Ou execute diretamente o executável independente (não precisa de Python):
& ".\Projeto 2 - Processamento de Imagens\PI\dist\LaboratorioProcessamentoImagens.exe"
```

### Projeto 1 (Computação Gráfica):
```powershell
python ".\Projeto 1 - Computação Gráfica\Projeto_CG_Final\main_menu.py"
```

---

## 🛠️ Tecnologias e Bibliotecas
- **Linguagem**: Python 3.10+
- **GUI**: Tkinter / TTK
- **Processamento Numérico e Científico**: NumPy, SciPy (Delaunay), Pillow
- **Formatos NetPBM**: Leitura e escrita nativa para `.pgm` (P2/P5) e `.pbm` (P1/P4)
