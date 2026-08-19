import os
import sys
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

# Garante acesso à raiz do projeto e à pasta do módulo (para encontrar 'core' e 'theme')
_dir_modulo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_dir_raiz = os.path.abspath(os.path.join(_dir_modulo, ".."))
if _dir_modulo not in sys.path:
    sys.path.insert(0, _dir_modulo)
if _dir_raiz not in sys.path:
    sys.path.insert(0, _dir_raiz)

from core.cg_utils import (
    Viewport, QuadroDesenho, registrar_quadro,
    reta_ponto_medio,
    multiplicar_matrizes, aplicar_transformacao,
    seg_origem, quadrado_origem, triangulo_origem,
    S, R, T, Sh
)
import theme

class _Dialog2(simpledialog.Dialog):
    def __init__(self, parent, title, fields, init=None):
        """Dialogo genérico usado para reaproveitar entradas numéricas das transformações."""
        self.fields = fields
        self.init = init or {}
        self.values = {}
        super().__init__(parent, title)

    def body(self, master):
        """Cria as entradas dinamicamente a partir da lista de campos recebida."""
        self._widgets = {}
        for i, (lbl, key) in enumerate(self.fields):
            ttk.Label(master, text=lbl).grid(row=i, column=0, sticky="e", padx=6, pady=4)
            e = ttk.Entry(master, width=14)
            e.grid(row=i, column=1, sticky="w", padx=6, pady=4)
            e.insert(0, str(self.init.get(key, "")))
            self._widgets[key] = e
        return list(self._widgets.values())[0]
    
    def apply(self):
        """Converte os campos para float e salva os valores para a janela principal."""
        out = {}
        for key, e in self._widgets.items():
            s = e.get().strip()
            out[key] = float(s) if s else 0.0
        self.values = out

class AppTransf2D:
    def __init__(self, root, on_back=None):
        """Interface para montar um objeto 2D e aplicar transformações homogêneas nele."""
        self.on_back = on_back
        theme.configure_ttk_styles(root)
        self.zoom = tk.IntVar(value=1)
        self.tamanho_pixel = tk.IntVar(value=1)
        self.objeto = tk.StringVar(value="Quadrado")
        self.size_obj = tk.IntVar(value=40)
        self.pontos = []
        self._undo, self._redo = [], []

        topo = tk.Frame(root, bg=theme.BG_PANEL, padx=10, pady=8)
        topo.pack(side=tk.TOP, fill=tk.X)

        theme.make_btn(topo, "◀ Voltar", self._voltar, "primary", padx=10, pady=4).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(topo, text="X:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        self.inp_x = ttk.Entry(topo, width=5)
        self.inp_x.pack(side=tk.LEFT, padx=(2, 6))
        
        tk.Label(topo, text="Y:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        self.inp_y = ttk.Entry(topo, width=5)
        self.inp_y.pack(side=tk.LEFT, padx=(2, 6))
        
        theme.make_btn(topo, "➕ Ponto", self._add_ponto, "secondary", padx=8, pady=3).pack(side=tk.LEFT, padx=(0, 12))
        
        tk.Label(topo, text="Forma:", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Combobox(topo, textvariable=self.objeto, state="readonly", width=11,
                     values=["Segmento", "Quadrado", "Triângulo"]).pack(side=tk.LEFT, padx=(0, 6))
        
        tk.Label(topo, text="Tam:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        ttk.Entry(topo, textvariable=self.size_obj, width=4).pack(side=tk.LEFT, padx=(2, 8))
        
        theme.make_btn(topo, "📐 Gerar Base", self.desenhar_base, "success", padx=10, pady=3).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(topo, text="Zoom:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        spz = ttk.Spinbox(topo, from_=1, to=40, textvariable=self.zoom, width=4, command=self._on_zoom_change)
        spz.pack(side=tk.LEFT, padx=(2, 6))
        spz.bind("<Return>", lambda e: self._on_zoom_change())
        spz.bind("<FocusOut>", lambda e: self._on_zoom_change())
        
        tk.Label(topo, text="Pixel:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        ttk.Spinbox(topo, from_=1, to=20, textvariable=self.tamanho_pixel, width=4).pack(side=tk.LEFT, padx=(2, 8))
        
        self.mostrar_coords = tk.BooleanVar(value=True)
        ttk.Checkbutton(topo, text="Coords", variable=self.mostrar_coords, command=lambda: getattr(self, 'quadro', None) and self.quadro.redraw()).pack(side=tk.LEFT, padx=(4, 0))

        corpo = ttk.Frame(root); corpo.pack(fill=tk.BOTH, expand=True)

        mid = ttk.Frame(corpo); mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.vp = Viewport(920, 600, escala=self.zoom.get())
        self.canvas = tk.Canvas(mid, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.quadro = QuadroDesenho(self.canvas, self.vp, usar_grade=True)
        registrar_quadro(self.quadro, self)
        self.quadro.set_redraw_callback(self._redesenhar)
        mid.bind("<Configure>", lambda e: self.quadro.resize(e.width, e.height))

        root.after(50, self.quadro.redraw)

        right = ttk.Frame(corpo); right.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,6), pady=6)
        nb = ttk.Notebook(right); nb.pack(fill=tk.BOTH, expand=True)
        frmResumo = ttk.Frame(nb); frmAjuda = ttk.Frame(nb)
        nb.add(frmResumo, text="Operações (resumo)"); nb.add(frmAjuda, text="Como calculamos")
        self.log = tk.Text(frmResumo, width=40, height=30, wrap="none",
                           bg="#222", fg="#ddd", insertbackground="#ddd",
                           font=("Consolas", 10))
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sc = ttk.Scrollbar(frmResumo, orient=tk.VERTICAL, command=self.log.yview)
        sc.pack(side=tk.LEFT, fill=tk.Y); self.log.configure(yscrollcommand=sc.set)
        self.help = tk.Text(frmAjuda, width=40, height=30, wrap="word",
                            font=("Segoe UI", 10), bg="#f7f7f7")
        self.help.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self._update_help(None)

        left = tk.Frame(corpo, bg=theme.BG_PANEL, width=220, padx=10, pady=8)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(6, 0), pady=6)
        left.pack_propagate(False)

        tk.Label(left, text="TRANSFORMAÇÕES 2D", font=theme.FONT_SUBTITLE, bg=theme.BG_PANEL, fg=theme.CYAN_GLOW).pack(anchor="w", pady=(0, 6))

        def add_action_btn(txt, cmd, btype="secondary"):
            btn = theme.make_btn(left, txt, cmd, btype, anchor="w", padx=10, pady=6)
            btn.pack(fill=tk.X, pady=3)
            return btn

        add_action_btn("✥  Transladar", self._dlg_transladar, "secondary")
        add_action_btn("↻  Rotacionar (Pivô)", self._dlg_rotacionar, "secondary")
        add_action_btn("⤢  Escalonar (Pivô)", self._dlg_escalonar, "secondary")
        add_action_btn("⇋  Cisalhar", self._dlg_cisalhar, "secondary")
        add_action_btn("🪞  Refletir", self._dlg_refletir, "secondary")
        add_action_btn("⚡  Compor Matrizes 2D", self._dlg_composicao, "primary")
        add_action_btn("👁  Mostrar Viewport", self._mostrar_viewport, "secondary")
        add_action_btn("↶  Desfazer Passo", self._desfazer, "warning")
        add_action_btn("↺  Limpar Tudo", self.limpar, "danger")


        bottom = ttk.Frame(root, padding=(8,6)); bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_pts = tk.Text(bottom, height=6, wrap="none",
                               bg="#222", fg="#ddd", insertbackground="#ddd",
                               font=("Consolas", 10))
        self.txt_pts.pack(fill=tk.X)

        root.bind("<Control-z>", lambda e: self._desfazer())
        root.bind("<Control-y>", lambda e: self._refazer())
        root.bind("<Delete>",    lambda e: self.limpar())

        self._log_clear()
        self._push_state()

    def _voltar(self):
        """Fecha a tela atual ou retorna ao menu pai se um callback existir."""
        if callable(self.on_back):
            self.on_back()
        else:
            self.canvas.winfo_toplevel().destroy()

    def _on_zoom_change(self):
        """Atualiza a escala da viewport mantendo o mesmo desenho em memória."""
        z = max(1, int(self.zoom.get()))
        self.vp.set_escala(z)
        self.quadro.redraw()

    def _log(self, s):
        """Escreve uma nova linha no painel de resumo das operações."""
        self.log.insert(tk.END, s + "\n"); self.log.see(tk.END)
    def _log_clear(self):
        """Apaga o histórico textual de operações."""
        self.log.delete("1.0", tk.END)
    def _fmtM(self, M):
        """Formata uma matriz para leitura humana no log lateral."""
        def row(r): return "| " + "  ".join(f"{v:6.2f}" for v in r) + " |"
        return "\n".join(row(r) for r in M)
    def _listar_pontos(self):
        """Atualiza a lista de vértices atualmente pertencentes ao objeto."""
        self.txt_pts.delete("1.0", tk.END)
        for i,(x,y) in enumerate(self.pontos):
            self.txt_pts.insert(tk.END, f"p{i}: ({x:.2f}, {y:.2f})\n")

    def _mapear_para_painel(self, x, y, xmin, xmax, ymin, ymax, left, top, right, bottom, inverter_y=False):
        """Mapeia coordenadas matemáticas para o retângulo de preview da janela auxiliar."""
        if abs(xmax - xmin) < 1e-9 or abs(ymax - ymin) < 1e-9:
            return left, bottom
        sx = left + ((x - xmin) / (xmax - xmin)) * (right - left)
        if inverter_y:
            sy = top + ((y - ymin) / (ymax - ymin)) * (bottom - top)
        else:
            sy = bottom - ((y - ymin) / (ymax - ymin)) * (bottom - top)
        return sx, sy

    def _desenhar_eixos_preview(self, canvas, xmin, xmax, ymin, ymax, left, top, right, bottom, inverter_y=False):
        """Desenha eixos de referência apenas quando o intervalo mostrado cruza a origem."""
        if xmin <= 0 <= xmax:
            sx, _ = self._mapear_para_painel(0, ymin, xmin, xmax, ymin, ymax, left, top, right, bottom, inverter_y)
            canvas.create_line(sx, top, sx, bottom, fill="#9aa0a6", dash=(4, 3))
            canvas.create_text(sx + 10, top + 12, text="Y", fill="#5f6368", font=("Segoe UI", 9, "bold"))
        if ymin <= 0 <= ymax:
            _, sy = self._mapear_para_painel(xmin, 0, xmin, xmax, ymin, ymax, left, top, right, bottom, inverter_y)
            canvas.create_line(left, sy, right, sy, fill="#9aa0a6", dash=(4, 3))
            canvas.create_text(right - 10, sy - 10, text="X", fill="#5f6368", font=("Segoe UI", 9, "bold"))

    def _desenhar_shape_preview(self, canvas, pontos, mapper, outline, fill):
        if not pontos:
            return
        coords = []
        for x, y in pontos:
            sx, sy = mapper(x, y)
            coords.extend([sx, sy])

        if len(pontos) >= 3:
            canvas.create_polygon(coords, outline=outline, fill=fill, width=2)
        elif len(pontos) == 2:
            canvas.create_line(*coords, fill=outline, width=2)
        else:
            sx, sy = coords
            canvas.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=outline, outline=outline)

    def _mostrar_viewport(self):
        """Abre uma janela didática mostrando mundo e tela para o estado atual do objeto."""
        top = tk.Toplevel(self.canvas.winfo_toplevel())
        top.title("Janela do Mundo e Viewport")
        top.geometry("1040x520")
        top.minsize(940, 480)

        frame = ttk.Frame(top, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Estado atual da Janela do Mundo e sua Viewport",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(frame, bg="white", highlightthickness=1, highlightbackground="#d0d7de")
        canvas.pack(fill=tk.BOTH, expand=True)

        info = tk.Text(frame, height=6, wrap="word", font=("Consolas", 10))
        info.pack(fill=tk.X, pady=(10, 0))
        info.configure(state="disabled")

        wxmin, wxmax, wymin, wymax = self.quadro._world_bounds()
        vxmin, vymin = 0.0, 0.0
        vxmax, vymax = float(self.vp.largura), float(self.vp.altura)

        def map_window_to_viewport(xw, yw):
            sx = (vxmax - vxmin) / (wxmax - wxmin) if abs(wxmax - wxmin) > 1e-9 else 1.0
            sy = (vymax - vymin) / (wymax - wymin) if abs(wymax - wymin) > 1e-9 else 1.0
            xv = vxmin + (xw - wxmin) * sx
            yv = vymin + (wymax - yw) * sy
            return xv, yv

        def redraw_preview(_event=None):
            canvas.delete("all")
            w = max(760, canvas.winfo_width())
            h = max(320, canvas.winfo_height())
            pad = 30
            gap = 40
            panel_w = (w - pad * 2 - gap) / 2
            panel_h = h - 90

            world_rect = (pad, 50, pad + panel_w, 50 + panel_h)
            view_rect = (pad + panel_w + gap, 50, pad + 2 * panel_w + gap, 50 + panel_h)

            canvas.create_text((world_rect[0] + world_rect[2]) / 2, 24, text="Janela do Mundo", font=("Segoe UI", 12, "bold"))
            canvas.create_text((view_rect[0] + view_rect[2]) / 2, 24, text="Viewport", font=("Segoe UI", 12, "bold"))

            canvas.create_rectangle(*world_rect, outline="#6c757d", width=2)
            canvas.create_rectangle(*view_rect, outline="#005a9c", width=2)

            self._desenhar_eixos_preview(canvas, wxmin, wxmax, wymin, wymax, *world_rect)
            self._desenhar_eixos_preview(canvas, vxmin, vxmax, vymin, vymax, *view_rect, inverter_y=True)

            self._desenhar_shape_preview(
                canvas,
                self.pontos,
                lambda x, y: self._mapear_para_painel(x, y, wxmin, wxmax, wymin, wymax, *world_rect),
                outline="#9a031e",
                fill="#f4acb7",
            )

            pontos_viewport = [map_window_to_viewport(x, y) for x, y in self.pontos]
            self._desenhar_shape_preview(
                canvas,
                pontos_viewport,
                lambda x, y: self._mapear_para_painel(x, y, vxmin, vxmax, vymin, vymax, *view_rect, inverter_y=True),
                outline="#005a9c",
                fill="#a9d6e5",
            )

            origem_x, origem_y = self._mapear_para_painel(0, 0, vxmin, vxmax, vymin, vymax, *view_rect, inverter_y=True)
            canvas.create_oval(origem_x - 4, origem_y - 4, origem_x + 4, origem_y + 4, fill="#005a9c", outline="#005a9c")
            canvas.create_text(origem_x + 10, origem_y + 10, text="Origem (0,0)", anchor="nw", fill="#005a9c", font=("Segoe UI", 9, "bold"))

            canvas.create_text(
                world_rect[0], world_rect[3] + 20,
                text=f"W = [{wxmin:.2f}, {wxmax:.2f}] x [{wymin:.2f}, {wymax:.2f}]",
                anchor="w", fill="#495057", font=("Consolas", 10)
            )
            canvas.create_text(
                view_rect[0], view_rect[3] + 20,
                text=f"V = [{vxmin:.0f}, {vxmax:.0f}] x [{vymin:.0f}, {vymax:.0f}] px",
                anchor="w", fill="#495057", font=("Consolas", 10)
            )

        sx = (vxmax - vxmin) / (wxmax - wxmin) if abs(wxmax - wxmin) > 1e-9 else 1.0
        sy = (vymax - vymin) / (wymax - wymin) if abs(wymax - wymin) > 1e-9 else 1.0
        pontos_txt = ["Nenhum ponto desenhado no estado atual."] if not self.pontos else [
            f"p{i}: mundo=({x:.2f}, {y:.2f}) -> viewport=({xv:.2f}, {yv:.2f})"
            for i, ((x, y), (xv, yv)) in enumerate(zip(self.pontos, [map_window_to_viewport(x, y) for x, y in self.pontos]))
        ]

        texto_info = "\n".join([
            "Mapeamento classico janela->viewport:",
            f"xv = vxmin + (xw - wxmin) * ((vxmax - vxmin) / (wxmax - wxmin))",
            f"yv = vymin + (wymax - yw) * ((vymax - vymin) / (wymax - wymin))",
            "Na viewport, a origem (0,0) fica no canto superior esquerdo e Y cresce para baixo.",
            f"Sx = {sx:.4f} px/unidade | Sy = {sy:.4f} px/unidade",
            *pontos_txt,
        ])
        info.configure(state="normal")
        info.delete("1.0", tk.END)
        info.insert("1.0", texto_info)
        info.configure(state="disabled")

        canvas.bind("<Configure>", redraw_preview)
        redraw_preview()

    def _help_text(self, op=None):
        """Retorna o texto matemático básico da transformação selecionada."""
        if op == "T":
            return ("Translação T(tx,ty):\n"
                    "|1 0 tx|\n|0 1 ty|\n|0 0  1|\n"
                    "(x',y')=(x+tx, y+ty)")
        if op == "R":
            return ("Rotação R(θ):\n"
                    "| cos -sin 0|\n| sin  cos 0|\n|  0    0  1|\n"
                    "Pivô p: T(p)·R·T(-p)")
        if op == "S":
            return ("Escala S(sx,sy):\n"
                    "|sx 0  0|\n|0  sy 0|\n|0  0  1|\n"
                    "Pivô p: T(p)·S·T(-p)")
        if op == "Sh":
            return ("Cisalhamento Sh(shx,shy):\n"
                    "|1  shx 0|\n|shy 1  0|\n|0   0  1|\n"
                    "Inclina X (shx) e/ou Y (shy).")
        if op == "Ref":
            return ("Reflexões (via S negativa):\n"
                    "X: S(1,-1)   Y: S(-1,1)   Ambos: S(-1,-1)")
        return ("Composição típica: M = T · R · S · Sh\n"
                "Aplicação: P' = M · [x y 1]^T\n"
                "Ordem importa.")
    def _update_help(self, op_tag):
        """Atualiza a aba de ajuda conforme a última operação focada pelo usuário."""
        self.help.config(state="normal")
        self.help.delete("1.0", tk.END)
        self.help.insert(tk.END, self._help_text(op_tag))
        self.help.config(state="disabled")

    def _desenhar_poligono(self, pts, cor="#000"):
        """Liga os vértices atuais com retas para montar o contorno do objeto."""
        n = len(pts)
        for i in range(n):
            x0,y0 = int(round(pts[i][0])), int(round(pts[i][1]))
            x1,y1 = int(round(pts[(i+1)%n][0])), int(round(pts[(i+1)%n][1]))
            reta_ponto_medio(x0,y0,x1,y1,cor)

    def _redesenhar(self):
        """Redesenha o objeto atual respeitando o modo de exibição e as anotações."""
        self.quadro.limpar()
        if not self.pontos:
            return
        if len(self.pontos) == 2:
            a,b = self.pontos
            reta_ponto_medio(int(round(a[0])), int(round(a[1])),
                             int(round(b[0])), int(round(b[1])))
        else:
            self._desenhar_poligono(self.pontos)

        if getattr(self, "mostrar_coords", None) and self.mostrar_coords.get():
            for x, y in self.pontos:
                sx, sy = self.quadro.mundo_para_canvas(x, y)
                self.quadro.cv.create_text(sx + 8, sy - 8, text=f"({x:.1f}, {y:.1f})", 
                                           fill="#d62728", font=("Segoe UI", 9, "bold"), anchor="sw")

    def desenhar_base(self):
        """Cria um objeto base padrão na origem para servir de referência às transformações."""
        try:
            s = int(self.size_obj.get())
        except Exception:
            s = 40
            self.size_obj.set(40)

        kind = self.objeto.get()
        if kind == "Segmento":
            self.pontos = seg_origem(s)
        elif kind == "Quadrado":
            self.pontos = quadrado_origem(s)
        else:
            self.pontos = triangulo_origem(s)

        self._log_clear()
        self._log(f"Base: {kind} na origem, size={s}")
        self._listar_pontos()
        self.quadro.redraw()
        self._push_state()

    def _add_ponto(self):
        """Adiciona um novo vértice manual ao objeto a partir das entradas X/Y."""
        try:
            x = float(self.inp_x.get().strip()); y = float(self.inp_y.get().strip())
        except Exception:
            messagebox.showwarning("Entrada inválida", "Digite X e Y numéricos."); return
        self.pontos.append((x,y))
        self._log(f"Adicionado: ({x}, {y})")
        self._listar_pontos(); self.quadro.redraw(); self._push_state()

    def limpar(self):
        """Remove todos os pontos do objeto sem fechar a interface."""
        self.pontos = []
        self._log("Limpar desenho")
        self._listar_pontos()
        self.quadro.redraw()
        self._push_state()

    def _push_state(self):
        """Guarda um snapshot do objeto para permitir desfazer e refazer depois."""
        self._undo.append(self.pontos[:]); self._redo.clear()
    def _desfazer(self):
        """Restaura o penúltimo estado salvo do objeto."""
        if len(self._undo) <= 1:
            messagebox.showinfo("Histórico", "O objeto já está no seu estado original!")
            return
        self._redo.append(self._undo.pop()); self.pontos = self._undo[-1][:]
        self._log("↩ Ação desfeita")
        self._listar_pontos(); self.quadro.redraw()
    def _refazer(self):
        """Reaplica um estado que foi removido pela operação de desfazer."""
        if not self._redo: return
        self.pontos = self._redo.pop(); self._undo.append(self.pontos[:])
        self._listar_pontos(); self.quadro.redraw()

    def _centro_objeto(self):
        """Calcula o centro geométrico (centróide) do objeto atual."""
        if not self.pontos:
            return 0.0, 0.0
        cx = sum(p[0] for p in self.pontos) / len(self.pontos)
        cy = sum(p[1] for p in self.pontos) / len(self.pontos)
        return cx, cy

    def _aplicar_M(self, M, label):
        """Aplica a matriz homogênea ao conjunto de pontos e registra a operação no log."""
        if not self.pontos:
            self._log("Nada para transformar. Desenhe a base ou adicione pontos."); return
        self._log(label + ":\n" + self._fmtM(M))
        self.pontos = aplicar_transformacao(self.pontos, M)
        self._listar_pontos(); self.quadro.redraw(); self._push_state()
        self._log("-"*34)

    def _dlg_transladar(self):
        """Solicita dx/dy ao usuário e executa a translação correspondente."""
        self._update_help("T")
        d = _Dialog2(self.canvas.winfo_toplevel(), "Transladar 2D",
                     [("Valor de dx:", "dx"), ("Valor de dy:", "dy")])
        if not d.values: return
        M = T(d.values.get("dx",0.0), d.values.get("dy",0.0))
        self._aplicar_M(M, "Translação T")

    def _dlg_rotacionar(self):
        """Aplica rotação permitindo escolher como pivô o centro do objeto ou a origem."""
        self._update_help("R")
        root = self.canvas.winfo_toplevel()
        top = tk.Toplevel(root)
        top.title("Rotacionar 2D (Com Pivô)")
        top.transient(root)
        top.grab_set()

        cx, cy = self._centro_objeto()

        ttk.Label(top, text="Ângulo de Rotação θ (graus):", font=("Segoe UI", 10, "bold")).pack(padx=12, pady=(10, 2))
        ent_theta = ttk.Entry(top, width=15)
        ent_theta.insert(0, "45")
        ent_theta.pack(padx=12, pady=4)

        ttk.Label(top, text="Ponto de Rotação (Pivô):", font=("Segoe UI", 10, "bold")).pack(padx=12, pady=(10, 2))
        pivo_var = tk.StringVar(value="centro")
        ttk.Radiobutton(top, text=f"Centro do Objeto ({cx:.1f}, {cy:.1f}) [Mantém na posição]", variable=pivo_var, value="centro").pack(anchor="w", padx=15, pady=2)
        ttk.Radiobutton(top, text="Origem do Sistema (0, 0)", variable=pivo_var, value="origem").pack(anchor="w", padx=15, pady=2)

        def ok():
            try:
                theta = float(ent_theta.get().strip() or 0.0)
            except ValueError:
                messagebox.showerror("Erro", "Digite um ângulo numérico válido.")
                return

            if pivo_var.get() == "centro":
                # Composição homogênea em torno do centro: M = T(cx, cy) · R(θ) · T(-cx, -cy)
                ida = T(-cx, -cy)
                rot = R(theta)
                volta = T(cx, cy)
                M = multiplicar_matrizes(volta, multiplicar_matrizes(rot, ida))
                label = f"Rotação R({theta:.1f}°) no Centro ({cx:.1f}, {cy:.1f})"
            else:
                M = R(theta)
                label = f"Rotação R({theta:.1f}°) na Origem (0,0)"

            top.destroy()
            self._aplicar_M(M, label)

        ttk.Button(top, text="Aplicar Rotação", command=ok).pack(pady=(12, 4), ipadx=10)
        ttk.Button(top, text="Cancelar", command=top.destroy).pack(pady=(0, 10))

    def _dlg_escalonar(self):
        """Solicita fatores em X/Y e aplica a escala em torno do centro do objeto ou da origem."""
        self._update_help("S")
        root = self.canvas.winfo_toplevel()
        top = tk.Toplevel(root)
        top.title("Escalonar 2D (Com Pivô)")
        top.transient(root)
        top.grab_set()

        cx, cy = self._centro_objeto()

        ttk.Label(top, text="Fator de Escala em X (sx):").pack(padx=12, pady=(8, 2))
        ent_sx = ttk.Entry(top, width=15)
        ent_sx.insert(0, "1.5")
        ent_sx.pack(padx=12, pady=2)

        ttk.Label(top, text="Fator de Escala em Y (sy):").pack(padx=12, pady=(6, 2))
        ent_sy = ttk.Entry(top, width=15)
        ent_sy.insert(0, "1.5")
        ent_sy.pack(padx=12, pady=2)

        pivo_var = tk.StringVar(value="centro")
        ttk.Radiobutton(top, text=f"Escalar no Centro ({cx:.1f}, {cy:.1f})", variable=pivo_var, value="centro").pack(anchor="w", padx=15, pady=4)
        ttk.Radiobutton(top, text="Escalar na Origem (0, 0)", variable=pivo_var, value="origem").pack(anchor="w", padx=15, pady=2)

        def ok():
            try:
                sx = float(ent_sx.get().strip() or 1.0)
                sy = float(ent_sy.get().strip() or 1.0)
            except ValueError:
                messagebox.showerror("Erro", "Digite fatores de escala numéricos válidos.")
                return

            if pivo_var.get() == "centro":
                # Composição homogênea: M = T(cx, cy) · S(sx, sy) · T(-cx, -cy)
                ida = T(-cx, -cy)
                esc = S(sx, sy)
                volta = T(cx, cy)
                M = multiplicar_matrizes(volta, multiplicar_matrizes(esc, ida))
                label = f"Escala S({sx:.2f}, {sy:.2f}) no Centro"
            else:
                M = S(sx, sy)
                label = f"Escala S({sx:.2f}, {sy:.2f}) na Origem"

            top.destroy()
            self._aplicar_M(M, label)

        ttk.Button(top, text="Aplicar Escala", command=ok).pack(pady=(10, 4), ipadx=10)
        ttk.Button(top, text="Cancelar", command=top.destroy).pack(pady=(0, 10))

    def _dlg_cisalhar(self):
        """Solicita os fatores de cisalhamento e constrói a matriz Sh."""
        self._update_help("Sh")
        d = _Dialog2(self.canvas.winfo_toplevel(), "Cisalhar 2D",
                     [("Valor de cisalhamento em x (shx):", "shx"),
                      ("Valor de cisalhamento em y (shy):", "shy")],
                     {"shx":0,"shy":0})
        if not d.values: return
        M = Sh(d.values.get("shx",0.0), d.values.get("shy",0.0))
        self._aplicar_M(M, "Cisalhamento Sh")

    def _dlg_refletir(self):
        """Abre um seletor simples para refletir em X, Y ou nos dois eixos."""
        self._update_help("Ref")
        root = self.canvas.winfo_toplevel()
        top = tk.Toplevel(root); top.title("Refletir"); top.transient(root); top.grab_set()
        v = tk.StringVar(value="X")
        for txt in ("X", "Y", "Ambos"):
            ttk.Radiobutton(top, text=txt, variable=v, value=txt).pack(anchor="w", padx=10, pady=4)
        def ok():
            choice = v.get()
            if choice == "X":   M = S(1,-1)
            elif choice == "Y": M = S(-1,1)
            else:               M = S(-1,-1)
            top.destroy()
            self._aplicar_M(M, f"Reflexão {choice}")
        ttk.Button(top, text="OK", command=ok).pack(pady=8)
        ttk.Button(top, text="Cancelar", command=top.destroy).pack()

    def _dlg_composicao(self):
        """Permite compor múltiplas transformações sequenciais em uma única matriz homogênea."""
        if not self.pontos:
            messagebox.showinfo("Aviso", "Desenhe a base ou adicione pontos antes de compor transformações.")
            return

        root = self.canvas.winfo_toplevel()
        top = tk.Toplevel(root)
        top.title("Composição de Transformações 2D")
        top.geometry("620x520")
        top.transient(root)
        top.grab_set()

        cx, cy = self._centro_objeto()
        etapas_matrizes = []

        top_frame = ttk.Frame(top, padding=12)
        top_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(top_frame, text="Composição Sequencial de Transformações 2D", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))
        ttk.Label(top_frame, text="Adicione transformações na sequência desejada. A matriz resultante M = Mn · ... · M1 será calculada e aplicada ao objeto.", wraplength=580).pack(anchor="w", pady=(0, 10))

        listbox = tk.Listbox(top_frame, height=6, font=("Consolas", 10))
        listbox.pack(fill=tk.X, pady=(0, 10))

        # Painel de adição de operações
        btn_grid = ttk.Frame(top_frame)
        btn_grid.pack(fill=tk.X, pady=4)

        def add_t():
            d = _Dialog2(top, "Adicionar Translação", [("dx:", "dx"), ("dy:", "dy")])
            if d.values:
                dx, dy = d.values.get("dx", 0.0), d.values.get("dy", 0.0)
                M = T(dx, dy)
                etapas_matrizes.append((f"Translação T(dx={dx:.1f}, dy={dy:.1f})", M))
                listbox.insert(tk.END, f"{len(etapas_matrizes)}. Translação T(dx={dx:.1f}, dy={dy:.1f})")

        def add_r():
            d = _Dialog2(top, "Adicionar Rotação no Centro", [("Ângulo θ:", "theta")])
            if d.values:
                th = d.values.get("theta", 0.0)
                ida = T(-cx, -cy); rot = R(th); volta = T(cx, cy)
                M = multiplicar_matrizes(volta, multiplicar_matrizes(rot, ida))
                etapas_matrizes.append((f"Rotação no Centro R(θ={th:.1f}°)", M))
                listbox.insert(tk.END, f"{len(etapas_matrizes)}. Rotação no Centro R(θ={th:.1f}°)")

        def add_s():
            d = _Dialog2(top, "Adicionar Escala no Centro", [("sx:", "sx"), ("sy:", "sy")], {"sx":1,"sy":1})
            if d.values:
                sx, sy = d.values.get("sx", 1.0), d.values.get("sy", 1.0)
                ida = T(-cx, -cy); esc = S(sx, sy); volta = T(cx, cy)
                M = multiplicar_matrizes(volta, multiplicar_matrizes(esc, ida))
                etapas_matrizes.append((f"Escala no Centro S(sx={sx:.2f}, sy={sy:.2f})", M))
                listbox.insert(tk.END, f"{len(etapas_matrizes)}. Escala no Centro S(sx={sx:.2f}, sy={sy:.2f})")

        def add_sh():
            d = _Dialog2(top, "Adicionar Cisalhamento", [("shx:", "shx"), ("shy:", "shy")])
            if d.values:
                shx, shy = d.values.get("shx", 0.0), d.values.get("shy", 0.0)
                M = Sh(shx, shy)
                etapas_matrizes.append((f"Cisalhamento Sh(shx={shx:.2f}, shy={shy:.2f})", M))
                listbox.insert(tk.END, f"{len(etapas_matrizes)}. Cisalhamento Sh(shx={shx:.2f}, shy={shy:.2f})")

        def limpar_etapas():
            etapas_matrizes.clear()
            listbox.delete(0, tk.END)

        ttk.Button(btn_grid, text="+ Translação", command=add_t).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_grid, text="+ Rotação (Centro)", command=add_r).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_grid, text="+ Escala (Centro)", command=add_s).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_grid, text="+ Cisalhamento", command=add_sh).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_grid, text="Limpar Lista", command=limpar_etapas).pack(side=tk.RIGHT, padx=3)

        def aplicar_composta():
            if not etapas_matrizes:
                messagebox.showwarning("Aviso", "Adicione ao menos uma transformação na lista.")
                return

            # Multiplicação sequencial acumulada: M_composta = Mn · ... · M1
            M_acumulada = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
            descricao_etapas = []
            for nome, M_etapa in etapas_matrizes:
                M_acumulada = multiplicar_matrizes(M_etapa, M_acumulada)
                descricao_etapas.append(nome)

            top.destroy()
            self._aplicar_M(M_acumulada, "Composição de Transformações (" + " -> ".join(descricao_etapas) + ")")

        ttk.Button(top_frame, text="✔ Aplicar Composição ao Objeto", command=aplicar_composta).pack(pady=(15, 6), fill=tk.X, ipady=8)

def main():
    """Ponto de entrada isolado da tela de transformações 2D."""
    root = tk.Tk()
    root.title("Transformações 2D - Editor Gráfico")
    AppTransf2D(root)
    root.mainloop()

if __name__ == "__main__":
    main()
