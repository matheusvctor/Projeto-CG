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
│       │   └── LaboratorioProcessamentoImagens.exe # Executável standalone independente
│       ├── assets/                           # Imagens de teste (.pgm, .pbm, .png, .jpg)
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
- **Leitor Universal**: Suporte a NetPBM (`.pgm`, `.pbm`) e formatos comuns (`.png`, `.jpg`, `.jpeg`, `.bmp`).

### ◈ Projeto 1 - Computação Gráfica (Unidade 1)
- **Questão 1**: Rasterização de primitivas (DDA, Bresenham) e transformações geométricas 2D.
- **Questão 2**: Algoritmos de recorte de retas (**Cohen-Sutherland**) e recorte de polígonos (**Sutherland-Hodgman**).
- **Questão 3**: Modelagem tridimensional, rotações espaciais e projeção de viewport.
- **Questão 4**: Manipulação e transformações espaciais sobre matrizes de imagem PGM.

---

## 🚀 Como Executar

### Projeto de Processamento de Imagens:
```powershell
# Execução direta via Python:
python ".\Projeto - Processamento de Imagens\PI\executar_projeto.py"

# Ou via executável independente (.exe):
& ".\Projeto - Processamento de Imagens\PI\dist\LaboratorioProcessamentoImagens.exe"
```

### Projeto 1 (Unidade 1):
```powershell
python ".\Projeto 1 - Computação Gráfica\Projeto_CG_Final\main_menu.py"
```
