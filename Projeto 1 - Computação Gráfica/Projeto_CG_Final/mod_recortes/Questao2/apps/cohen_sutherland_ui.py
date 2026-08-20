"""
Interface da Questão 2 – recorte de janela de Cohen-Sutherland.
"""
import math
import os
import sys
import tkinter as tk
from tkinter import ttk

_dir_modulo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_dir_raiz = os.path.abspath(os.path.join(_dir_modulo, ".."))
if _dir_modulo not in sys.path:
    sys.path.insert(0, _dir_modulo)
if _dir_raiz not in sys.path:
    sys.path.insert(0, _dir_raiz)

import theme
from core.cg_utils import (
    Viewport,
    QuadroDesenho,
    registrar_quadro,
    ligar_coleta,
    desligar_coleta,
    reta_dda,
    desenhar_janela,
    cohen_sutherland_clip,
    compute_outcode,
    format_outcode,
    nomes_outcode,
    normalizar_janela,
)


class AppCohenSutherland:
    def __init__(self, root, on_back=None):
        """Interface para testar recorte de segmentos com explicação passo a passo."""
        self.on_back = on_back
        theme.configure_ttk_styles(root)
        self.tamanho_pixel = tk.IntVar(value=1)
        self.zoom = tk.IntVar(value=1)
        self.anotar = tk.BooleanVar(value=True)

        self.x0 = tk.IntVar(value=-80)
        self.y0 = tk.IntVar(value=-60)
        self.x1 = tk.IntVar(value=90)
        self.y1 = tk.IntVar(value=80)
        self.xmin = tk.IntVar(value=-40)
        self.ymin = tk.IntVar(value=-30)
        self.xmax = tk.IntVar(value=50)
        self.ymax = tk.IntVar(value=40)

        self.angulo = tk.DoubleVar(value=35.0)
        self.delta_angulo = tk.DoubleVar(value=6.0)
        self.intervalo_ms = tk.IntVar(value=80)
        self.fator_comprimento = tk.DoubleVar(value=1.6)

        self._last = None
        self.pontos_anotacao = []
        self._animando = False
        self._after_id = None
        self._frame = 0

        topo = tk.Frame(root, bg=theme.BG_PANEL, padx=10, pady=8)
        topo.pack(side=tk.TOP, fill=tk.X)

        theme.make_btn(topo, "◀ Voltar", self._voltar, "primary", padx=10, pady=4).pack(side=tk.LEFT, padx=(0, 10))
        self.param_frame = tk.Frame(topo, bg=theme.BG_PANEL)
        self.param_frame.pack(side=tk.LEFT)
        self._row("P0 (x,y):", self.x0, self.y0)
        self._row("P1 (x,y):", self.x1, self.y1)
        self._row("Janela Min:", self.xmin, self.ymin)
        self._row("Janela Max:", self.xmax, self.ymax)
        self._row("Âng/Passo:", self.angulo, self.delta_angulo)
        self._row("ms/Fator:", self.intervalo_ms, self.fator_comprimento)

        fopt = tk.Frame(topo, bg=theme.BG_PANEL)
        fopt.pack(side=tk.RIGHT)
        
        tk.Label(fopt, text="Pixel:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        ttk.Spinbox(fopt, from_=1, to=20, textvariable=self.tamanho_pixel, width=4).pack(side=tk.LEFT, padx=(2, 6))
        
        tk.Label(fopt, text="Zoom:", bg=theme.BG_PANEL, fg=theme.FG_SUBTEXT, font=theme.FONT_NORMAL).pack(side=tk.LEFT)
        sp_zoom = ttk.Spinbox(fopt, from_=1, to=40, textvariable=self.zoom, width=4, command=self._on_zoom_change)
        sp_zoom.pack(side=tk.LEFT, padx=(2, 6))
        sp_zoom.bind("<Return>", lambda e: self._on_zoom_change())
        sp_zoom.bind("<FocusOut>", lambda e: self._on_zoom_change())
        
        ttk.Checkbutton(fopt, text="Anotar", variable=self.anotar, command=self._redraw_if_possible).pack(side=tk.LEFT, padx=(2, 6))
        
        theme.make_btn(fopt, "📁 Exemplo", self.carregar_exemplo, "secondary", padx=8, pady=3).pack(side=tk.LEFT, padx=2)
        theme.make_btn(fopt, "✂ Recortar", self.desenhar, "success", padx=10, pady=3).pack(side=tk.LEFT, padx=2)
        theme.make_btn(fopt, "▶ Animar", self.iniciar_animacao, "primary", padx=8, pady=3).pack(side=tk.LEFT, padx=2)
        theme.make_btn(fopt, "⏹ Parar", self.parar_animacao, "warning", padx=8, pady=3).pack(side=tk.LEFT, padx=2)
        theme.make_btn(fopt, "↺ Limpar", self.limpar, "danger", padx=8, pady=3).pack(side=tk.LEFT, padx=2)
        theme.make_btn_insp(fopt, lambda: ("mod_recortes/Questao2/apps/cohen_sutherland_ui.py", 220)).pack(side=tk.LEFT, padx=2)

        corpo = ttk.Frame(root)
        corpo.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        right = ttk.Frame(corpo)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0), pady=8)
        nb = ttk.Notebook(right)
        nb.pack(fill=tk.BOTH, expand=True)
        frm_resumo = ttk.Frame(nb)
        frm_ajuda = ttk.Frame(nb)
        nb.add(frm_resumo, text="Operações (resumo)")
        nb.add(frm_ajuda, text="Como calculamos")

        self.log = tk.Text(frm_resumo, width=50, height=34, wrap="none", font=("Consolas", 9))
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sc = ttk.Scrollbar(frm_resumo, orient=tk.VERTICAL, command=self.log.yview)
        sc.pack(side=tk.LEFT, fill=tk.Y)
        self.log.configure(yscrollcommand=sc.set)

        self.help = tk.Text(frm_ajuda, width=50, height=34, wrap="word", font=("Segoe UI", 10), bg="#f7f7f7")
        self.help.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self._update_help()

        mid = ttk.Frame(corpo)
        mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vp = Viewport(900, 700, escala=self.zoom.get())
        self.canvas = tk.Canvas(mid, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.quadro = QuadroDesenho(self.canvas, self.vp, usar_grade=True)
        registrar_quadro(self.quadro, self)
        self.quadro.set_redraw_callback(self._redesenhar)
        mid.bind("<Configure>", lambda e: self.quadro.resize(e.width, e.height))

        left = ttk.LabelFrame(corpo, text="Pontos / códigos", padding=8)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8), pady=8)
        self.lista = tk.Text(left, width=34, height=34, wrap="none", font=("Consolas", 9))
        self.lista.pack(side=tk.LEFT, fill=tk.Y)
        sc2 = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.lista.yview)
        sc2.pack(side=tk.LEFT, fill=tk.Y)
        self.lista.configure(yscrollcommand=sc2.set)

        self.carregar_exemplo()

    def _row(self, lbl, var1, var2):
        """Cria um pequeno grupo de entradas numéricas relacionadas no topo da tela."""
        f = ttk.Frame(self.param_frame)
        f.pack(side=tk.LEFT, padx=4)
        ttk.Label(f, text=lbl).pack(anchor="w")
        frm_in = ttk.Frame(f)
        frm_in.pack(anchor="w")
        ttk.Entry(frm_in, textvariable=var1, width=6).pack(side=tk.LEFT)
        ttk.Entry(frm_in, textvariable=var2, width=6).pack(side=tk.LEFT, padx=(2, 0))

    def _voltar(self):
        """Encerra a animação, se existir, e retorna ao menu anterior."""
        self.parar_animacao()
        if callable(self.on_back):
            self.on_back()
        else:
            self.canvas.winfo_toplevel().destroy()

    def _on_zoom_change(self):
        """Atualiza a escala da viewport mantendo o mesmo estado recortado."""
        try:
            z = int(self.zoom.get())
        except Exception:
            return
        if z < 1:
            z = 1
            self.zoom.set(1)
        self.vp.set_escala(z)
        self.quadro.redraw()

    def _redraw_if_possible(self):
        """Força redraw apenas quando já existe uma cena válida armazenada."""
        if self._last:
            self.quadro.redraw()

    def _update_help(self):
        """Preenche a aba de ajuda com o resumo conceitual do algoritmo."""
        texto = """Cálculo Matemático - Algoritmos de Recorte:

1. Cohen-Sutherland (Recorte de Linhas):
Dividimos o espaço em 9 regiões e atribuímos um Outcode (código de 4 bits: 
Topo, Fundo, Direita, Esquerda) para P0 e P1.
- Aceitação Trivial: Se (P0 | P1) == 0000 (Ambos dentro).
- Rejeição Trivial: Se (P0 & P1) != 0000 (Ambos fora do mesmo lado).
- Interseção: Usamos semelhança de triângulos para achar o corte. 
  Exemplo p/ corte na Direita: y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)."""
        self.help.config(state="normal")
        self.help.delete("1.0", tk.END)
        self.help.insert(tk.END, texto)
        self.help.config(state="disabled")

    def _iniciar_log(self, titulo):
        """Limpa e reinicia o log textual da operação atual."""
        self.log.delete("1.0", tk.END)
        self.log.insert(tk.END, f"▶ {titulo}\n" + "-" * 48 + "\n")

    def _registrar(self, msg):
        """Adiciona uma mensagem ao log lateral."""
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def _anotar_lista(self, dados):
        """Mostra no painel lateral os pontos, códigos e interseções relevantes."""
        self.lista.delete("1.0", tk.END)
        for linha in dados:
            self.lista.insert(tk.END, linha + "\n")
        self.lista.see(tk.END)

    def _desenhar_rotulo(self, x, y, texto, cor):
        """Marca um ponto importante da cena com rótulo diretamente no canvas."""
        sx, sy = self.quadro.mundo_para_canvas(x, y)
        self.canvas.create_rectangle(sx - 2, sy - 2, sx + 2, sy + 2, outline=cor, fill=cor, tags="ANOT")
        self.canvas.create_text(
            sx + 6,
            sy - 6,
            text=texto,
            fill=cor,
            font=("Segoe UI", 9, "bold"),
            anchor="sw",
            tags="ANOT",
        )

    def limpar(self):
        """Remove a cena atual e reinicia os painéis de apoio."""
        self.parar_animacao()
        self._last = None
        self.pontos_anotacao = []
        self._iniciar_log("Limpar")
        self.lista.delete("1.0", tk.END)
        self.canvas.delete("ANOT")
        self.quadro.limpar()

    def carregar_exemplo(self):
        """Carrega um caso inicial que atravessa a janela para facilitar testes."""
        self.parar_animacao()
        self.x0.set(-45)
        self.y0.set(25)
        self.x1.set(70)
        self.y1.set(-15)
        self.xmin.set(-20)
        self.ymin.set(-20)
        self.xmax.set(30)
        self.ymax.set(20)
        self.desenhar()

    def _desenhar_cena(self, estado):
        """Desenha linha original, janela, segmento recortado e marcações auxiliares."""
        ox0, oy0, ox1, oy1 = estado["segmento_original"]
        xmin, ymin, xmax, ymax = estado["janela"]

        desenhar_janela(xmin, ymin, xmax, ymax, cor="#1f4e79")
        reta_dda(ox0, oy0, ox1, oy1, cor="#c0392b")

        if estado["resultado"]["accepted"]:
            cx0, cy0, cx1, cy1 = estado["resultado"]["clipped"]
            reta_dda(cx0, cy0, cx1, cy1, cor="#0b8f3a")

        if not self.anotar.get():
            return

        self.canvas.delete("ANOT")
        self._desenhar_rotulo(ox0, oy0, f"P0 {estado['codes'][0]}", "#c0392b")
        self._desenhar_rotulo(ox1, oy1, f"P1 {estado['codes'][1]}", "#c0392b")
        self._desenhar_rotulo(xmin, ymin, "Jmin", "#1f4e79")
        self._desenhar_rotulo(xmax, ymax, "Jmax", "#1f4e79")
        if "centro" in estado:
            cx, cy = estado["centro"]
            self._desenhar_rotulo(cx, cy, "M", "#d68910")

        if estado["resultado"]["accepted"]:
            cx0, cy0, cx1, cy1 = estado["resultado"]["clipped"]
            self._desenhar_rotulo(cx0, cy0, "C0", "#0b8f3a")
            self._desenhar_rotulo(cx1, cy1, "C1", "#0b8f3a")

        for i, (x, y, borda) in enumerate(estado["resultado"]["intersections"], 1):
            self._desenhar_rotulo(x, y, f"I{i}-{borda[0]}", "#8e44ad")

    def _redesenhar(self):
        """Refaz a cena quando o canvas muda de tamanho ou zoom."""
        if not self._last:
            return
        self._desenhar_cena(self._last)

    def _coletar_janela(self):
        """Lê e normaliza os limites da janela independentemente da ordem digitada."""
        xmin = self.xmin.get()
        ymin = self.ymin.get()
        xmax = self.xmax.get()
        ymax = self.ymax.get()
        return normalizar_janela(xmin, ymin, xmax, ymax)

    def _montar_estado(self, x0, y0, x1, y1):
        """Agrupa todos os dados derivados do segmento para facilitar render e log."""
        xmin, ymin, xmax, ymax = self._coletar_janela()
        code0 = compute_outcode(x0, y0, xmin, ymin, xmax, ymax)
        code1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
        resultado = cohen_sutherland_clip(x0, y0, x1, y1, xmin, ymin, xmax, ymax)
        return {
            "segmento_original": (x0, y0, x1, y1),
            "janela": (xmin, ymin, xmax, ymax),
            "resultado": resultado,
            "codes": (
                f"{format_outcode(code0)} [{nomes_outcode(code0)}]",
                f"{format_outcode(code1)} [{nomes_outcode(code1)}]",
            ),
            "centro": ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0),
        }

    def _renderizar_estado(self, estado):
        """Desenha o estado atual e o salva para redraw futuro."""
        pts = []
        ligar_coleta(pts)
        try:
            self._desenhar_cena(estado)
        finally:
            desligar_coleta()
        self._last = estado

    def _preencher_lista(self, estado):
        """Converte o resultado num resumo enxuto para o painel lateral esquerdo."""
        x0, y0, x1, y1 = estado["segmento_original"]
        xmin, ymin, xmax, ymax = estado["janela"]
        resultado = estado["resultado"]

        linhas_lista = [
            f"P0 original: ({x0:.3f}, {y0:.3f})",
            f"  code: {estado['codes'][0]}",
            f"P1 original: ({x1:.3f}, {y1:.3f})",
            f"  code: {estado['codes'][1]}",
            f"Janela min: ({xmin:.3f}, {ymin:.3f})",
            f"Janela max: ({xmax:.3f}, {ymax:.3f})",
        ]

        if resultado["accepted"]:
            cx0, cy0, cx1, cy1 = resultado["clipped"]
            linhas_lista.append(f"C0: ({cx0:.3f}, {cy0:.3f})")
            linhas_lista.append(f"C1: ({cx1:.3f}, {cy1:.3f})")
        else:
            linhas_lista.append("Clipped: rejeitado")

        for i, (x, y, borda) in enumerate(resultado["intersections"], 1):
            linhas_lista.append(f"I{i} {borda}: ({x:.3f}, {y:.3f})")

        self._anotar_lista(linhas_lista)

    def _escrever_log_manual(self, estado):
        """Detalha no log o processamento completo de uma execução manual."""
        resultado = estado["resultado"]
        xmin, ymin, xmax, ymax = estado["janela"]
        self._registrar(f"Janela normalizada: xmin={xmin:g}, ymin={ymin:g}, xmax={xmax:g}, ymax={ymax:g}")
        self._registrar(f"P0 code: {estado['codes'][0]}")
        self._registrar(f"P1 code: {estado['codes'][1]}")
        self._registrar("Legenda dos bits: T B R L")
        for passo in resultado["steps"][2:]:
            self._registrar(passo)

        if resultado["accepted"]:
            cx0, cy0, cx1, cy1 = resultado["clipped"]
            self._registrar(
                f"Segmento recortado: ({cx0:.3f}, {cy0:.3f}) -> ({cx1:.3f}, {cy1:.3f})"
            )
        else:
            self._registrar("Segmento rejeitado: nenhuma parte visível dentro da janela.")

    def _escrever_log_animacao(self, estado):
        """Resume no log os dados de cada quadro da animação do segmento girando."""
        resultado = estado["resultado"]
        xmin, ymin, xmax, ymax = estado["janela"]
        x0, y0, x1, y1 = estado["segmento_original"]
        centro_x, centro_y = estado["centro"]
        diag = math.hypot(xmax - xmin, ymax - ymin)
        comprimento = math.hypot(x1 - x0, y1 - y0)

        self._iniciar_log("Animacao - Cohen-Sutherland")
        self._registrar(f"quadro={self._frame} | angulo={self.angulo.get():.2f} graus | passo horario={self.delta_angulo.get():.2f}")
        self._registrar(f"janela: xmin={xmin:g}, ymin={ymin:g}, xmax={xmax:g}, ymax={ymax:g}")
        self._registrar(f"centro da janela: ({centro_x:.3f}, {centro_y:.3f})")
        self._registrar(f"diagonal da janela={diag:.3f} | comprimento da linha={comprimento:.3f}")
        self._registrar(f"P0 code: {estado['codes'][0]}")
        self._registrar(f"P1 code: {estado['codes'][1]}")

        if resultado["accepted"]:
            cx0, cy0, cx1, cy1 = resultado["clipped"]
            self._registrar(f"clipped: ({cx0:.3f}, {cy0:.3f}) -> ({cx1:.3f}, {cy1:.3f})")
        else:
            self._registrar("clipped: rejeitado")

        if resultado["intersections"]:
            for i, (x, y, borda) in enumerate(resultado["intersections"], 1):
                self._registrar(f"I{i} {borda}: ({x:.3f}, {y:.3f})")
        else:
            self._registrar("interseções neste quadro: nenhuma")

    def _estado_linha_animada(self):
        """Gera um segmento centrado na janela para demonstrar várias situações de recorte."""
        xmin, ymin, xmax, ymax = self._coletar_janela()
        centro_x = (xmin + xmax) / 2.0
        centro_y = (ymin + ymax) / 2.0
        diagonal = math.hypot(xmax - xmin, ymax - ymin)
        fator = max(1.05, float(self.fator_comprimento.get()))
        comprimento = diagonal * fator
        meio = comprimento / 2.0
        theta = math.radians(self.angulo.get())
        dx = meio * math.cos(theta)
        dy = meio * math.sin(theta)
        x0 = centro_x - dx
        y0 = centro_y - dy
        x1 = centro_x + dx
        y1 = centro_y + dy
        return self._montar_estado(x0, y0, x1, y1)

    def parar_animacao(self):
        """Cancela o timer ativo da animação, se houver um em execução."""
        self._animando = False
        if self._after_id is not None:
            self.canvas.after_cancel(self._after_id)
            self._after_id = None

    def iniciar_animacao(self):
        """Inicia a rotação contínua do segmento de exemplo."""
        self.parar_animacao()
        self._animando = True
        self._frame = 0
        self._tick_animacao()

    def _tick_animacao(self):
        """Atualiza um quadro da animação e agenda o próximo."""
        if not self._animando:
            return

        self.canvas.delete("ANOT")
        self.quadro.limpar()
        estado = self._estado_linha_animada()
        self._renderizar_estado(estado)
        self._preencher_lista(estado)
        self._escrever_log_animacao(estado)

        self._frame += 1
        self.angulo.set(self.angulo.get() - self.delta_angulo.get())
        intervalo = max(10, int(self.intervalo_ms.get()))
        self._after_id = self.canvas.after(intervalo, self._tick_animacao)

    def desenhar(self):
        """Executa uma rodada manual do algoritmo com os valores digitados na interface."""
        self.parar_animacao()
        self.limpar()
        self._iniciar_log("Cohen-Sutherland")

        x0 = self.x0.get()
        y0 = self.y0.get()
        x1 = self.x1.get()
        y1 = self.y1.get()

        estado = self._montar_estado(x0, y0, x1, y1)
        self._renderizar_estado(estado)
        self._escrever_log_manual(estado)
        self._preencher_lista(estado)


def main():
    """Ponto de entrada isolado da interface de Cohen-Sutherland."""
    root = tk.Tk()
    root.title("Questão 2 - Cohen-Sutherland")
    AppCohenSutherland(root)
    root.mainloop()


if __name__ == "__main__":
    main()
