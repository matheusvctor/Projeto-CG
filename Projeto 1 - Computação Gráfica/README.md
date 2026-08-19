# Projeto 1 - Computação Gráfica (Unidade 1)

Ambiente integrado em Python/Tkinter com a implementação de todos os algoritmos fundamentais de rasterização de primitivas, recortes 2D, modelagem 3D, transformações homogêneas e splines da Unidade 1.

---

## 🔬 Módulos Implementados

### ◈ Questão 1 & 5 — Primitivas, Cônicas e Splines de Bézier
- **Segmentos de Reta**: Algoritmos **DDA** e **Ponto Médio (Bresenham)** para todos os 8 oitantes do plano cartesiano ($|m| \le 1$ e $|m| > 1$).
- **Circunferências**: Métodos da **Equação Explícita (Polinomial)**, **Parametrização Trigonométrica** e **Ponto Médio com Simetria de 8 Oitantes**.
- **Elipse por Varredura**: Algoritmo do **Ponto Médio** com separação analítica em Região 1 ($\frac{dy}{dx} > -1$) e Região 2 ($\frac{dy}{dx} < -1$).
- **Seções Cônicas**: Varredura e classificação por discriminante para **Parábolas** e **Hipérboles**.
- **Splines de Bézier Cúbicas (Q5)**: Curvas com 4 pontos de controle via polinômios de Bernstein:
  $$P(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3$$

### ◈ Transformações Homogêneas 2D & Composição (Q1)
- **Transformações com Pivô no Centro**: Rotação e Escala aplicadas em torno do baricentro geométrico do objeto ($M = T(x_c, y_c) \cdot R(\theta) \cdot T(-x_c, -y_c)$), garantindo que o objeto gire no próprio lugar sem transladar para fora da posição.
- **Composição de Transformações**: Pipeline sequencial de multiplicação matricial acumulada ($M_{\text{total}} = M_n \cdot M_{n-1} \dots M_1$), permitindo encadear translações, rotações, escalas e cisalhamentos em uma única matriz aplicada diretamente.

### ◈ Questão 2 — Algoritmos de Recorte de Janela
- **Recorte de Linhas (Cohen-Sutherland)**: Códigos de região (*Outcodes* de 4 bits: `TOP`, `BOTTOM`, `RIGHT`, `LEFT`), rejeição/aceitação trivial e cálculo das interseções nas 4 bordas.
- **Animação Contínua**: Linha com comprimento superior à diagonal da janela girando em sentido horário no centro do viewport com recorte dinâmico a cada quadro.
- **Recorte de Polígonos (Sutherland-Hodgman)**: Pipeline completo contra as 4 bordas com rastreamento visual das regras (*dentro $\to$ dentro*, *fora $\to$ dentro*, *dentro $\to$ fora*, *fora $\to$ fora*).

### ◈ Questão 3 — Modelagem 3D, Projeção Isométrica & Viewport
- **Transformações 3D**: Translação, Rotação em $X, Y, Z$, Escala, Cisalhamento 3D e Reflexões espaciais.
- **Projeção Paralela Isométrica**: Projeção ortográfica isométrica sobre matriz 3D com mapeamento da **Janela do Mundo $\to$ Viewport**.

### ◈ Questão 4 — Transformações Afins em Imagens PGM
- **Operadores Geométricos**: Escala, Rotação, Translação, Cisalhamento e Reflexão sobre imagens PGM (`.pgm`).
- **Mapeamento Inverso (Inverse Mapping)**: Prevenção de furos/buracos por varredura da imagem de saída com matriz inversa $T^{-1}$.

---

## 🛠️ Correções e Aprimoramentos Técnicos

- **Ativação Real de Pixels Discretos**: A função de plotagem gráfica foi corrigida para desenhar exatamente **1 pixel físico nítido** por coordenada calculada (eliminando bordas que geravam 4 pixels duplicados).
- **Rotação com Pivô Central**: A rotação 2D agora calcula automaticamente o centro geométrico $(x_c, y_c)$, preservando o objeto na sua posição espacial correta.
- **Composição Matricial 2D**: Adicionada ferramenta dedicada para compor e executar cadeias de matrizes homogêneas $3\times3$.

---

## 🚀 Como Executar

### Via Script Python:
```powershell
python ".\Projeto 1 - Computação Gráfica\Projeto_CG_Final\main_menu.py"
```

### Via Executável Standalone (.exe):
```powershell
& ".\Projeto 1 - Computação Gráfica\Projeto_CG_Final\dist\Projeto1_ComputacaoGrafica.exe"
```