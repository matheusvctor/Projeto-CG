import tkinter as tk
from tkinter import filedialog
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import theme

from matrix_utils import scale_2d, translate_2d, rotate_2d, multiply_3x3
from image_utils import read_pgm, write_pgm_p5, apply_image_transformation

img_original_pixels = None
img_transformada_pixels = None
rows, cols = 0, 0

def mostrar(pixels, w, h, painel, temp_filename):
    """Converte a lista de pixels em imagem temporária e atualiza um painel Tkinter."""
    if pixels is None: return
    write_pgm_p5(temp_filename, w, h, pixels)
    img_tk = tk.PhotoImage(file=temp_filename)
    painel.config(image=img_tk, width=w, height=h)
    painel.image = img_tk

def atualizar_telas():
    mostrar(img_original_pixels, cols, rows, painel_original, "temp_orig.pgm")
    mostrar(img_transformada_pixels, cols, rows, painel_transformada, "temp_trans.pgm")

def carregar_imagem():
    """Lê um arquivo PGM do disco e o define como base para todas as operações."""
    global img_original_pixels, img_transformada_pixels, rows, cols
    caminho = filedialog.askopenfilename(filetypes=[("Imagens PGM", "*.pgm"), ("Todas", "*.*")])
    if caminho:
        w, h, maxv, pix = read_pgm(caminho)
        img_original_pixels = pix
        img_transformada_pixels = pix.copy()
        cols, rows = w, h
        atualizar_telas()

def resetar():
    """Restaura a imagem transformada para o estado original carregado."""
    global img_transformada_pixels
    if img_original_pixels is not None:
        img_transformada_pixels = img_original_pixels.copy()
        atualizar_telas()

def atualizar_inputs(event=None):
    """Troca dinamicamente os campos de entrada de acordo com a operação escolhida."""
    global inputs
    inputs.clear()
    for widget in frame_inputs.winfo_children():
        widget.destroy()

    op = operacao_var.get()
    if op == "Escala":
        criar_input("Fator de escala", "1")
    elif op == "Rotação":
        criar_input("Ângulo (graus)", "0")
    elif op == "Translação":
        criar_input("TX", "0")
        criar_input("TY", "0")
    elif op == "Cisalhamento":
        criar_input("Fator X", "0")
        criar_input("Fator Y", "0")
    elif op == "Reflexão":
        criar_input("Eixo (Digite X ou Y)", "X")

inputs = []

def criar_input(label, default):
    """Cria um campo simples para um parâmetro escalar da transformação atual."""
    tk.Label(frame_inputs, text=label, bg=theme.BG_APP, fg=theme.FG_TEXT).pack()
    entry = tk.Entry(frame_inputs, justify="center")
    entry.insert(0, default)
    entry.pack()
    inputs.append(entry)

def aplicar():
    """Monta a matriz da operação, recentra no meio da imagem e aplica a transformação."""
    global img_transformada_pixels
    if img_original_pixels is None: return

    op = operacao_var.get()
    M = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]

    try:
        if op == "Escala":
            s = float(inputs[0].get())
            M = scale_2d(s, s)
        elif op == "Rotação":
            ang = float(inputs[0].get())
            M = rotate_2d(ang)
        elif op == "Translação":
            tx = float(inputs[0].get())
            ty = float(inputs[1].get())
            M = translate_2d(tx, ty)
        elif op == "Cisalhamento":
            shx = float(inputs[0].get())
            shy = float(inputs[1].get())
            M = [[1.0, shx, 0.0],
                 [shy, 1.0, 0.0],
                 [0.0, 0.0, 1.0]]
        elif op == "Reflexão":
            eixo = inputs[0].get().strip().upper()
            if eixo == "Y":
                M = scale_2d(-1.0, 1.0)
            else:
                M = scale_2d(1.0, -1.0)

        cx, cy = cols / 2.0, rows / 2.0
        ida = translate_2d(-cx, -cy)
        volta = translate_2d(cx, cy)
        M_final = multiply_3x3(volta, multiply_3x3(M, ida))

        new_pix, new_w, new_h = apply_image_transformation(img_original_pixels, cols, rows, M_final)
        img_transformada_pixels = new_pix
        mostrar(img_transformada_pixels, new_w, new_h, painel_transformada, "temp_trans.pgm")

    except Exception as e:
        print("Erro nos valores:", e)

def cmd_como_calculamos():
    """Abre uma janela com o resumo matemático do pipeline de transformação da imagem."""
    janela = tk.Toplevel(root)
    janela.title("Como Calculamos - Imagens")
    janela.geometry("600x400")
    janela.configure(bg=theme.BG_PANEL)
    texto = """Cálculo Matemático - Transformações Afins em Imagens:

1. Matriz de Transformação:
As coordenadas de cada pixel formam um vetor [x, y, 1] que é 
multiplicado pela Matriz Homogênea (3x3) de transformação (Rotação, 
Escala, Translação, Reflexão ou Cisalhamento).

2. Bounding Box Dinâmico:
Para a imagem não ser cortada ao girar ou cisalhar, multiplicamos os 4 cantos
da imagem original pela matriz para descobrir a nova largura e 
altura (min_x, max_x, min_y, max_y) do "quadro espacial".

3. Mapeamento Inverso (Prevenção de Buracos):
Em vez de mapear a origem para o destino, varremos os pixels vazios
da nova imagem e multiplicamos a coordenada atual pela MATRIZ INVERSA 
(M^-1) calculada via Regra de Cramer. 
Se a coordenada resultante existir na imagem original, copiamos a cor."""
    tk.Label(janela, text=texto, justify="left", font=("Helvetica", 11), bg=theme.BG_PANEL, fg=theme.FG_TEXT).pack(padx=20, pady=20)

# ==========================================
# INTERFACE GRÁFICA (TEMA)
# ==========================================

root = tk.Tk()
root.title("Transformações Afins em Imagens PGM")
root.configure(bg=theme.BG_APP)

nav = tk.Frame(root, bg=theme.BG_PANEL)
nav.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
tk.Button(nav, text="◀ Voltar", command=root.destroy, bg=theme.ACCENT, fg="white", relief="flat").pack(side="left", padx=10, pady=5)

painel_original = tk.Label(root, text="Original", bg=theme.BG_CANVAS, fg=theme.FG_TEXT, width=40, height=20, highlightthickness=1, highlightbackground=theme.AXIS_COLOR)
painel_original.grid(row=1, column=0, padx=10, pady=10)

painel_transformada = tk.Label(root, text="Transformada", bg=theme.BG_CANVAS, fg=theme.FG_TEXT, width=40, height=20, highlightthickness=1, highlightbackground=theme.AXIS_COLOR)
painel_transformada.grid(row=1, column=1, padx=10, pady=10)

tk.Button(root, text="Carregar Imagem PGM", command=carregar_imagem, bg=theme.ACCENT, fg="white", font=theme.FONT_NORMAL)\
    .grid(row=2, column=0, columnspan=2, pady=5)

tk.Button(root, text="Resetar Imagem", command=resetar, bg=theme.DANGER, fg="white", font=theme.FONT_NORMAL)\
    .grid(row=3, column=0, columnspan=2, pady=5)

operacao_var = tk.StringVar(value="Cisalhamento")
tk.Label(root, text="Operação:", bg=theme.BG_APP, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE).grid(row=4, column=0, columnspan=2, pady=(10,0))

menu = tk.OptionMenu(root, operacao_var, "Escala", "Rotação", "Translação", "Cisalhamento", "Reflexão", command=atualizar_inputs)
menu.config(bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_NORMAL)
menu.grid(row=5, column=0, columnspan=2)

frame_inputs = tk.Frame(root, bg=theme.BG_APP)
frame_inputs.grid(row=6, column=0, columnspan=2, pady=10)

tk.Button(root, text="Aplicar Algoritmo", command=aplicar, width=20, bg=theme.LINE_COLOR_3D_PROC, fg="white", font=theme.FONT_TITLE)\
    .grid(row=7, column=0, columnspan=2, pady=10)

tk.Button(root, text="Como Calculamos?", command=cmd_como_calculamos, width=20, bg=theme.ACCENT_HOVER, fg="white", font=theme.FONT_NORMAL)\
    .grid(row=8, column=0, columnspan=2, pady=5)

atualizar_inputs()
root.mainloop()
