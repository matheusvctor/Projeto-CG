#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
import sys

# Garante que o Python encontre o 'theme.py' na raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import theme

from core.cg_utils import (
    mat_mult, vec_mult, identity, translate3d, scale3d, 
    rotate_x, rotate_y, rotate_z, reflect_x3d, reflect_y3d, reflect_z3d, shear3d,
    projection_isometric, sutherland_hodgman_clip, reta_dda
)

# ==========================================
# DEFINIÇÃO DO OBJETO 3D (Cubo na Origem 0,0,0)
# ==========================================
vertices_originais = [
    [0, 0, 0, 1], [4, 0, 0, 1], [4, 4, 0, 1], [0, 4, 0, 1],
    [0, 0, 4, 1], [4, 0, 4, 1], [4, 4, 4, 1], [0, 4, 4, 1]
]
ares = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (0, 3, 7, 4), (1, 2, 6, 5)]

Wxmin, Wxmax, Wymin, Wymax = -15, 20, -15, 20
Vxmin, Vymin = 50, 50
Vxmax, Vymax = 350, 350

def map_window_to_viewport_rect(wx, wy, vxmin, vxmax, vymin, vymax):
    """Mapeia um ponto 2D projetado da janela do mundo para o retângulo da viewport."""
    sx = (vxmax - vxmin) / (Wxmax - Wxmin) if (Wxmax - Wxmin) != 0 else 1.0
    sy = (vymax - vymin) / (Wymax - Wymin) if (Wymax - Wymin) != 0 else 1.0
    vx = vxmin + (wx - Wxmin) * sx
    vy = vymin + (wy - Wymin) * sy
    return [int(round(vx)), int(round(vy))]

world_transform_matrix = identity()
vp_transform_matrix = identity()
historico_matrizes = [identity()]

canvas = None
root = None
text_log = None # Variável para o Terminal de Logs
CANVAS_PADDING = 40
CANVAS_TOP_OFFSET = 80

def get_viewport_dimensions():
    """Retorna largura e altura atuais da viewport em coordenadas de tela."""
    return Vxmax - Vxmin, Vymax - Vymin

def viewport_to_canvas_coords(vx, vy, offset_x, viewport_height):
    """Converte coordenadas da viewport para pixels do canvas do Tkinter."""
    x = offset_x + (vx - Vxmin)
    y = CANVAS_TOP_OFFSET + (viewport_height - (vy - Vymin))
    return int(round(x)), int(round(y))

# ==========================================
# LÓGICA DO LOG DE MATRIZES 3D
# ==========================================
def fmt_matriz(M):
    """Formata a matriz 4x4 em texto alinhado."""
    def row(r): return "| " + "  ".join(f"{v:6.2f}" for v in r) + " |"
    return "\n".join(row(r) for r in M)

def log_operacao(label, M):
    """Imprime a matriz no console/log da tela."""
    if text_log is None: return
    text_log.config(state=tk.NORMAL)
    text_log.insert(tk.END, label + ":\n" + fmt_matriz(M) + "\n" + "-"*34 + "\n")
    text_log.see(tk.END)
    text_log.config(state=tk.DISABLED)

# ==========================================
# DESENHO DA CENA
# ==========================================
def draw_3d_axes(cv, offset_x, vp_h):
    m_proj = projection_isometric()
    pts_mundo = {"O": [0,0,0,1], "X": [15,0,0,1], "Y": [0,15,0,1], "Z": [0,0,15,1]}
    pts_tela = {}
    for nome, pt in pts_mundo.items():
        proj = vec_mult(m_proj, pt)
        vp_pt = map_window_to_viewport_rect(proj[0], proj[1], Vxmin, Vxmax, Vymin, Vymax)
        cx, cy = viewport_to_canvas_coords(vp_pt[0], vp_pt[1], offset_x, vp_h)
        pts_tela[nome] = (cx, cy)
    
    ox, oy = pts_tela["O"]
    reta_dda(cv, ox, oy, pts_tela["X"][0], pts_tela["X"][1], cor="#d63031")
    cv.create_text(pts_tela["X"][0] + 10, pts_tela["X"][1], text="X", fill="#d63031", font=("Segoe UI", 10, "bold"))
    reta_dda(cv, ox, oy, pts_tela["Y"][0], pts_tela["Y"][1], cor="#00b894")
    cv.create_text(pts_tela["Y"][0], pts_tela["Y"][1] - 10, text="Y", fill="#00b894", font=("Segoe UI", 10, "bold"))
    reta_dda(cv, ox, oy, pts_tela["Z"][0], pts_tela["Z"][1], cor="#0984e3")
    cv.create_text(pts_tela["Z"][0] - 10, pts_tela["Z"][1], text="Z", fill="#0984e3", font=("Segoe UI", 10, "bold"))

def draw_original_view(cv, offset_x, vp_h):
    m_proj = projection_isometric()
    for aresta in ares:
        v1_t = vec_mult(world_transform_matrix, vertices_originais[aresta[0]])
        v2_t = vec_mult(world_transform_matrix, vertices_originais[aresta[1]])
        v1_proj = vec_mult(m_proj, v1_t)
        v2_proj = vec_mult(m_proj, v2_t)
        
        p1 = map_window_to_viewport_rect(v1_proj[0], v1_proj[1], Vxmin, Vxmax, Vymin, Vymax)
        p2 = map_window_to_viewport_rect(v2_proj[0], v2_proj[1], Vxmin, Vxmax, Vymin, Vymax)
        x1, y1 = viewport_to_canvas_coords(p1[0], p1[1], offset_x, vp_h)
        x2, y2 = viewport_to_canvas_coords(p2[0], p2[1], offset_x, vp_h)
        reta_dda(cv, x1, y1, x2, y2, theme.LINE_COLOR_3D)

def draw_processed_view(cv, offset_x, vp_w, vp_h):
    pv_rect = (Vxmin, Vxmin + vp_w, Vymin, Vymin + vp_h)
    m_proj = projection_isometric()
    
    for face in faces:
        poly_mapped = []
        for vi in face:
            v_t = vec_mult(vp_transform_matrix, vertices_originais[vi])
            v_proj = vec_mult(m_proj, v_t)
            v_m = map_window_to_viewport_rect(v_proj[0], v_proj[1], pv_rect[0], pv_rect[1], pv_rect[2], pv_rect[3])
            poly_mapped.append(v_m)

        poly_clipped = sutherland_hodgman_clip(poly_mapped, pv_rect)
        if len(poly_clipped) > 2:
            for i in range(len(poly_clipped)):
                p1, p2 = poly_clipped[i], poly_clipped[(i + 1) % len(poly_clipped)]
                x1, y1 = viewport_to_canvas_coords(p1[0], p1[1], offset_x, vp_h)
                x2, y2 = viewport_to_canvas_coords(p2[0], p2[1], offset_x, vp_h)
                reta_dda(cv, x1, y1, x2, y2, theme.LINE_COLOR_3D_PROC)

def draw_scene():
    if canvas is None: return
    vp_w, vp_h = get_viewport_dimensions()
    
    OFFSET_ORIGINAL = CANVAS_PADDING
    OFFSET_PROCESSED = OFFSET_ORIGINAL + vp_w + CANVAS_PADDING
    needed_w = OFFSET_PROCESSED + vp_w + CANVAS_PADDING
    needed_h = CANVAS_TOP_OFFSET + vp_h + CANVAS_PADDING
    
    canvas.configure(scrollregion=(0, 0, needed_w, needed_h))
    canvas.delete("all")

    canvas.create_text(OFFSET_ORIGINAL + vp_w / 2, 30, text="Mundo 3D (Rascunho de Eixos)", fill=theme.FG_TEXT, font=theme.FONT_TITLE)
    canvas.create_rectangle(OFFSET_ORIGINAL, CANVAS_TOP_OFFSET, OFFSET_ORIGINAL + vp_w, CANVAS_TOP_OFFSET + vp_h, outline=theme.AXIS_COLOR, fill="#ffffff")
    draw_3d_axes(canvas, OFFSET_ORIGINAL, vp_h)
    draw_original_view(canvas, OFFSET_ORIGINAL, vp_h)

    canvas.create_text(OFFSET_PROCESSED + vp_w / 2, 30, text=f"Viewport Renderizada (Z+) [{vp_w}x{vp_h}]", fill=theme.FG_TEXT, font=theme.FONT_TITLE)
    p_l, p_t = OFFSET_PROCESSED, CANVAS_TOP_OFFSET
    p_r, p_b = p_l + vp_w, p_t + vp_h
    canvas.create_rectangle(p_l, p_t, p_r, p_b, outline=theme.AXIS_COLOR, fill=theme.BG_CANVAS)
    draw_processed_view(canvas, OFFSET_PROCESSED, vp_w, vp_h)

# ==========================================
# TRANSFORMAÇÕES
# ==========================================
def calcular_centroide_atual():
    cx, cy, cz = 0.0, 0.0, 0.0
    for v in vertices_originais:
        v_t = vec_mult(world_transform_matrix, v)
        cx += v_t[0]; cy += v_t[1]; cz += v_t[2]
    return cx/8.0, cy/8.0, cz/8.0

def aplicar_transformacao_composta(matriz_op, usar_centroide=True, label="Operação"):
    global world_transform_matrix, historico_matrizes, vp_transform_matrix
    
    log_operacao(label, matriz_op)
    
    if usar_centroide:
        cx, cy, cz = calcular_centroide_atual()
        ida, volta = translate3d(-cx, -cy, -cz), translate3d(cx, cy, cz)
        matriz_composta = mat_mult(volta, mat_mult(matriz_op, ida))
    else:
        matriz_composta = matriz_op
        
    nova_m = mat_mult(matriz_composta, world_transform_matrix)
    historico_matrizes.append(nova_m)
    world_transform_matrix = nova_m
    # Sincronização automática em tempo real com a Viewport
    vp_transform_matrix = [row[:] for row in world_transform_matrix]
    listbox.insert(tk.END, f"★ {label}")
    listbox.yview(tk.END)
    draw_scene()

def cmd_enviar_viewport():
    global vp_transform_matrix
    vp_transform_matrix = [row[:] for row in world_transform_matrix]
    listbox.insert(tk.END, f"➔ PROJETADO NA VIEWPORT")
    listbox.yview(tk.END)
    draw_scene()

def cmd_atualizar_vp():
    global Vxmin, Vymin, Vxmax, Vymax
    try:
        xmin = int(ent_vxmin.get())
        ymin = int(ent_vymin.get())
        xmax = int(ent_vxmax.get())
        ymax = int(ent_vymax.get())
        
        if xmin < 0 or ymin < 0 or xmax < 0 or ymax < 0:
            messagebox.showerror("Erro de Domínio", "Nenhum valor pode ser negativo (Regra Z+).")
            return
        if xmin >= xmax or ymin >= ymax:
            messagebox.showerror("Erro Lógico", "Os valores de 'Max' devem ser maiores que 'Min'.")
            return
            
        Vxmin, Vymin, Vxmax, Vymax = xmin, ymin, xmax, ymax
        draw_scene()
        listbox.insert(tk.END, f"◱ VP: ({xmin},{ymin}) a ({xmax},{ymax})")
        listbox.yview(tk.END)
    except ValueError: pass

def cmd_desfazer():
    global world_transform_matrix, vp_transform_matrix, historico_matrizes
    if len(historico_matrizes) > 1:
        historico_matrizes.pop()
        world_transform_matrix = historico_matrizes[-1]
        vp_transform_matrix = [row[:] for row in world_transform_matrix]
        listbox.insert(tk.END, "↩ Ação desfeita")
        listbox.yview(tk.END)
        draw_scene()
    else:
        messagebox.showinfo("Histórico", "O objeto já está no seu estado original!")

def cmd_reset():
    global world_transform_matrix, vp_transform_matrix, historico_matrizes
    world_transform_matrix = identity()
    vp_transform_matrix = identity()
    historico_matrizes = [identity()]
    listbox.delete(0, tk.END)
    if text_log:
        text_log.config(state=tk.NORMAL)
        text_log.delete("1.0", tk.END)
        text_log.config(state=tk.DISABLED)
    draw_scene()


def cmd_como_calculamos():
    janela = tk.Toplevel(root)
    janela.title("Como Calculamos - Ambiente 3D")
    janela.geometry("600x480")
    janela.configure(bg=theme.BG_PANEL)
    texto = """Cálculo Matemático - Transformações 3D e Pipeline:

1. Transformação Composta no Eixo vs Origem:
As operações acontecem primeiro no MUNDO. Para Rotação e Escala, 
calculamos o Centroide (C) e aplicamos: M_final = T(C) * Operacao * T(-C).

2. Viewport Estática:
O objeto só é mapeado para a Viewport quando o usuário manda.
Isso clona a matriz do mundo e projeta com rotações em Y(45°) e X(-35,264°).
Coordenada projetada Vx = Vxmin + (Wx - Wxmin) * ScaleX.
Ao final, aplicamos int(round()) para garantir o Z+ e recortamos."""
    tk.Label(janela, text=texto, justify="left", font=("Helvetica", 11), bg=theme.BG_PANEL, fg=theme.FG_TEXT).pack(padx=20, pady=20)

def setup_tkinter():
    global root, canvas, listbox, text_log
    global ent_vxmin, ent_vymin, ent_vxmax, ent_vymax
    global ent_tx, ent_ty, ent_tz, ent_sx, ent_sy, ent_sz, ent_rx, ent_ry, ent_rz
    global ent_shxy, ent_shxz, ent_shyz

    root = tk.Tk()
    root.title("Ambiente de Modelagem 3D UEPB - Isométrico Puro")
    root.geometry("1200x850")
    root.configure(bg=theme.BG_APP)

    main_frm = tk.Frame(root, bg=theme.BG_APP)
    main_frm.pack(fill="both", expand=True)
    
    nav = tk.Frame(main_frm, bg=theme.BG_PANEL)
    nav = tk.Frame(main_frm, bg=theme.BG_HEADER, height=44)
    nav.pack(fill="x", padx=0, pady=(0, 4))
    theme.make_btn(nav, "◀ Voltar", root.destroy, "primary", padx=10, pady=4).pack(side="left", padx=10, pady=4)
    tk.Label(nav, text="Modelagem & Transformações 3D (Regra Z+)", bg=theme.BG_HEADER, fg=theme.CYAN_GLOW, font=theme.FONT_TITLE).pack(side="left", padx=10)
    theme.make_btn_insp(nav, lambda: ("mod_3d/Questao3/Questao3..py", 35)).pack(side="right", padx=10, pady=4)

    controls = tk.Frame(main_frm, bg=theme.BG_PANEL, width=320, pady=8)
    controls.pack(side="left", fill="y")
    controls.pack_propagate(False)

    # Frame da Direita (Canvas de desenho + Log embaixo)
    right_frm = tk.Frame(main_frm, bg=theme.BG_CANVAS)
    right_frm.pack(side="right", fill="both", expand=True)

    canvas_frm = tk.Frame(right_frm, bg=theme.BG_CANVAS)
    canvas_frm.pack(side="top", fill="both", expand=True)
    canvas = tk.Canvas(canvas_frm, bg=theme.BG_CANVAS, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Painel de Log inferior
    log_frm = tk.Frame(right_frm, bg=theme.BG_PANEL, height=130)
    log_frm.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
    tk.Label(log_frm, text="Log de Matrizes & Transformações 3D:", bg=theme.BG_PANEL, fg=theme.CYAN_GLOW, font=theme.FONT_SUBTITLE).pack(anchor="w", padx=8, pady=(4, 0))
    
    scroll = tk.Scrollbar(log_frm)
    scroll.pack(side="right", fill="y")
    text_log = tk.Text(log_frm, height=6, bg=theme.BG_CANVAS, fg=theme.CYAN_GLOW, insertbackground="#dddddd", font=theme.FONT_CODE, yscrollcommand=scroll.set, relief="flat")
    text_log.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 4))
    scroll.config(command=text_log.yview)
    text_log.config(state=tk.DISABLED)

    # Painel Esquerdo
    tk.Label(controls, text="PAINEL DE CONTROLE 3D", font=theme.FONT_SUBTITLE, bg=theme.BG_PANEL, fg=theme.CYAN_GLOW).pack(pady=(0, 4))

    f_vp = tk.LabelFrame(controls, text="Viewport (Regra Z+)", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE)
    f_vp.pack(fill="x", pady=2, padx=8)
    
    f_vp_l1 = tk.Frame(f_vp, bg=theme.BG_PANEL)
    f_vp_l1.pack(fill="x", pady=1)
    tk.Label(f_vp_l1, text="Xmin:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side="left", padx=2)
    ent_vxmin = tk.Entry(f_vp_l1, width=4, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_vxmin.insert(0, str(Vxmin)); ent_vxmin.pack(side="left", padx=2)
    tk.Label(f_vp_l1, text="Ymin:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side="left", padx=2)
    ent_vymin = tk.Entry(f_vp_l1, width=4, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_vymin.insert(0, str(Vymin)); ent_vymin.pack(side="left", padx=2)
    
    f_vp_l2 = tk.Frame(f_vp, bg=theme.BG_PANEL)
    f_vp_l2.pack(fill="x", pady=1)
    tk.Label(f_vp_l2, text="Xmax:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side="left", padx=2)
    ent_vxmax = tk.Entry(f_vp_l2, width=4, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_vxmax.insert(0, str(Vxmax)); ent_vxmax.pack(side="left", padx=2)
    tk.Label(f_vp_l2, text="Ymax:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side="left", padx=2)
    ent_vymax = tk.Entry(f_vp_l2, width=4, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_vymax.insert(0, str(Vymax)); ent_vymax.pack(side="left", padx=2)
    
    theme.make_btn(f_vp, "📐 Redimensionar VP", cmd_atualizar_vp, "secondary", padx=6, pady=2).pack(pady=3)

    f_t = tk.LabelFrame(controls, text="Translação (X, Y, Z)", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE)
    f_t.pack(fill="x", pady=2, padx=8)
    ent_tx = tk.Entry(f_t, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_tx.pack(side="left", padx=2, pady=2)
    ent_ty = tk.Entry(f_t, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_ty.pack(side="left", padx=2, pady=2)
    ent_tz = tk.Entry(f_t, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_tz.pack(side="left", padx=2, pady=2)
    theme.make_btn(f_t, "✥ Mover", lambda: aplicar_transformacao_composta(translate3d(float(ent_tx.get() or 0), float(ent_ty.get() or 0), float(ent_tz.get() or 0)), label="Translação T"), "secondary", padx=6, pady=2).pack(side="right", padx=2)

    f_s = tk.LabelFrame(controls, text="Escala (X, Y, Z)", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE)
    f_s.pack(fill="x", pady=2, padx=8)
    ent_sx = tk.Entry(f_s, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_sx.insert(0,"1"); ent_sx.pack(side="left", padx=2, pady=2)
    ent_sy = tk.Entry(f_s, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_sy.insert(0,"1"); ent_sy.pack(side="left", padx=2, pady=2)
    ent_sz = tk.Entry(f_s, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_sz.insert(0,"1"); ent_sz.pack(side="left", padx=2, pady=2)
    theme.make_btn(f_s, "⤢ Escalar", lambda: aplicar_transformacao_composta(scale3d(float(ent_sx.get() or 1), float(ent_sy.get() or 1), float(ent_sz.get() or 1)), label="Escala S"), "secondary", padx=6, pady=2).pack(side="right", padx=2)

    f_r = tk.LabelFrame(controls, text="Rotação (Graus)", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE)
    f_r.pack(fill="x", pady=2, padx=8)
    ent_rx = tk.Entry(f_r, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_rx.grid(row=0, column=0, padx=2, pady=2)
    theme.make_btn(f_r, "↻ X", lambda: aplicar_transformacao_composta(rotate_x(float(ent_rx.get() or 0)), label="Rotação X"), "secondary", padx=4, pady=1).grid(row=0, column=1, padx=2, pady=2)
    ent_ry = tk.Entry(f_r, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_ry.grid(row=0, column=2, padx=2, pady=2)
    theme.make_btn(f_r, "↻ Y", lambda: aplicar_transformacao_composta(rotate_y(float(ent_ry.get() or 0)), label="Rotação Y"), "secondary", padx=4, pady=1).grid(row=0, column=3, padx=2, pady=2)
    ent_rz = tk.Entry(f_r, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_rz.grid(row=1, column=0, padx=2, pady=2)
    theme.make_btn(f_r, "↻ Z", lambda: aplicar_transformacao_composta(rotate_z(float(ent_rz.get() or 0)), label="Rotação Z"), "secondary", padx=4, pady=1).grid(row=1, column=1, padx=2, pady=2)

    f_ref = tk.LabelFrame(controls, text="Reflexão (Espelhar)", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE)
    f_ref.pack(fill="x", pady=2, padx=8)
    theme.make_btn(f_ref, "🪞 X", lambda: aplicar_transformacao_composta(reflect_x3d(), False, label="Reflexão X"), "secondary", padx=6, pady=1).pack(side="left", padx=2, pady=2, expand=True, fill="x")
    theme.make_btn(f_ref, "🪞 Y", lambda: aplicar_transformacao_composta(reflect_y3d(), False, label="Reflexão Y"), "secondary", padx=6, pady=1).pack(side="left", padx=2, pady=2, expand=True, fill="x")
    theme.make_btn(f_ref, "🪞 Z", lambda: aplicar_transformacao_composta(reflect_z3d(), False, label="Reflexão Z"), "secondary", padx=6, pady=1).pack(side="left", padx=2, pady=2, expand=True, fill="x")

    f_sh = tk.LabelFrame(controls, text="Cisalhamento (XY, XZ, YZ)", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE)
    f_sh.pack(fill="x", pady=2, padx=8)
    ent_shxy = tk.Entry(f_sh, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_shxy.insert(0,"0"); ent_shxy.pack(side="left", padx=2, pady=2)
    ent_shxz = tk.Entry(f_sh, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_shxz.insert(0,"0"); ent_shxz.pack(side="left", padx=2, pady=2)
    ent_shyz = tk.Entry(f_sh, width=3, bg=theme.BG_INPUT, fg=theme.FG_TEXT, relief="flat"); ent_shyz.insert(0,"0"); ent_shyz.pack(side="left", padx=2, pady=2)
    tk.Label(controls, text="● Sincronização em Tempo Real (Ativa)", font=theme.FONT_NORMAL, bg=theme.BG_PANEL, fg=theme.CYAN_GLOW).pack(pady=(4, 2))

    listbox = tk.Listbox(controls, height=4, bg=theme.BG_INPUT, fg=theme.FG_TEXT, font=theme.FONT_CODE, relief="flat", highlightthickness=0)
    listbox.pack(fill="x", pady=2, padx=8)

    theme.make_btn(controls, "↶ Desfazer no Mundo", cmd_desfazer, "warning", padx=8, pady=3).pack(pady=2, fill="x", padx=8)
    theme.make_btn(controls, "↺ Resetar Tudo", cmd_reset, "danger", padx=8, pady=3).pack(pady=2, fill="x", padx=8)
    theme.make_btn(controls, "❓ Como Calculamos?", cmd_como_calculamos, "primary", padx=8, pady=3).pack(pady=2, fill="x", padx=8)

    draw_scene()

if __name__ == "__main__":
    setup_tkinter()
    root.mainloop()