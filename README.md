# Projeto de Computação Gráfica — Processamento Digital de Imagens

Ambiente integrado com implementações de algoritmos fundamentais e avançados de **Computação Gráfica e Processamento Digital de Imagens (PDI)** desenvolvidos em Python.

---

## 📂 Estrutura do Repositório

```
Computacao-grafica-main/
│
└── Projeto - Processamento de Imagens/       # Projeto de Computação Gráfica
    └── PI/
        ├── executar_projeto.py               # Ponto de entrada do Projeto
        ├── dist/
        │   └── LaboratorioProcessamentoImagens.exe # Executável standalone independente
        ├── assets/                           # Imagens de teste (.pgm, .pbm, etc.)
        └── src/laboratorio_imagens/          # Módulos matemáticos e Interface com Menu Lateral
```

---

## 🔬 Destaques dos Módulos

- **Interface Moderna com Sidebar**: Navegação lateral dinâmica sem abas horizontais tradicionais.
- **Filtros Espaciais**: Média, Mediana, Laplaciano Passa-Altas, Roberts, Roberts Cruzado, Prewitt, Sobel (com componentes nos eixos e magnitude) e High-Boost.
- **Operações Pixel a Pixel**: Soma, Subtração, Multiplicação, Divisão, AND, OR, XOR e NOT com controle de truncamento/normalização.
- **Intensidade & Histograma**: Negativo, Gamma ($\gamma$), Logaritmo, Função Sigmóide, Faixa Dinâmica, Transferência Linear e Equalização de Histograma via CDF com visualizador e zoom de apresentação.
- **Morfologia Matemática**: Erosão, Dilatação, Abertura, Fechamento, Contornos, Gradiente Morfológico, Top/Bottom-Hat e Hit-or-Miss (binário e tons de cinza).
- **Transformações Geométricas**: Escala, Translação, Rotação (mapeamento inverso cartesiano), Reflexão e Cisalhamento.
- **Deformação e Morfismo Temporal**: Triangulação de Delaunay e interpolação afim por triângulos ($t \in [0, 1]$) com exportação para GIF animado e frames.
- **Inspetor Matricial de Pixels**: Visualização em tempo real de matrizes de pixels ($10\times10$ até $40\times40$).

---

## 🚀 Como Executar

### Execução Direta via Python:
```powershell
python ".\Projeto - Processamento de Imagens\PI\executar_projeto.py"
```

### Execução via Binário Standalone (.exe):
Basta executar diretamente o arquivo:
```powershell
& ".\Projeto - Processamento de Imagens\PI\dist\LaboratorioProcessamentoImagens.exe"
```

---

## 🛠️ Tecnologias e Bibliotecas
- **Linguagem**: Python 3.10+
- **GUI**: Tkinter / TTK (Tema customizado Obsidian & Cyan)
- **Processamento Numérico e Científico**: NumPy, SciPy (Delaunay), Pillow
- **Formatos NetPBM**: Leitura e escrita nativa para `.pgm` (P2/P5) e `.pbm` (P1/P4)
