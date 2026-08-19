#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from core.cg_utils import (
    Viewport, QuadroDesenho, registrar_quadro,
    reta_ponto_medio,
    multiplicar_matrizes, aplicar_transformacao,
    seg_origem, quadrado_origem, triangulo_origem,
    S, R, T, Sh
)

# ---------- Caixinha de diálogo genérica (2~N campos numéricos) ----------
class _Dialog2(simpledialog.Dialog):
    def __init__(self, parent, title, fields, init=None):
        self.fields = fields
        self.init = init or {}
        self.values = {}
        super().__init__(parent, title)
    def body(self, master):
        self._widgets = {}
        for i, (lbl, key) in enumerate(self.fields):
            ttk.Label(master, text=lbl).grid(row=i, column=0, sticky="e", padx=6, pady=4)
            e = ttk.Entry(master, width=14)
            e.grid(row=i, column=1, sticky="w", padx=6, pady=4)
            e.insert(0, str(self.init.get(key, "")))
            self._widgets[key] = e
        return list(self._widgets.values())[0]
    def apply(self):
        out = {}
        for key, e in self._widgets.items():
            s = e.get().strip()
            out[key] = float(s) if s else 0.0
        self.values = out

# ====================== APP ======================
class AppTransf2D:
    def __init__(self, root, on_back=None):
        self.on_back = on_back
        self.zoom = tk.IntVar(value=1)            # zoom padrão = 1
        self.tamanho_pixel = tk.IntVar(value=1)
        self.objeto = tk.StringVar(value="Quadrado")
        self.size_obj = tk.IntVar(value=40)
        self.pontos = []
        self._undo, self._redo = [], []

        # ---------- TOP BAR ----------
        topo = ttk.Frame(root, padding=(8,6)); topo.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(topo, text="◀ Voltar", command=self._voltar).pack(side=tk.LEFT, padx=(0,8))
        ttk.Label(topo, text="Coordenada X:").pack(side=tk.LEFT)
        self.inp_x = ttk.Entry(topo, width=8); self.inp_x.pack(side=tk.LEFT, padx=(2,10))
        ttk.Label(topo, text="Coordenada Y:").pack(side=tk.LEFT)
        self.inp_y = ttk.Entry(topo, width=8); self.inp_y.pack(side=tk.LEFT, padx=(2,10))
        ttk.Button(topo, text="Adicionar Ponto", command=self._add_ponto).pack(side=tk.LEFT, padx=(0,18))
        ttk.Label(topo, text="Objeto:").pack(side=tk.LEFT)
        ttk.Combobox(topo, textvariable=self.objeto, state="readonly", width=12,
                     values=["Segmento","Quadrado","Triângulo"]).pack(side=tk.LEFT, padx=(2,8))
        ttk.Label(topo, text="size (obj):").pack(side=tk.LEFT)
        ttk.Entry(topo, textvariable=self.size_obj, width=6).pack(side=tk.LEFT, padx=(2,14))
        ttk.Button(topo, text="Desenhar base", command=self.desenhar_base).pack(side=tk.LEFT, padx=(0,8))
        ttk.Label(topo, text="zoom:").pack(side=tk.LEFT)
        spz = ttk.Spinbox(topo, from_=1, to=40, textvariable=self.zoom, width=5, command=self._on_zoom_change)
        spz.pack(side=tk.LEFT, padx=(2,8))
        spz.bind("<Return>", lambda e: self._on_zoom_change())
        spz.bind("<FocusOut>", lambda e: self._on_zoom_change())
        ttk.Label(topo, text="pixel:").pack(side=tk.LEFT)
        ttk.Spinbox(topo, from_=1, to=20, textvariable=self.tamanho_pixel, width=5).pack(side=tk.LEFT)
        self.mostrar_coords = tk.BooleanVar(value=True)
        ttk.Checkbutton(topo, text="Mostrar Coords", variable=self.mostrar_coords, command=lambda: getattr(self, 'quadro', None) and self.quadro.redraw()).pack(side=tk.LEFT, padx=(8,0))
        
        # ---------- CORPO ----------
        corpo = ttk.Frame(root); corpo.pack(fill=tk.BOTH, expand=True)

        # — Centro (Canvas) primeiro, para já criar grade/borda:
        mid = ttk.Frame(corpo); mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.vp = Viewport(920, 600, escala=self.zoom.get())
        self.canvas = tk.Canvas(mid, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.quadro = QuadroDesenho(self.canvas, self.vp, usar_grade=True)
        registrar_quadro(self.quadro, self)
        self.quadro.set_redraw_callback(self._redesenhar)
        mid.bind("<Configure>", lambda e: self.quadro.resize(e.width, e.height))
        # garante que a grade apareça já na abertura:
        root.after(50, self.quadro.redraw)

        # — Direita: notebook (Resumo + Como calculamos)
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

        # — Esquerda: botões grandes
        left = ttk.Frame(corpo); left.pack(side=tk.LEFT, fill=tk.Y, padx=(6,0), pady=6)
        def bigbtn(txt, cmd):
            b = ttk.Button(left, text=txt, command=cmd)
            b.pack(fill=tk.X, pady=6, ipadx=10, ipady=12)
        bigbtn("Transladar", self._dlg_transladar)
        bigbtn("Rotacionar", self._dlg_rotacionar)
        bigbtn("Escalonar", self._dlg_escalonar)
        bigbtn("Cisalhar",  self._dlg_cisalhar)
        bigbtn("Refletir",  self._dlg_refletir)
        bigbtn("Limpar",    self.limpar)

        # — Rodapé: lista de pontos
        bottom = ttk.Frame(root, padding=(8,6)); bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_pts = tk.Text(bottom, height=6, wrap="none",
                               bg="#222", fg="#ddd", insertbackground="#ddd",
                               font=("Consolas", 10))
        self.txt_pts.pack(fill=tk.X)

        # atalhos
        root.bind("<Control-z>", lambda e: self._desfazer())
        root.bind("<Control-y>", lambda e: self._refazer())
        root.bind("<Delete>",    lambda e: self.limpar())

        self._log_clear()
        self._push_state()

    # ---------- util ----------
    def _voltar(self):
        if callable(self.on_back):
            self.on_back()
        else:
            # fallback: fecha esta janela
            self.canvas.winfo_toplevel().destroy()

    def _on_zoom_change(self):
        z = max(1, int(self.zoom.get()))
        self.vp.set_escala(z)
        self.quadro.redraw()

    def _log(self, s):
        self.log.insert(tk.END, s + "\n"); self.log.see(tk.END)
    def _log_clear(self):
        self.log.delete("1.0", tk.END)
    def _fmtM(self, M):
        def row(r): return "| " + "  ".join(f"{v:6.2f}" for v in r) + " |"
        return "\n".join(row(r) for r in M)
    def _listar_pontos(self):
        self.txt_pts.delete("1.0", tk.END)
        for i,(x,y) in enumerate(self.pontos):
            self.txt_pts.insert(tk.END, f"p{i}: ({x:.2f}, {y:.2f})\n")

    # ---------- ajuda ----------
    def _help_text(self, op=None):
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
        self.help.config(state="normal")
        self.help.delete("1.0", tk.END)
        self.help.insert(tk.END, self._help_text(op_tag))
        self.help.config(state="disabled")

    # ---------- desenho ----------
    def _desenhar_poligono(self, pts, cor="#000"):
        n = len(pts)
        for i in range(n):
            x0,y0 = int(round(pts[i][0])), int(round(pts[i][1]))
            x1,y1 = int(round(pts[(i+1)%n][0])), int(round(pts[(i+1)%n][1]))
            reta_ponto_medio(x0,y0,x1,y1,cor)

    def _redesenhar(self):
        self.quadro.limpar()
        if not self.pontos:
            return
        if len(self.pontos) == 2:
            a,b = self.pontos
            reta_ponto_medio(int(round(a[0])), int(round(a[1])),
                             int(round(b[0])), int(round(b[1])))
        else:
            self._desenhar_poligono(self.pontos)
            
        #Mapeia do mundo matemático para os pixels da tela e escreve o texto
        if getattr(self, "mostrar_coords", None) and self.mostrar_coords.get():
            for x, y in self.pontos:
                sx, sy = self.quadro.mundo_para_canvas(x, y)
                self.quadro.cv.create_text(sx + 8, sy - 8, text=f"({x:.1f}, {y:.1f})", 
                                           fill="#d62728", font=("Segoe UI", 9, "bold"), anchor="sw")

    # ---------- base / pontos ----------
    def desenhar_base(self):
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
        try:
            x = float(self.inp_x.get().strip()); y = float(self.inp_y.get().strip())
        except Exception:
            messagebox.showwarning("Entrada inválida", "Digite X e Y numéricos."); return
        self.pontos.append((x,y))
        self._log(f"Adicionado: ({x}, {y})")
        self._listar_pontos(); self.quadro.redraw(); self._push_state()

    # ---------- limpar / undo / redo ----------
    def limpar(self):
        self.pontos = []
        self._log("Limpar desenho")
        self._listar_pontos()
        self.quadro.redraw()
        self._push_state()

    def _push_state(self):
        self._undo.append(self.pontos[:]); self._redo.clear()
    def _desfazer(self):
        if len(self._undo) <= 1: return
        self._redo.append(self._undo.pop()); self.pontos = self._undo[-1][:]
        self._listar_pontos(); self.quadro.redraw()
    def _refazer(self):
        if not self._redo: return
        self.pontos = self._redo.pop(); self._undo.append(self.pontos[:])
        self._listar_pontos(); self.quadro.redraw()

    # ---------- aplicar M ----------
    def _aplicar_M(self, M, label):
        if not self.pontos:
            self._log("Nada para transformar. Desenhe a base ou adicione pontos."); return
        self._log(label + ":\n" + self._fmtM(M))
        self.pontos = aplicar_transformacao(self.pontos, M)
        self._listar_pontos(); self.quadro.redraw(); self._push_state()
        self._log("-"*34)

    # ---------- diálogos ----------
    def _dlg_transladar(self):
        self._update_help("T")
        d = _Dialog2(self.canvas.winfo_toplevel(), "Transladar",
                     [("Valor de dx:", "dx"), ("Valor de dy:", "dy")])
        if not d.values: return
        M = T(d.values.get("dx",0.0), d.values.get("dy",0.0))
        self._aplicar_M(M, "Translação T")

    def _dlg_rotacionar(self):
        self._update_help("R")
        d = _Dialog2(self.canvas.winfo_toplevel(), "Rotacionar",
                     [("Ângulo θ (graus):", "theta")], {"theta":0})
        if not d.values: return
        M = R(d.values.get("theta",0.0))
        self._aplicar_M(M, "Rotação R")

    def _dlg_escalonar(self):
        self._update_help("S")
        d = _Dialog2(self.canvas.winfo_toplevel(), "Escalonar",
                     [("sx:", "sx"), ("sy:", "sy")], {"sx":1,"sy":1})
        if not d.values: return
        M = S(d.values.get("sx",1.0), d.values.get("sy",1.0))
        self._aplicar_M(M, "Escala S")

    def _dlg_cisalhar(self):
        self._update_help("Sh")
        d = _Dialog2(self.canvas.winfo_toplevel(), "Cisalhar",
                     [("Valor de cisalhamento em x (shx):", "shx"),
                      ("Valor de cisalhamento em y (shy):", "shy")],
                     {"shx":0,"shy":0})
        if not d.values: return
        M = Sh(d.values.get("shx",0.0), d.values.get("shy",0.0))
        self._aplicar_M(M, "Cisalhamento Sh")

    def _dlg_refletir(self):
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

def main():
    root = tk.Tk()
    root.title("Transformações 2D - Editor Gráfico")
    AppTransf2D(root)
    root.mainloop()

if __name__ == "__main__":
    main()
