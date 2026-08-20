"""
Interface da Questão 2 - Recorte de Polígonos por Weiler-Atherton.
Suporta polígonos côncavos, janelas de recorte e múltiplos sub-polígonos resultantes.
"""

from __future__ import annotations

import math
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

_dir_modulo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_dir_raiz = os.path.abspath(os.path.join(_dir_modulo, ".."))
if _dir_modulo not in sys.path:
    sys.path.insert(0, _dir_modulo)
if _dir_raiz not in sys.path:
    sys.path.insert(0, _dir_raiz)

import theme
from core.cg_utils import QuadroDesenho, Viewport, normalizar_janela, weiler_atherton_clip_trace

Point = tuple[float, float]


class AppWeilerAtherton:
    def __init__(self, root, on_back=None):
        """Interface para recortar polígonos côncavos via Weiler-Atherton e acompanhar o trace."""
        self.root = root
        self.on_back = on_back
        self.root.title("Questão 2 — Recorte de Polígonos de Weiler-Atherton")
        self.root.configure(bg=theme.BG_APP)
        theme.configure_ttk_styles(root)

        self.zoom = tk.IntVar(value=3)
        self.vertex_x = tk.StringVar(value="0")
        self.vertex_y = tk.StringVar(value="0")
        self.vertices_text = tk.StringVar()
        
        # Janela de recorte padrão
        self.xmin = tk.DoubleVar(value=-30)
        self.ymin = tk.DoubleVar(value=-25)
        self.xmax = tk.DoubleVar(value=40)
        self.ymax = tk.DoubleVar(value=35)
        
        self.show_vertex_markers_var = tk.BooleanVar(value=True)
        self.show_vertex_values_var = tk.BooleanVar(value=True)
        self.show_intersections_var = tk.BooleanVar(value=True)
        self.interactive_draw_mode = False

        self.status_var = tk.StringVar(
            value="Adicione pontos pelo formulário, clique na tela para desenhar ou carregue um exemplo côncavo."
        )

        self._last_result = None
        self._build_ui(root)
        self.carregar_exemplo_concavo()

    def _build_ui(self, root):
        controls = tk.Frame(root, bg=theme.BG_PANEL, padx=10, pady=8)
        controls.pack(fill=tk.X)

        if callable(self.on_back):
            theme.make_btn(controls, "◀ Voltar", self.on_back, "primary", padx=10, pady=4).pack(side=tk.LEFT, padx=(0, 10))

        controls_inner = ttk.Frame(controls)
        controls_inner.pack(side=tk.LEFT, fill=tk.X, expand=True)
        controls_inner.columnconfigure(0, weight=1)
        controls_inner.columnconfigure(1, weight=0)
        controls_inner.columnconfigure(2, weight=0)

        # Card 1: Polígono de Entrada
        polygon_frame = ttk.LabelFrame(controls_inner, text="Polígono Sujeito (Suporta Côncavos)")
        polygon_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        polygon_frame.columnconfigure(5, weight=1)
        
        ttk.Label(polygon_frame, text="Vértices (x,y; x,y; ...):").grid(row=0, column=0, sticky="w", padx=8, pady=(4, 2))
        ttk.Entry(polygon_frame, textvariable=self.vertices_text).grid(row=1, column=0, columnspan=6, sticky="ew", padx=8)

        ttk.Label(polygon_frame, text="X").grid(row=2, column=0, sticky="w", padx=(8, 2), pady=(4, 2))
        ttk.Entry(polygon_frame, textvariable=self.vertex_x, width=6).grid(row=3, column=0, sticky="w", padx=(8, 2), pady=(0, 6))
        ttk.Label(polygon_frame, text="Y").grid(row=2, column=1, sticky="w", padx=2, pady=(4, 2))
        ttk.Entry(polygon_frame, textvariable=self.vertex_y, width=6).grid(row=3, column=1, sticky="w", padx=2, pady=(0, 6))
        
        theme.make_btn(polygon_frame, "➕ Ponto", self.add_polygon_point, "secondary", padx=6, pady=2).grid(row=3, column=2, sticky="w", padx=(6, 2), pady=(0, 6))
        theme.make_btn(polygon_frame, "➖ Remover", self.remove_last_polygon_point, "secondary", padx=6, pady=2).grid(row=3, column=3, sticky="w", padx=2, pady=(0, 6))
        self.draw_button = theme.make_btn(polygon_frame, "✏ Desenhar na Tela", self.toggle_draw_mode, "primary", padx=8, pady=2)
        self.draw_button.grid(row=3, column=4, sticky="w", padx=2, pady=(0, 6))

        # Card 2: Janela de Recorte
        window_frame = ttk.LabelFrame(controls_inner, text="Janela de Recorte")
        window_frame.grid(row=0, column=1, sticky="nw", padx=(0, 10))
        self._window_field(window_frame, "X min", self.xmin, 0, 0)
        self._window_field(window_frame, "Y min", self.ymin, 0, 1)
        self._window_field(window_frame, "X max", self.xmax, 1, 0)
        self._window_field(window_frame, "Y max", self.ymax, 1, 1)

        # Card 3: Ações e Visualização
        options_frame = ttk.LabelFrame(controls_inner, text="Ações & Exemplos")
        options_frame.grid(row=0, column=2, sticky="ne")
        
        f_zoom = tk.Frame(options_frame, bg=theme.BG_PANEL)
        f_zoom.pack(fill=tk.X, padx=6, pady=(4, 2))
        tk.Label(f_zoom, text="Zoom:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        zoom_box = ttk.Spinbox(f_zoom, from_=1, to=40, textvariable=self.zoom, width=4, command=self._on_zoom_change)
        zoom_box.pack(side=tk.RIGHT)
        zoom_box.bind("<Return>", lambda e: self._on_zoom_change())
        zoom_box.bind("<FocusOut>", lambda e: self._on_zoom_change())
        
        f_botoes = tk.Frame(options_frame, bg=theme.BG_PANEL)
        f_botoes.pack(fill=tk.X, padx=4, pady=(2, 4))
        
        theme.make_btn(f_botoes, "✂ Recortar (WA)", self.desenhar, "success", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        theme.make_btn(f_botoes, "⤢ Enquadrar", self.enquadrar, "primary", padx=8, pady=2).pack(side=tk.LEFT, padx=2)
        theme.make_btn(f_botoes, "📁 Ex. Côncavo U", self.carregar_exemplo_concavo, "secondary", padx=6, pady=2).pack(side=tk.LEFT, padx=2)
        theme.make_btn(f_botoes, "⭐ Estrela", self.carregar_exemplo_estrela, "secondary", padx=6, pady=2).pack(side=tk.LEFT, padx=2)
        theme.make_btn(f_botoes, "↺ Limpar", self.limpar, "danger", padx=6, pady=2).pack(side=tk.LEFT, padx=2)

        # Status Bar
        f_status = tk.Frame(root, bg=theme.BG_APP, padx=10, pady=4)
        f_status.pack(fill=tk.X)
        tk.Label(f_status, textvariable=self.status_var, font=theme.FONT_NORMAL, bg=theme.BG_APP, fg=theme.CYAN_GLOW).pack(anchor="w")

        # Corpo Principal (Canvas à esquerda, Log/Resumo à direita)
        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        plot_frame = ttk.Frame(body)
        plot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        plot_frame.rowconfigure(0, weight=1)
        plot_frame.columnconfigure(0, weight=1)

        self.vp = Viewport(920, 720, escala=self.zoom.get())
        self.canvas = tk.Canvas(plot_frame, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.quadro = QuadroDesenho(self.canvas, self.vp, usar_grade=True)
        self.quadro.set_redraw_callback(self._redesenhar)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_left_release, add="+")
        self.canvas.bind("<Button-3>", self._on_canvas_right_click, add="+")
        plot_frame.bind("<Configure>", lambda e: self.quadro.resize(e.width, e.height))

        # Painel Lateral com Notebook
        side = ttk.Frame(body)
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)
        side.rowconfigure(0, weight=1)

        nb = ttk.Notebook(side)
        nb.pack(fill=tk.BOTH, expand=True)

        frm_resumo = ttk.Frame(nb)
        frm_passos = ttk.Frame(nb)
        frm_ajuda = ttk.Frame(nb)

        nb.add(frm_resumo, text="Resumo")
        nb.add(frm_passos, text="Trace Passo a Passo")
        nb.add(frm_ajuda, text="Como Funciona?")

        # Resumo Text
        self.txt_resumo = tk.Text(frm_resumo, wrap="word", bg="#1e293b", fg="#f8fafc", font=theme.FONT_CODE, insertbackground="#ffffff")
        self.txt_resumo.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Passos Text
        self.txt_passos = tk.Text(frm_passos, wrap="word", bg="#050811", fg=theme.CYAN_GLOW, font=theme.FONT_CODE, insertbackground="#ffffff")
        self.txt_passos.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Ajuda Text
        self.txt_ajuda = tk.Text(frm_ajuda, wrap="word", bg="#1e293b", fg="#f8fafc", font=theme.FONT_NORMAL)
        self.txt_ajuda.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        texto_teoria = """ALGORITMO DE WEILER-ATHERTON PARA RECORTE DE POLÍGONOS

O algoritmo de Weiler-Atherton é uma técnica clássica e poderosa capaz de recortar polígonos côncavos arbitrários, inclusive gerando múltiplos sub-polígonos desconectados quando uma forma é seccionada.

COMO FUNCIONA:
1. Ordenação Horária:
   Garante que tanto o polígono sujeito quanto a janela de recorte estejam em sentido horário.
2. Cálculo de Interseções:
   Calcula todas as interseções entre as arestas do polígono e os 4 lados da janela.
3. Inserção e Classificação:
   Insere os pontos de interseção em listas encadeadas circulares para o Polígono e para a Janela.
   - Ponto de ENTRADA: O polígono vem de fora para dentro da janela.
   - Ponto de SAÍDA: O polígono vai de dentro para fora da janela.
4. Travessia de Listas:
   - Começa em um ponto de ENTRADA não visitado.
   - Percorre o polígono sujeito até encontrar um ponto de SAÍDA.
   - Alterna para a lista da Janela de Recorte no sentido horário até achar uma ENTRADA.
   - Alterna de volta para o polígono sujeito até fechar o contorno.
   - Repete para todos os pontos de entrada, extraindo múltiplos polígonos se necessário!"""
        self.txt_ajuda.insert(tk.END, texto_teoria)
        self.txt_ajuda.config(state=tk.DISABLED)

    def _window_field(self, parent, label_text, var, row, col):
        f = tk.Frame(parent, bg=theme.BG_PANEL)
        f.grid(row=row, column=col, padx=4, pady=2, sticky="w")
        tk.Label(f, text=label_text, bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        e = ttk.Entry(f, textvariable=var, width=5)
        e.pack(side=tk.LEFT, padx=2)
        e.bind("<Return>", lambda e: self.desenhar())

    def _on_zoom_change(self):
        z = max(1, int(self.zoom.get()))
        self.vp.set_escala(z)
        self.quadro.redraw()

    def add_polygon_point(self):
        try:
            x = float(self.vertex_x.get())
            y = float(self.vertex_y.get())
            pts = self.get_polygon_points()
            pts.append((x, y))
            self.set_polygon_points(pts)
            self.desenhar()
        except ValueError:
            messagebox.showerror("Erro", "Coordenadas X e Y devem ser números válidos.")

    def remove_last_polygon_point(self):
        pts = self.get_polygon_points()
        if pts:
            pts.pop()
            self.set_polygon_points(pts)
            self.desenhar()

    def toggle_draw_mode(self):
        self.interactive_draw_mode = not self.interactive_draw_mode
        if self.interactive_draw_mode:
            self.draw_button.config(bg=theme.SUCCESS, text="🛑 Parar Desenho")
            self.status_var.set("Modo Desenho ATIVO: Clique com o Botão Esquerdo no canvas para adicionar vértices.")
            self.quadro.set_pan_enabled(False)
        else:
            self.draw_button.config(bg=theme.ACCENT, text="✏ Desenhar na Tela")
            self.status_var.set("Modo Desenho Desativado.")
            self.quadro.set_pan_enabled(True)

    def _on_canvas_left_release(self, event):
        if not self.interactive_draw_mode:
            return
        wx, wy = self.quadro.canvas_para_mundo(event.x, event.y)
        pts = self.get_polygon_points()
        pts.append((round(wx, 1), round(wy, 1)))
        self.set_polygon_points(pts)
        self.desenhar()

    def _on_canvas_right_click(self, event):
        if self.interactive_draw_mode:
            self.remove_last_polygon_point()

    def get_polygon_points(self) -> list[Point]:
        txt = self.vertices_text.get().strip()
        if not txt:
            return []
        pontos = []
        for pedaco in txt.split(";"):
            pedaco = pedaco.strip()
            if not pedaco:
                continue
            partes = pedaco.split(",")
            if len(partes) == 2:
                try:
                    pontos.append((float(partes[0].strip()), float(partes[1].strip())))
                except ValueError:
                    pass
        return pontos

    def set_polygon_points(self, points: list[Point]):
        txt = "; ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in points)
        self.vertices_text.set(txt)

    def carregar_exemplo_concavo(self):
        """Carrega um polígono côncavo em forma de U que é dividido em 2 sub-polígonos separados."""
        pts = [
            (-45, -20), (45, -20), (45, 50),
            (25, 50), (25, 5), (-25, 5),
            (-25, 50), (-45, 50)
        ]
        self.xmin.set(-35)
        self.ymin.set(10)
        self.xmax.set(35)
        self.ymax.set(60)
        self.set_polygon_points(pts)
        self.desenhar()
        self.enquadrar()

    def carregar_exemplo_estrela(self):
        """Carrega uma estrela côncava de 5 pontas."""
        pts = []
        raio_ext, raio_int = 45, 20
        for i in range(10):
            r = raio_ext if i % 2 == 0 else raio_int
            ang = math.pi / 2 + i * (math.pi / 5)
            pts.append((round(r * math.cos(ang), 1), round(r * math.sin(ang), 1)))
        self.xmin.set(-25)
        self.ymin.set(-25)
        self.xmax.set(25)
        self.ymax.set(25)
        self.set_polygon_points(pts)
        self.desenhar()
        self.enquadrar()

    def limpar(self):
        self.set_polygon_points([])
        self._last_result = None
        self.quadro.limpar()
        self.txt_resumo.delete("1.0", tk.END)
        self.txt_passos.delete("1.0", tk.END)
        self.status_var.set("Tela e dados limpos.")

    def enquadrar(self):
        pts = self.get_polygon_points()
        if not pts:
            return
        xs = [p[0] for p in pts] + [self.xmin.get(), self.xmax.get()]
        ys = [p[1] for p in pts] + [self.ymin.get(), self.ymax.get()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        larg_cenario = max(10, max_x - min_x)
        alt_cenario = max(10, max_y - min_y)
        
        larg_canvas = self.canvas.winfo_width() or 800
        alt_canvas = self.canvas.winfo_height() or 600
        
        escala_x = larg_canvas / (larg_cenario * 1.4)
        escala_y = alt_canvas / (alt_cenario * 1.4)
        novo_zoom = max(1, min(40, int(min(escala_x, escala_y))))
        
        self.zoom.set(novo_zoom)
        self.vp.set_escala(novo_zoom)
        self.quadro.cxw = (min_x + max_x) / 2.0
        self.quadro.cyw = (min_y + max_y) / 2.0
        self.quadro.redraw()

    def desenhar(self):
        pts = self.get_polygon_points()
        if len(pts) < 3:
            self.status_var.set("Informe ao menos 3 vértices para formar um polígono.")
            self.quadro.redraw()
            return

        xmin, ymin, xmax, ymax = normalizar_janela(
            self.xmin.get(), self.ymin.get(), self.xmax.get(), self.ymax.get()
        )
        self.xmin.set(xmin); self.ymin.set(ymin); self.xmax.set(xmax); self.ymax.set(ymax)

        result = weiler_atherton_clip_trace(pts, xmin, ymin, xmax, ymax)
        self._last_result = result
        self._atualizar_resumo(result)
        self._atualizar_passos(result)
        self.quadro.redraw()

    def _redesenhar(self, cv: tk.Canvas):
        if not self._last_result:
            pts = self.get_polygon_points()
            if pts:
                self._desenhar_poligono(cv, pts, outline="#38bdf8", fill="", dash=(3, 3))
            return

        res = self._last_result
        orig = res["original"]
        xmin, ymin, xmax, ymax = res["window"]
        clipped_polys = res["clipped_polygons"]
        intersections = res["intersections"]

        # 1. Desenha a Janela de Recorte (Retângulo em destaque)
        p1 = self.quadro.mundo_para_canvas(xmin, ymax)
        p2 = self.quadro.mundo_para_canvas(xmax, ymin)
        cv.create_rectangle(p1[0], p1[1], p2[0], p2[1], outline="#ef4444", width=2, dash=(6, 4))
        cv.create_text(p1[0] + 8, p1[1] + 12, text="Janela de Recorte", fill="#ef4444", font=("Segoe UI", 9, "bold"), anchor="w")

        # 2. Desenha o Polígono Original Sujeito (Linhas tracejadas azul)
        if orig and len(orig) >= 3:
            self._desenhar_poligono(cv, orig, outline="#0284c7", fill="", dash=(4, 3), width=2)
            if self.show_vertex_markers_var.get():
                for idx, pt in enumerate(orig):
                    cx, cy = self.quadro.mundo_para_canvas(pt[0], pt[1])
                    cv.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#0284c7", outline="#ffffff")
                    if self.show_vertex_values_var.get():
                        cv.create_text(cx + 8, cy - 6, text=f"P{idx}({pt[0]:.1f},{pt[1]:.1f})", fill="#0284c7", font=("Segoe UI", 8, "bold"))

        # 3. Desenha os Sub-Polígonos Recortados por Weiler-Atherton (Preenchimento Verde Esmeralda)
        cores_preenchimento = ["#10b981", "#06b6d4", "#8b5cf6", "#f59e0b"]
        for p_idx, poly in enumerate(clipped_polys):
            cor = cores_preenchimento[p_idx % len(cores_preenchimento)]
            self._desenhar_poligono(cv, poly, outline=cor, fill=cor, stipple="gray25", width=3)
            # Destaque dos vértices recortados
            for v_idx, pt in enumerate(poly):
                cx, cy = self.quadro.mundo_para_canvas(pt[0], pt[1])
                cv.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=cor, outline="#ffffff")

        # 4. Desenha as Interseções
        if self.show_intersections_var.get():
            for ipt in intersections:
                cx, cy = self.quadro.mundo_para_canvas(ipt[0], ipt[1])
                cv.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#f43f5e", outline="#ffffff", width=2)
                cv.create_text(cx + 10, cy + 8, text=f"({ipt[0]:.1f},{ipt[1]:.1f})", fill="#f43f5e", font=("Segoe UI", 8, "bold"))

    def _desenhar_poligono(self, cv: tk.Canvas, pontos: list[Point], outline="#000000", fill="", width=1, dash=(), stipple=""):
        if len(pontos) < 2:
            return
        coords = []
        for p in pontos:
            cx, cy = self.quadro.mundo_para_canvas(p[0], p[1])
            coords.extend([cx, cy])
        if len(pontos) >= 3:
            cv.create_polygon(coords, outline=outline, fill=fill, width=width, dash=dash, stipple=stipple)
        else:
            cv.create_line(coords, fill=outline, width=width, dash=dash)

    def _atualizar_resumo(self, res: dict):
        self.txt_resumo.delete("1.0", tk.END)
        n_polys = len(res["clipped_polygons"])
        texto = f"=== RESUMO DO RECORTE (WEILER-ATHERTON) ===\n"
        texto += f"Polígonos Resultantes: {n_polys}\n"
        texto += f"Total de Interseções: {len(res['intersections'])}\n\n"
        
        for i, poly in enumerate(res["clipped_polygons"], 1):
            texto += f"▶ Sub-polígono {i} ({len(poly)} vértices):\n"
            for v in poly:
                texto += f"   • ({v[0]:.2f}, {v[1]:.2f})\n"
            texto += "\n"
        
        self.txt_resumo.insert(tk.END, texto)

    def _atualizar_passos(self, res: dict):
        self.txt_passos.delete("1.0", tk.END)
        texto = "=== EXECUÇÃO PASSO A PASSO (TRACE WEILER-ATHERTON) ===\n\n"
        for s in res["steps"]:
            texto += s + "\n\n"
        self.txt_passos.insert(tk.END, texto)
