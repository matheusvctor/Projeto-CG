"""
formas_simples.py – Aplicação para desenhar formas simples.
Como executar: python apps/formas_simples.py
"""

import math
import os
import sys
import tkinter as tk
from tkinter import ttk

# Garante acesso à raiz do projeto e à pasta do módulo (para encontrar 'core' e 'theme')
_dir_modulo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_dir_raiz = os.path.abspath(os.path.join(_dir_modulo, ".."))
if _dir_modulo not in sys.path:
    sys.path.insert(0, _dir_modulo)
if _dir_raiz not in sys.path:
    sys.path.insert(0, _dir_raiz)

from core.cg_utils import *
import theme

def _direcao(dx, dy):
    """Resume o sentido do segmento em notação cardeal, útil para o log didático."""
    if dx == 0 and dy == 0: return "—"
    comp = ""
    if dy > 0: comp += "N"
    elif dy < 0: comp += "S"
    if dx > 0: comp += "E"
    elif dx < 0: comp += "W"
    return comp or ("E" if dx>0 else "W" if dx<0 else "N" if dy>0 else "S")

def _declive_intercepto(x0, y0, x1, y1):
    """Calcula declive e intercepto da reta para exibir a forma analítica no resumo."""
    dx = x1 - x0
    if dx == 0:
        return None, x0
    m = (y1 - y0) / dx
    b = y0 - m * x0
    return m, b

class AppFormas:
    def __init__(self, root, on_back=None): 
        """Monta a interface da Questão 1 para desenhar primitivas, cônicas e Bézier."""
        self.on_back = on_back
        theme.configure_ttk_styles(root)
        self.tamanho_pixel = tk.IntVar(value=1)
        self.zoom = tk.IntVar(value=1)
        self.algoritmo = tk.StringVar(value="DDA (Reta)")
        self.anotar = tk.BooleanVar(value=True)

        self.x0=tk.IntVar(value=-40); self.y0=tk.IntVar(value=-30)
        self.x1=tk.IntVar(value= 60); self.y1=tk.IntVar(value= 70)
        self.xc=tk.IntVar(value=0);   self.yc=tk.IntVar(value=0); self.r=tk.IntVar(value=40)
        self.rx=tk.IntVar(value=50);  self.ry=tk.IntVar(value=30)
        self.par_xv=tk.IntVar(value=0); self.par_yv=tk.IntVar(value=-20)
        self.par_p=tk.IntVar(value=12); self.par_orient=tk.StringVar(value="Vertical")
        self.hip_xc=tk.IntVar(value=0); self.hip_yc=tk.IntVar(value=0)
        self.hip_a=tk.IntVar(value=28); self.hip_b=tk.IntVar(value=18)
        self.hip_orient=tk.StringVar(value="Horizontal")
        self.bx0 = tk.IntVar(value=-40); self.by0 = tk.IntVar(value=-20)
        self.bx1 = tk.IntVar(value=-10); self.by1 = tk.IntVar(value= 50)
        self.bx2 = tk.IntVar(value= 20); self.by2 = tk.IntVar(value=-40)
        self.bx3 = tk.IntVar(value= 50); self.by3 = tk.IntVar(value= 30)

        topo = tk.Frame(root, bg=theme.BG_PANEL, padx=10, pady=8)
        topo.pack(side=tk.TOP, fill=tk.X)

        theme.make_btn(topo, "◀ Voltar", self._voltar, "primary", padx=10, pady=4).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(topo, text="Algoritmo:", bg=theme.BG_PANEL, fg=theme.FG_TEXT, font=theme.FONT_SUBTITLE).pack(side=tk.LEFT, padx=(0, 4))
        cb = ttk.Combobox(topo, textvariable=self.algoritmo, state="readonly", width=28,
            values=[
                "DDA (Reta)",
                "Ponto Médio (Reta)",
                "Circunferência – Ponto Médio",
                "Circunferência – Polinomial",
                "Circunferência – Trigonométrico",
                "Elipse (Ponto Médio)",   
                "Parábola",
                "Hipérbole",
                "Curva de Bézier"         
            ])
        cb.pack(side=tk.LEFT, padx=(0, 12))
        cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_inputs())

        self.param_frame = tk.Frame(topo, bg=theme.BG_PANEL)
        self.param_frame.pack(side=tk.LEFT, padx=(0, 10))

        fopt = tk.Frame(topo, bg=theme.BG_PANEL)
        fopt.pack(side=tk.RIGHT)
        
        tk.Label(fopt, text="Pixel:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        ttk.Spinbox(fopt, from_=1, to=20, textvariable=self.tamanho_pixel, width=4).pack(side=tk.LEFT, padx=(2, 8))
        
        tk.Label(fopt, text="Zoom:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        sp_zoom = ttk.Spinbox(fopt, from_=1, to=40, textvariable=self.zoom, width=4, command=self._on_zoom_change)
        sp_zoom.pack(side=tk.LEFT, padx=(2, 8))
        sp_zoom.bind("<Return>", lambda e: self._on_zoom_change())
        sp_zoom.bind("<FocusOut>", lambda e: self._on_zoom_change())
        
        ttk.Checkbutton(fopt, text="Anotar pontos", variable=self.anotar).pack(side=tk.LEFT, padx=(0, 8))
        theme.make_btn(fopt, "▶ Desenhar", self.desenhar, "success", padx=12, pady=4).pack(side=tk.LEFT, padx=4)
        theme.make_btn(fopt, "↺ Limpar", self.limpar, "danger", padx=10, pady=4).pack(side=tk.LEFT, padx=4)


        corpo = ttk.Frame(root); corpo.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0,6))

        right = ttk.Frame(corpo)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(8,0), pady=8)
        nb = ttk.Notebook(right); nb.pack(fill=tk.BOTH, expand=True)
        frmResumo = ttk.Frame(nb); frmAjuda = ttk.Frame(nb)
        nb.add(frmResumo, text="Operações (resumo)")
        nb.add(frmAjuda,  text="Como calculamos")

        self.log = tk.Text(frmResumo, width=46, height=34, wrap="none", font=("Consolas", 9))
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sc=ttk.Scrollbar(frmResumo, orient=tk.VERTICAL, command=self.log.yview)
        sc.pack(side=tk.LEFT, fill=tk.Y); self.log.configure(yscrollcommand=sc.set)

        self.help = tk.Text(frmAjuda, width=46, height=34, wrap="word", font=("Segoe UI", 10), bg="#f7f7f7")
        self.help.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        mid = ttk.Frame(corpo); mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vp = Viewport(900, 700, escala=self.zoom.get())
        self.canvas = tk.Canvas(mid, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.quadro = QuadroDesenho(self.canvas, self.vp, usar_grade=True)
        registrar_quadro(self.quadro, self)
        self.quadro.set_redraw_callback(self._redesenhar)
        mid.bind("<Configure>", lambda e: self.quadro.resize(e.width, e.height))

        left = ttk.LabelFrame(corpo, text="Pontos (amostras)", padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8), pady=8)
        self.lista = tk.Text(left, width=28, height=34, wrap="none", font=("Consolas", 9))
        self.lista.pack(side=tk.LEFT, fill=tk.Y)
        sc2=ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.lista.yview)
        sc2.pack(side=tk.LEFT, fill=tk.Y); self.lista.configure(yscrollcommand=sc2.set)

        self._last = None
        self._rebuild_inputs()
        self._update_help()

    def _clear_param(self):
        """Remove os campos do algoritmo anterior antes de reconstruir o formulário."""
        for w in self.param_frame.winfo_children(): w.destroy()

    def _row(self, lbl, var1, var2=None):
        """Cria uma pequena linha de entrada para 1 ou 2 parâmetros relacionados."""
        f=ttk.Frame(self.param_frame); f.pack(side=tk.LEFT, padx=4)
        ttk.Label(f,text=lbl).pack(anchor="w")
        frm_in = ttk.Frame(f); frm_in.pack(anchor="w")
        ttk.Entry(frm_in,textvariable=var1, width=5).pack(side=tk.LEFT)
        if var2: ttk.Entry(frm_in,textvariable=var2, width=5).pack(side=tk.LEFT, padx=(2,0))

    def _selector(self, lbl, var, values, width=12):
        """Cria um seletor readonly para parâmetros discretos, como orientação."""
        f = ttk.Frame(self.param_frame); f.pack(side=tk.LEFT, padx=4)
        ttk.Label(f, text=lbl).pack(anchor="w")
        cb = ttk.Combobox(f, textvariable=var, state="readonly", values=values, width=width)
        cb.pack(anchor="w")

    def _rebuild_inputs(self):
        """Troca dinamicamente os campos de entrada conforme o algoritmo selecionado."""
        self._clear_param(); alg = self.algoritmo.get()
        if "Reta" in alg:
            self._row("P0 (x,y):", self.x0, self.y0); self._row("P1 (x,y):", self.x1, self.y1)
        elif alg == "Elipse (Ponto Médio)":
            self._row("Centro (x,y):", self.xc, self.yc); self._row("Raios (rx, ry):", self.rx, self.ry)
        elif alg == "Parábola":
            self._row("Vértice (x,y):", self.par_xv, self.par_yv)
            self._row("Parâmetro p:", self.par_p)
            self._selector("Abertura:", self.par_orient, ("Vertical", "Horizontal"), width=10)
        elif alg == "Hipérbole":
            self._row("Centro (x,y):", self.hip_xc, self.hip_yc)
            self._row("Semi-eixos (a,b):", self.hip_a, self.hip_b)
            self._selector("Orientação:", self.hip_orient, ("Horizontal", "Vertical"), width=10)
        elif alg == "Curva de Bézier":
            self._row("P0 (x,y):", self.bx0, self.by0); self._row("P1 (x,y):", self.bx1, self.by1)
            self._row("P2 (x,y):", self.bx2, self.by2); self._row("P3 (x,y):", self.bx3, self.by3)
        else:
            self._row("Centro (x,y):", self.xc, self.yc); self._row("Raio:", self.r)
        self._update_help()

    def _on_zoom_change(self):
        """Atualiza a escala da viewport e redesenha o conteúdo já existente."""
        try: z = int(self.zoom.get())
        except Exception: return
        if z < 1: z = 1; self.zoom.set(1)
        self.vp.set_escala(z); self.quadro.redraw()

    def _voltar(self):
        """Fecha a janela atual ou devolve o controle ao menu quando houver callback."""
        if callable(self.on_back):
            self.on_back()
        else:
            self.canvas.winfo_toplevel().destroy()

    def _help_text(self, alg):
        """Gera o resumo matemático do algoritmo ativo para a aba de ajuda."""
        if alg == "DDA (Reta)":
            return ("DDA (Digital Differential Analyzer)\n"
                    "• declive: m = dy/dx e intercepto: b = y0 − m*x0\n"
                    "• passos = max(|dx|, |dy|)\n"
                    "• inc_x = dx/passos, inc_y = dy/passos\n"
                    "• x += inc_x, y += inc_y; plot(round(x), round(y))")
        if alg == "Ponto Médio (Reta)":
            return ("Reta por Ponto Médio (Bresenham)\n"
                    "• identificar oitante por sinais de dx, dy e por |dx| vs |dy|\n"
                    "• declive m e intercepto b descrevem a reta ideal\n"
                    "• x-dom: d=2*dy−dx; se d<=0: d+=2*dy; senão: d+=2*(dy−dx), y+=sy\n"
                    "• análogo para y-dom")
        if alg == "Circunferência – Ponto Médio":
            return ("Círculo (Midpoint)\n"
                    "• início: x=0, y=r, d=1−r\n"
                    "• se d<0: d+=2x+3; senão: d+=2(x−y)+5, y--\n"
                    "• plota por simetria de 8 pontos")
        if alg == "Circunferência – Polinomial":
            return ("Círculo (Equação x²+y²=r²)\n"
                    "• x∈[0,r]: y=sqrt(r²−x²) + simetria 8\n"
                    "• sem correção: pode ter lacunas (natural)")
        if alg == "Elipse (Ponto Médio)":
            return ("Elipse (Midpoint)\n"
                    "• região 1: avança em x enquanto 2*ry²*x < 2*rx²*y\n"
                    "• região 2: avança em y com novo parâmetro de decisão\n"
                    "• usa simetria de 4 pontos em torno do centro")
        if alg == "Parábola":
            return ("Parábola\n"
                    "• forma padrão: (x-h)² = 4p(y-k) ou (y-k)² = 4p(x-h)\n"
                    "• entrada por vértice, abertura e parâmetro p\n"
                    "• a interface converte para Ax² + By² + Cxy + Dx + Ey + F = 0\n"
                    "• depois usa a mesma varredura da seção cônica geral")
        if alg == "Hipérbole":
            return ("Hipérbole\n"
                    "• horizontal: (x-h)²/a² − (y-k)²/b² = 1\n"
                    "• vertical: (y-k)²/a² − (x-h)²/b² = 1\n"
                    "• entrada por centro, semi-eixos e orientação\n"
                    "• a interface converte para a equação geral e desenha por varredura")
        return ("Círculo (Trigonométrico)\n"
                "• x=xc+r cos t, y=yc+r sin t; t∈[0,2π]\n"
                "• passo ~ 1/r; sem ligar amostras → lacunas (natural)")
    def _update_help(self):
        """Atualiza a aba de ajuda toda vez que o algoritmo selecionado muda."""
        self.help.config(state="normal")
        self.help.delete("1.0", tk.END)
        self.help.insert(tk.END, self._help_text(self.algoritmo.get()))
        self.help.config(state="disabled")

    def _iniciar_log(self, titulo):
        """Reinicia o painel de log para uma nova execução do algoritmo."""
        self.log.delete("1.0", tk.END); self.log.insert(tk.END, f"▶ {titulo}\n" + "-"*42 + "\n")
    def _registrar(self, msg):
        """Adiciona uma linha explicativa ao log lateral."""
        self.log.insert(tk.END, msg + "\n"); self.log.see(tk.END)
    def _anotar_lista(self, pts):
        """Lista as amostras geradas para facilitar conferência manual dos pontos."""
        self.lista.delete("1.0", tk.END)
        for i,(x,y) in enumerate(pts): self.lista.insert(tk.END, f"P{i:03d}: ({x},{y})\n")
        self.lista.see(tk.END)

    def _coeficientes_parabola(self):
        """Converte a parábola parametrizada pelo usuário para a forma geral Ax²+By²+...=0."""
        h = self.par_xv.get()
        k = self.par_yv.get()
        p = self.par_p.get()
        if p == 0:
            raise ValueError("O parâmetro p da parábola não pode ser zero.")
        if self.par_orient.get() == "Horizontal":
            return (0.0, 1.0, 0.0, -4.0 * p, -2.0 * k, k * k + 4.0 * p * h)
        return (1.0, 0.0, 0.0, -2.0 * h, -4.0 * p, h * h + 4.0 * p * k)

    def _coeficientes_hiperbole(self):
        """Converte a hipérbole escolhida para a equação geral usada pela rotina de varredura."""
        h = self.hip_xc.get()
        k = self.hip_yc.get()
        a = self.hip_a.get()
        b = self.hip_b.get()
        if a == 0 or b == 0:
            raise ValueError("Os semi-eixos da hipérbole devem ser diferentes de zero.")
        a2 = float(a * a)
        b2 = float(b * b)
        if self.hip_orient.get() == "Vertical":
            return (-1.0 / b2, 1.0 / a2, 0.0, 2.0 * h / b2, -2.0 * k / a2, (k * k) / a2 - (h * h) / b2 - 1.0)
        return (1.0 / a2, -1.0 / b2, 0.0, -2.0 * h / a2, 2.0 * k / b2, (h * h) / a2 - (k * k) / b2 - 1.0)

    def _limites_parabola(self):
        """Estima um retângulo local de desenho para evitar varredura desnecessária da parábola."""
        h = self.par_xv.get()
        k = self.par_yv.get()
        p = self.par_p.get()
        abs_p = abs(p)
        alcance = max(40, 6 * abs_p)
        desloc_lateral = math.ceil(math.sqrt(max(0.0, 4.0 * abs_p * alcance))) + 2
        if self.par_orient.get() == "Horizontal":
            xmin = h if p > 0 else h - alcance
            xmax = h + alcance if p > 0 else h
            return (xmin - 2, xmax + 2, k - desloc_lateral, k + desloc_lateral)
        ymin = k if p > 0 else k - alcance
        ymax = k + alcance if p > 0 else k
        return (h - desloc_lateral, h + desloc_lateral, ymin - 2, ymax + 2)

    def _limites_hiperbole(self):
        """Define uma caixa de amostragem razoável para desenhar a hipérbole no canvas."""
        h = self.hip_xc.get()
        k = self.hip_yc.get()
        a = abs(self.hip_a.get())
        b = abs(self.hip_b.get())
        alcance_transversal = max(40, 2 * b)
        alcance_principal = math.ceil(a * math.sqrt(1.0 + (alcance_transversal * alcance_transversal) / float(b * b))) + 2
        if self.hip_orient.get() == "Vertical":
            return (h - alcance_transversal - 2, h + alcance_transversal + 2, k - alcance_principal, k + alcance_principal)
        return (h - alcance_principal, h + alcance_principal, k - alcance_transversal - 2, k + alcance_transversal + 2)

    def _marcar_pontos_canvas(self, pts):
        """Marca uma amostra dos pixels gerados diretamente no canvas para inspeção visual."""
        for i,(x,y) in enumerate(pts):
            sx, sy = self.quadro.mundo_para_canvas(x, y)
            self.canvas.create_rectangle(sx-2, sy-2, sx+2, sy+2, outline="#1f77b4", fill="#1f77b4", tags="ANOT")
            if i in (0, len(pts)-1) or (i % max(1, len(pts)//12) == 0):
                self.canvas.create_text(sx+5, sy-5, text=f"P{i}", fill="#1f77b4", font=("Segoe UI", 9), tags="ANOT", anchor="sw")
    def limpar(self):
        self._iniciar_log("Limpar"); self.lista.delete("1.0", tk.END); self.canvas.delete("ANOT"); self.quadro.limpar()

    def _redesenhar(self):
        """Refaz o último desenho quando o canvas muda de tamanho ou zoom."""
        if not self._last: return
        kind, params = self._last
        if   kind == "reta_dda":  reta_dda(*params)
        elif kind == "reta_pm":   reta_ponto_medio(*params)
        elif kind == "circ_pm":   circunferencia_ponto_medio(*params)
        elif kind == "circ_eq":   circunferencia_equacao(*params)
        elif kind == "circ_trig": circunferencia_trigonometrica(*params)
        elif kind == "elipse_pm": elipse_ponto_medio(*params)
        elif kind == "conica":    secao_conica_varredura(*params)
        elif kind == "bezier":    curva_bezier_cubica(*params)
        if getattr(self, "anotar", None) and self.anotar.get() and getattr(self, "pontos_anotacao", None):
            self._marcar_pontos_canvas(self.pontos_anotacao)

    def desenhar(self):
        """Executa o algoritmo selecionado, registra explicações e guarda o estado para redraw."""
        alg = self.algoritmo.get(); self.limpar(); self._iniciar_log(alg)
        pts=[]; ligar_coleta(pts)
        try:
            if   alg == "DDA (Reta)":
                x0,y0,x1,y1 = self.x0.get(), self.y0.get(), self.x1.get(), self.y1.get()
                dx, dy = x1-x0, y1-y0; passos = int(max(abs(dx), abs(dy)))
                inc_x = dx/passos if passos else 0; inc_y = dy/passos if passos else 0
                m, b = _declive_intercepto(x0, y0, x1, y1)
                self._registrar(f"dx={dx}, dy={dy}, passos={passos}")
                if passos: self._registrar(f"inc_x={inc_x:.3f}, inc_y={inc_y:.3f}")
                if m is None: self._registrar(f"reta vertical: x = {b}")
                else: self._registrar(f"declive m={m:.3f}, intercepto b={b:.3f}")
                self._registrar(f"direção: {_direcao(dx,dy)} ; pixels~{passos+1}")
                reta_dda(x0,y0,x1,y1); self._last=("reta_dda",(x0,y0,x1,y1))
            elif alg == "Ponto Médio (Reta)":
                x0,y0,x1,y1 = self.x0.get(), self.y0.get(), self.x1.get(), self.y1.get()
                dx, dy = x1-x0, y1-y0
                m, b = _declive_intercepto(x0, y0, x1, y1)
                self._registrar(f"|dx|={abs(dx)}, |dy|={abs(dy)}, direção={_direcao(dx,dy)}")
                if m is None: self._registrar(f"reta vertical: x = {b}")
                else: self._registrar(f"declive m={m:.3f}, intercepto b={b:.3f}")
                self._registrar(f"pixels (aprox): {max(abs(dx),abs(dy))+1}")
                reta_ponto_medio(x0,y0,x1,y1); self._last=("reta_pm",(x0,y0,x1,y1))
            elif alg == "Circunferência – Ponto Médio":
                xc,yc,r = self.xc.get(), self.yc.get(), self.r.get()
                self._registrar(f"centro=({xc},{yc}), r={r}, d0={1-r}")
                circunferencia_ponto_medio(xc,yc,r); self._last=("circ_pm",(xc,yc,r))
            elif alg == "Circunferência – Polinomial":
                xc,yc,r = self.xc.get(), self.yc.get(), self.r.get()
                self._registrar(f"centro=({xc},{yc}), r={r}, x∈[0,{r}] (sem correção)")
                circunferencia_equacao(xc,yc,r); self._last=("circ_eq",(xc,yc,r))
            elif alg == "Circunferência – Trigonométrico":
                xc,yc,r = self.xc.get(), self.yc.get(), self.r.get()
                step = (1.0/r) if r>0 else 0
                self._registrar(f"centro=({xc},{yc}), r={r}, passo θ≈{step:.3f} rad (sem correção)")
                circunferencia_trigonometrica(xc,yc,r); self._last=("circ_trig",(xc,yc,r))
            elif alg == "Elipse (Ponto Médio)":
                xc, yc, rx, ry = self.xc.get(), self.yc.get(), self.rx.get(), self.ry.get()
                self._registrar(f"Elipse: centro=({xc},{yc}), rx={rx}, ry={ry}")
                elipse_ponto_medio(xc, yc, rx, ry)
                self._last=("elipse_pm", (xc, yc, rx, ry))
            elif alg == "Parábola":
                xv, yv, p = self.par_xv.get(), self.par_yv.get(), self.par_p.get()
                orient = self.par_orient.get().lower()
                a, b, c, d, e, f = self._coeficientes_parabola()
                limites = self._limites_parabola()
                tipo, discriminante = classificar_secao_conica(a, b, c, d, e, f)
                self._registrar(f"Parábola: vértice=({xv},{yv}), p={p}, abertura={orient}")
                self._registrar(
                    f"equação geral: {a:g}x² + {b:g}y² + {c:g}xy + {d:g}x + {e:g}y + {f:g} = 0"
                )
                self._registrar(f"Δ = C² - 4AB = {discriminante:.3f} -> {tipo}")
                self._registrar(
                    f"recorte local: x=[{limites[0]:.0f}, {limites[1]:.0f}] | y=[{limites[2]:.0f}, {limites[3]:.0f}]"
                )
                secao_conica_varredura(a, b, c, d, e, f, limites)
                self._last=("conica", (a, b, c, d, e, f, limites))
            elif alg == "Hipérbole":
                xc, yc = self.hip_xc.get(), self.hip_yc.get()
                eixo_a, eixo_b = self.hip_a.get(), self.hip_b.get()
                orient = self.hip_orient.get().lower()
                a, b, c, d, e, f = self._coeficientes_hiperbole()
                limites = self._limites_hiperbole()
                tipo, discriminante = classificar_secao_conica(a, b, c, d, e, f)
                self._registrar(
                    f"Hipérbole: centro=({xc},{yc}), a={eixo_a}, b={eixo_b}, orientação={orient}"
                )
                self._registrar(
                    f"equação geral: {a:g}x² + {b:g}y² + {c:g}xy + {d:g}x + {e:g}y + {f:g} = 0"
                )
                self._registrar(f"Δ = C² - 4AB = {discriminante:.3f} -> {tipo}")
                self._registrar(
                    f"recorte local: x=[{limites[0]:.0f}, {limites[1]:.0f}] | y=[{limites[2]:.0f}, {limites[3]:.0f}]"
                )
                secao_conica_varredura(a, b, c, d, e, f, limites)
                self._last=("conica", (a, b, c, d, e, f, limites))
            elif alg == "Curva de Bézier":
                p0 = (self.bx0.get(), self.by0.get())
                p1 = (self.bx1.get(), self.by1.get())
                p2 = (self.bx2.get(), self.by2.get())
                p3 = (self.bx3.get(), self.by3.get())
                self._registrar(f"Bézier (4 Pontos): {p0}, {p1}, {p2}, {p3}")
                curva_bezier_cubica(p0, p1, p2, p3)
                self._last=("bezier", (p0, p1, p2, p3))
        except ValueError as exc:
            self._registrar(f"Erro: {exc}")
            self._last = None
        finally:
            desligar_coleta()
        if self.anotar.get():
            seen=set(); uniq=[]
            for p in pts:
                if p not in seen: seen.add(p); uniq.append(p)
            self.pontos_anotacao = uniq  
            self._anotar_lista(uniq); self._marcar_pontos_canvas(uniq)
        else:
            self.pontos_anotacao = []

def main():
    """Ponto de entrada isolado para abrir a interface de primitivas diretamente."""
    root = tk.Tk()
    root.title("Lab2 - Formas Simples")
    app = AppFormas(root)
    root.mainloop()

if __name__ == "__main__":
    main()
