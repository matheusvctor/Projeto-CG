from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Callable
import uuid
import tkinter as tk
from tkinter import ttk

import numpy as np

from laboratorio_imagens import tema
from laboratorio_imagens.core.io_netpbm import ImagemNetpbm, criar_imagem, salvar_imagem


def _misturar_cores(cor_a: str, cor_b: str, proporcao: float) -> str:
    proporcao = min(max(proporcao, 0.0), 1.0)
    canais_a = [int(cor_a[indice : indice + 2], 16) for indice in (1, 3, 5)]
    canais_b = [int(cor_b[indice : indice + 2], 16) for indice in (1, 3, 5)]
    misturada = [
        round(canal_a * (1.0 - proporcao) + canal_b * proporcao)
        for canal_a, canal_b in zip(canais_a, canais_b, strict=True)
    ]
    return "#" + "".join(f"{canal:02x}" for canal in misturada)


def _ajustar_photoimage(photo: tk.PhotoImage, largura_max: int, altura_max: int) -> tk.PhotoImage:
    largura = max(photo.width(), 1)
    altura = max(photo.height(), 1)

    fator_reducao = max(
        1,
        int(np.ceil(max(largura / largura_max, altura / altura_max))),
    )
    if fator_reducao > 1:
        photo = photo.subsample(fator_reducao, fator_reducao)

    fator_ampliacao = min(
        max(1, largura_max // max(photo.width(), 1)),
        max(1, altura_max // max(photo.height(), 1)),
    )
    if fator_ampliacao > 1 and max(photo.width(), photo.height()) < min(largura_max, altura_max) // 2:
        photo = photo.zoom(fator_ampliacao, fator_ampliacao)

    return photo


def salvar_preview_temporario(matriz: np.ndarray, caminho_preview: Path) -> Path:
    # preview: grava uma copia temporaria para o Tkinter conseguir abrir a imagem
    imagem_preview = criar_imagem(np.asarray(matriz, dtype=np.uint8), nome="preview")
    salvar_imagem(imagem_preview, caminho_preview, formato="P5")
    return caminho_preview


def criar_photoimage_ajustada(
    matriz: np.ndarray,
    caminho_preview: Path,
    *,
    largura_max: int,
    altura_max: int,
) -> tk.PhotoImage:
    # escala: prepara uma PhotoImage ajustada ao espaco disponivel na interface
    salvar_preview_temporario(matriz, caminho_preview)
    photo = tk.PhotoImage(file=str(caminho_preview))
    return _ajustar_photoimage(photo, largura_max, altura_max)


def criar_photoimage_original(matriz: np.ndarray, caminho_preview: Path) -> tk.PhotoImage:
    # escala real: preserva o tamanho da matriz para exibicao 1:1 no canvas
    salvar_preview_temporario(matriz, caminho_preview)
    return tk.PhotoImage(file=str(caminho_preview))


def _normalizar_texto_status(texto: str) -> str:
    return " ".join(texto.strip().lower().split())


def _definir_estilo_status(texto: str) -> dict[str, str]:
    texto_normalizado = _normalizar_texto_status(texto)

    if any(chave in texto_normalizado for chave in ("erro", "falha", "inval", "nao foi possivel")):
        cor_base = tema.COR_ERRO
        titulo = "Erro"
    elif any(chave in texto_normalizado for chave in ("salvo", "sucesso", "concluid", "aplicad", "executad", "carregad", "pronto")):
        cor_base = tema.COR_SUCESSO
        titulo = "Sucesso"
    elif any(chave in texto_normalizado for chave in ("carregue", "aguardando", "antes de", "nao ha", "ajuste", "marque", "precisa", "selecione", "informe")):
        cor_base = tema.COR_AVISO
        titulo = "Atenção"
    else:
        cor_base = tema.COR_INFO
        titulo = "Info"

    return {
        "titulo": titulo,
        "cor_base": cor_base,
        "cor_fundo": _misturar_cores(tema.COR_PAINEL, cor_base, 0.25),
        "cor_borda": _misturar_cores(tema.COR_BORDA, cor_base, 0.60),
        "cor_texto_secundario": tema.COR_TEXTO,
    }


class BarraStatus(tk.Frame):
    def __init__(self, master, variavel_status: tk.StringVar, *, wraplength: int = 900):
        self._master_inicial = master
        self._toplevel = master.winfo_toplevel()
        
        super().__init__(self._toplevel, bg=tema.COR_FUNDO)
        self._variavel_status = variavel_status
        self._wraplength = wraplength
        self._timer_id = None
        self._anim_id = None
        
        self._trace_id = self._variavel_status.trace_add("write", self._ao_alterar_status)
        self.bind("<Destroy>", self._ao_destruir, add="+")

        self._caixa = tk.Frame(self, bd=0, highlightthickness=1)
        self._caixa.pack(fill="both", expand=True)

        self._faixa = tk.Frame(self._caixa, width=8)
        self._faixa.pack(side="left", fill="y")

        self._conteudo = tk.Frame(self._caixa, padx=14, pady=10)
        self._conteudo.pack(side="left", fill="both", expand=True)

        self._topo = tk.Frame(self._conteudo)
        self._topo.pack(fill="x")

        self._selo = tk.Label(
            self._topo,
            padx=8,
            pady=2,
            fg="#ffffff",
            font=tema.FONTE_PEQUENA,
        )
        self._selo.pack(side="left")

        self._botao_fechar = tk.Label(
            self._topo,
            text="✕",
            fg=tema.COR_TEXTO,
            cursor="hand2",
            font=("Segoe UI", 9, "bold")
        )
        self._botao_fechar.pack(side="right")
        self._botao_fechar.bind("<Button-1>", lambda e: self.ocultar())

        self._mensagem = tk.Label(
            self._conteudo,
            textvariable=self._variavel_status,
            justify="left",
            anchor="w",
            wraplength=self._wraplength,
            font=tema.FONTE_CORPO,
            pady=4,
        )
        self._mensagem.pack(fill="x")

        self._atualizar_visual()

    def pack(self, *args, **kwargs):
        pass

    def grid(self, *args, **kwargs):
        pass

    def place(self, *args, **kwargs):
        pass

    def _ao_alterar_status(self, *_args) -> None:
        self._atualizar_visual()
        texto = self._variavel_status.get().strip()
        
        if not texto or not self._master_inicial.winfo_viewable():
            self.ocultar(animar=False)
            return
            
        if any(texto.startswith(prefix) for prefix in (
            "Carregue uma imagem",
            "Carregue duas imagens",
            "Carregue uma ou duas imagens"
        )):
            return

        self.mostrar()

    def mostrar(self):
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None

        self._animar_entrada(0)
        self._timer_id = self.after(4000, lambda: self.ocultar(animar=True))

    def ocultar(self, animar=True):
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None
            
        if animar:
            self._animar_saida(0)
        else:
            super().place_forget()

    def _animar_entrada(self, passo=0):
        if passo > 8:
            super().place(relx=0.5, rely=0.88, anchor="s")
            self.lift()
            return
        
        rely_atual = 0.96 - (passo * 0.01)
        super().place(relx=0.5, rely=rely_atual, anchor="s")
        self.lift()
        self._anim_id = self.after(12, lambda: self._animar_entrada(passo + 1))

    def _animar_saida(self, passo=0):
        if passo > 8:
            super().place_forget()
            return
            
        rely_atual = 0.88 + (passo * 0.01)
        super().place(relx=0.5, rely=rely_atual, anchor="s")
        self._anim_id = self.after(12, lambda: self._animar_saida(passo + 1))

    def _ao_destruir(self, _evento) -> None:
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None
        if self._anim_id is not None:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        if self._trace_id is None:
            return
        try:
            self._variavel_status.trace_remove("write", self._trace_id)
        except tk.TclError:
            pass
        self._trace_id = None

    def _atualizar_visual(self) -> None:
        estilo = _definir_estilo_status(self._variavel_status.get())
        cor_base = estilo["cor_base"]
        cor_fundo = estilo["cor_fundo"]
        cor_borda = estilo["cor_borda"]

        self._caixa.configure(bg=cor_fundo, highlightbackground=cor_borda)
        self._faixa.configure(bg=cor_base)
        self._conteudo.configure(bg=cor_fundo)
        self._topo.configure(bg=cor_fundo)
        self._selo.configure(text=estilo["titulo"].upper(), bg=cor_base)
        self._mensagem.configure(bg=cor_fundo, fg=tema.COR_TEXTO)
        self._botao_fechar.configure(bg=cor_fundo)


def criar_barra_status(master, variavel_status: tk.StringVar, *, wraplength: int = 900) -> BarraStatus:
    return BarraStatus(master, variavel_status, wraplength=wraplength)


def criar_seletor_janela(master) -> ttk.Frame:
    if PainelImagem.tamanho_janela_compartilhado is None:
        PainelImagem.tamanho_janela_compartilhado = tk.StringVar(value="12 x 12")
        
    frame = ttk.Frame(master, style="Root.TFrame")
    ttk.Label(frame, text="Janela:", style="Texto.TLabel").pack(side="left", padx=(0, 6))
    
    seletor = ttk.Combobox(
        frame,
        textvariable=PainelImagem.tamanho_janela_compartilhado,
        values=list(PainelImagem.OPCOES_JANELA.keys()),
        state="readonly",
        width=8,
    )
    seletor.pack(side="left")
    return frame


class FrameRolavel(ttk.Frame):
    def __init__(self, master, *, padding: int = 0, style: str = "Root.TFrame"):
        super().__init__(master, padding=0, style=style)
        self._canvas = tk.Canvas(self, bg=tema.COR_FUNDO, highlightthickness=0)
        self._canvas.pack(side="left", fill="both", expand=True)

        self._barra_scroll = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._barra_scroll.pack(side="right", fill="y")
        self._canvas.configure(yscrollcommand=self._barra_scroll.set)

        self.conteudo = ttk.Frame(self._canvas, padding=padding, style=style)
        self._janela = self._canvas.create_window((0, 0), window=self.conteudo, anchor="nw")
        self.conteudo.bind("<Configure>", self._ao_configurar_conteudo)
        self._canvas.bind("<Configure>", self._ao_configurar_canvas)

        self.bind_all("<MouseWheel>", self._ao_rolar_mouse, add="+")
        self.bind_all("<Button-4>", self._ao_rolar_mouse_linux, add="+")
        self.bind_all("<Button-5>", self._ao_rolar_mouse_linux, add="+")

    def _atualizar_scrollregion(self) -> None:
        self.update_idletasks()
        bbox = self._canvas.bbox("all")
        if bbox:
            x1, y1, x2, y2 = bbox
            canvas_height = self._canvas.winfo_height()
            if y2 - y1 < canvas_height:
                y2 = y1 + canvas_height
            canvas_width = self._canvas.winfo_width()
            if x2 - x1 < canvas_width:
                x2 = x1 + canvas_width
            self._canvas.configure(scrollregion=(x1, y1, x2, y2))

    def _ao_configurar_conteudo(self, _evento) -> None:
        self._atualizar_scrollregion()

    def _ao_configurar_canvas(self, evento) -> None:
        self._canvas.itemconfigure(self._janela, width=evento.width)
        self._atualizar_scrollregion()

    def _widget_pertence_ao_frame(self, widget) -> bool:
        while widget is not None:
            if widget == self:
                return True
            nome_pai = widget.winfo_parent()
            if not nome_pai:
                break
            try:
                widget = widget.nametowidget(nome_pai)
            except KeyError:
                break
        return False

    def _ao_rolar_mouse(self, evento) -> None:
        widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        if not self.winfo_ismapped() or not self._widget_pertence_ao_frame(widget):
            return
        if evento.delta == 0:
            return
        direcao = -1 if evento.delta > 0 else 1
        passos = max(1, abs(int(evento.delta)) // 120)
        self._canvas.yview_scroll(direcao * passos, "units")

    def _ao_rolar_mouse_linux(self, evento) -> None:
        widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        if not self.winfo_ismapped() or not self._widget_pertence_ao_frame(widget):
            return
        direcao = -1 if evento.num == 4 else 1
        self._canvas.yview_scroll(direcao, "units")


class PainelImagem(ttk.LabelFrame):
    tamanho_janela_compartilhado: tk.StringVar | None = None
    OPCOES_JANELA = {
        "10 x 10": 10,
        "12 x 12": 12,
        "20 x 20": 20,
        "30 x 30": 30,
        "40 x 40": 40,
    }
    TAMANHO_GRADE_PADRAO = 220
    LARGURA_INSPECTOR = 220
    COR_BORDA_GRADE = "#334155"
    COR_DESTAQUE_GRADE = "#6366f1"

    def __init__(
        self,
        master,
        titulo: str,
        *,
        largura_max: int = 280,
        altura_max: int = 280,
        modo_exibicao: str = "ajustar",
        inspector_posicao: str = "right",
    ):
        super().__init__(master, text=titulo, padding=10)
        self.largura_max = largura_max
        self.altura_max = altura_max
        self.modo_exibicao = modo_exibicao
        self.inspector_posicao = inspector_posicao
        self._photo: tk.PhotoImage | None = None
        self._preview = Path(tempfile.gettempdir()) / f"preview_{uuid.uuid4().hex}.pgm"
        self._matriz: np.ndarray | None = None
        self._centro_atual: tuple[int, int] | None = None
        self._centro_fixado: tuple[int, int] | None = None
        self._offset_x = 0
        self._offset_y = 0
        self._largura_exibida = 0
        self._altura_exibida = 0
        self._tamanho_grade_atual = self.TAMANHO_GRADE_PADRAO
        self._observador_inspecao: Callable[[PainelImagem, tuple[int, int] | None, bool, str], None] | None = None
        self._suspender_observador = False
        
        if PainelImagem.tamanho_janela_compartilhado is None:
            PainelImagem.tamanho_janela_compartilhado = tk.StringVar(value="12 x 12")
        self.tamanho_janela = PainelImagem.tamanho_janela_compartilhado
        self._trace_janela_id = self.tamanho_janela.trace_add("write", lambda *args: self._ao_mudar_janela())
        self.bind("<Destroy>", self._ao_destruir_painel, add="+")

        self.texto_cursor = tk.StringVar(value="Passe o mouse sobre a imagem para inspecionar os pixels.")
        self.texto_janela = tk.StringVar(value="Clique esquerdo fixa a janela. Clique direito limpa a selecao.")

        self.configure(style="Card.TLabelframe")

        if self.inspector_posicao == "bottom":
            area_visual = tk.Frame(self, bg=tema.COR_PAINEL)
            area_visual.pack(fill="x", padx=6, pady=(0, 6))
            bloco_imagem = tk.Frame(area_visual, bg=tema.COR_PAINEL)
            bloco_imagem.pack(fill="x", anchor="n")
        else:
            area_visual = ttk.Frame(self, style="Root.TFrame")
            area_visual.pack(fill="x", padx=6, pady=(0, 6))
            bloco_imagem = ttk.Frame(area_visual, style="Root.TFrame")
            bloco_imagem.pack(side="left", anchor="n")

        moldura = tk.Frame(bloco_imagem, bg=tema.COR_FUNDO, width=largura_max, height=altura_max)
        moldura.pack(pady=(0, 6))
        moldura.pack_propagate(False)
        moldura.grid_rowconfigure(0, weight=1)
        moldura.grid_columnconfigure(0, weight=1)

        self.canvas_imagem = tk.Canvas(
            moldura,
            width=largura_max,
            height=altura_max,
            bg=tema.COR_FUNDO,
            highlightbackground=tema.COR_BORDA,
            highlightthickness=1,
            cursor="crosshair",
        )
        self.barra_vertical = ttk.Scrollbar(moldura, orient="vertical", command=self.canvas_imagem.yview)
        self.barra_horizontal = ttk.Scrollbar(moldura, orient="horizontal", command=self.canvas_imagem.xview)
        self.canvas_imagem.configure(
            xscrollcommand=self.barra_horizontal.set,
            yscrollcommand=self.barra_vertical.set,
        )
        self.canvas_imagem.grid(row=0, column=0, sticky="nsew")
        self.barra_vertical.grid(row=0, column=1, sticky="ns")
        self.barra_horizontal.grid(row=1, column=0, sticky="ew")
        self.canvas_imagem.bind("<Motion>", self._ao_mover_mouse)
        self.canvas_imagem.bind("<Leave>", self._ao_sair_imagem)
        self.canvas_imagem.bind("<Button-1>", self._ao_clicar_imagem)
        self.canvas_imagem.bind("<Button-3>", self._ao_limpar_selecao)

        if self.modo_exibicao != "pixels_reais":
            self.barra_vertical.grid_remove()
            self.barra_horizontal.grid_remove()

        if self.inspector_posicao in ("none", None, False):
            self.rotulo_info = tk.Label(bloco_imagem, text="Nenhuma imagem carregada.", bg=tema.COR_PAINEL, fg=tema.COR_TEXTO_MUTED, font=tema.FONTE_CORPO)
            self.rotulo_info.pack(pady=(0, 0))
            self.canvas_grade = None
            self._desenhar_imagem_vazia()
            return

        if self.inspector_posicao == "bottom":
            self.rotulo_info = tk.Label(bloco_imagem, text="Nenhuma imagem carregada.", bg=tema.COR_PAINEL, fg=tema.COR_TEXTO_MUTED, font=tema.FONTE_CORPO)
        else:
            self.rotulo_info = ttk.Label(bloco_imagem, text="Nenhuma imagem carregada.", style="Status.TLabel")
        self.rotulo_info.pack(pady=(0, 0))

        if self.inspector_posicao == "bottom":
            bloco_inspector = tk.Frame(area_visual, bg=tema.COR_PAINEL)
            bloco_inspector.pack(fill="x", anchor="n", pady=(10, 0))
            bloco_info = tk.Frame(bloco_inspector, bg=tema.COR_PAINEL)
            bloco_info.pack(side="left", fill="both", expand=True)
            bloco_grade = tk.Frame(bloco_inspector, bg=tema.COR_PAINEL)
            bloco_grade.pack(side="left", padx=(12, 0), anchor="n")
            tk.Label(bloco_info, text="Tabela sincronizada", bg=tema.COR_PAINEL, fg=tema.COR_TEXTO, font=tema.FONTE_SUBTITULO).pack(anchor="w")
            largura_texto = 130
            self.rotulo_cursor = tk.Label(bloco_info, textvariable=self.texto_cursor, bg=tema.COR_PAINEL, fg=tema.COR_TEXTO_MUTED, font=tema.FONTE_PEQUENA, wraplength=largura_texto, justify="left")
            self.rotulo_cursor.pack(anchor="w", pady=(4, 0))
            self.rotulo_janela = tk.Label(bloco_info, textvariable=self.texto_janela, bg=tema.COR_PAINEL, fg=tema.COR_TEXTO_MUTED, font=tema.FONTE_PEQUENA, wraplength=largura_texto, justify="left")
            self.rotulo_janela.pack(anchor="w", pady=(2, 0))
        else:
            bloco_inspector = ttk.Frame(area_visual, style="Root.TFrame")
            bloco_inspector.pack(side="left", anchor="n", padx=(14, 0))
            bloco_info = bloco_inspector
            bloco_grade = bloco_inspector
            ttk.Label(bloco_info, text="Tabela sincronizada", style="Card.TLabelframe.Label").pack(anchor="w")
            largura_texto = self.LARGURA_INSPECTOR
            self.rotulo_cursor = ttk.Label(bloco_info, textvariable=self.texto_cursor, style="Status.TLabel", wraplength=largura_texto, justify="left")
            self.rotulo_cursor.pack(anchor="w", pady=(4, 0))
            self.rotulo_janela = ttk.Label(bloco_info, textvariable=self.texto_janela, style="Status.TLabel", wraplength=largura_texto, justify="left")
            self.rotulo_janela.pack(anchor="w", pady=(2, 0))

        self.canvas_grade = tk.Canvas(
            bloco_grade,
            width=self._tamanho_grade_atual,
            height=self._tamanho_grade_atual,
            bg=tema.COR_FUNDO,
            highlightbackground=tema.COR_BORDA,
            highlightthickness=1,
        )
        if self.inspector_posicao == "bottom":
            self.canvas_grade.pack(anchor="ne")
        else:
            self.canvas_grade.pack(anchor="w", pady=(8, 0))
        self._desenhar_imagem_vazia()
        self._desenhar_grade_vazia()

    def _desenhar_imagem_vazia(self) -> None:
        self.canvas_imagem.delete("all")
        self.canvas_imagem.configure(scrollregion=(0, 0, self.largura_max, self.altura_max))
        self.canvas_imagem.create_text(
            self.largura_max / 2,
            self.altura_max / 2,
            text="Nenhuma imagem carregada",
            fill=tema.COR_TEXTO,
            font=tema.FONTE_CORPO,
        )

    def _desenhar_grade_vazia(self) -> None:
        if self.canvas_grade is None:
            return
        self.canvas_grade.delete("all")
        self.canvas_grade.create_text(
            self._tamanho_grade_atual / 2,
            self._tamanho_grade_atual / 2,
            text="Tabela de pixels",
            fill=tema.COR_TEXTO,
            font=tema.FONTE_CORPO,
        )

    def _obter_tamanho_janela(self) -> int:
        return self.OPCOES_JANELA.get(self.tamanho_janela.get(), 12)

    def _obter_tamanho_grade(self) -> int:
        tamanho_janela = self._obter_tamanho_janela()
        TAMANHO_MIN_CELULA = 18
        
        if self.inspector_posicao == "bottom":
            tamanhos = {
                10: 160,
                12: 192,
                20: 260,
                30: 300,
                40: 400,
            }
        elif self.largura_max >= 240:
            tamanhos = {
                10: 240,
                12: 288,
                20: 360,
                30: 420,
                40: 480,
            }
        else:
            tamanhos = {
                10: 220,
                12: 252,
                20: 300,
                30: 360,
                40: 440,
            }
        return tamanho_janela * TAMANHO_MIN_CELULA

    def _atualizar_canvas_grade(self) -> None:
        if self.canvas_grade is None:
            return
        self._tamanho_grade_atual = self._obter_tamanho_grade()
        self.canvas_grade.configure(width=self._tamanho_grade_atual, height=self._tamanho_grade_atual)

    def _ao_mudar_janela(self) -> None:
        if self._matriz is None:
            self._atualizar_canvas_grade()
            self._desenhar_grade_vazia()
            return

        self._atualizar_canvas_grade()
        centro = self._centro_fixado or self._centro_atual
        if centro is None:
            altura, largura = self._matriz.shape
            centro = (largura // 2, altura // 2)
        self._atualizar_inspecao(centro, fixada=self._centro_fixado is not None)
        self._emitir_observador_inspecao(centro, self._centro_fixado is not None)

    def _ao_mover_mouse(self, evento) -> None:
        if self._matriz is None or self._centro_fixado is not None:
            return

        pixel = self._coordenada_imagem(*self._coordenadas_canvas_evento(evento))
        if pixel is None:
            return
        self._atualizar_inspecao(pixel, fixada=False)
        self._emitir_observador_inspecao(pixel, False)

    def _ao_sair_imagem(self, _evento) -> None:
        if self._matriz is None or self._centro_fixado is not None:
            return
        self.texto_janela.set("Clique esquerdo fixa a janela. Clique direito limpa a selecao.")

    def _ao_clicar_imagem(self, evento) -> None:
        if self._matriz is None:
            return

        pixel = self._coordenada_imagem(*self._coordenadas_canvas_evento(evento))
        if pixel is None:
            return

        self._centro_fixado = pixel
        self._atualizar_inspecao(pixel, fixada=True)
        self._emitir_observador_inspecao(pixel, True)

    def _ao_limpar_selecao(self, evento) -> None:
        if self._matriz is None:
            return

        self._centro_fixado = None
        pixel = self._coordenada_imagem(*self._coordenadas_canvas_evento(evento))
        if pixel is None:
            self.texto_cursor.set("Selecao fixa removida. Passe o mouse sobre a imagem para inspecionar os pixels.")
            self.texto_janela.set("Selecao fixa removida. Passe o mouse para continuar a inspecao.")
            self._redesenhar_canvas_imagem()
            self._emitir_observador_inspecao(None, False)
            return
        self._atualizar_inspecao(pixel, fixada=False)
        self._emitir_observador_inspecao(pixel, False)

    def _ao_destruir_painel(self, _evento) -> None:
        if hasattr(self, "_trace_janela_id") and self._trace_janela_id is not None:
            try:
                self.tamanho_janela.trace_remove("write", self._trace_janela_id)
            except tk.TclError:
                pass
            self._trace_janela_id = None

    def _coordenadas_canvas_evento(self, evento) -> tuple[int, int]:
        # scroll: converte o ponto visivel do mouse para a coordenada real do canvas
        return int(self.canvas_imagem.canvasx(evento.x)), int(self.canvas_imagem.canvasy(evento.y))

    def _coordenada_imagem(self, x_canvas: int, y_canvas: int) -> tuple[int, int] | None:
        if self._matriz is None or self._largura_exibida <= 0 or self._altura_exibida <= 0:
            return None

        if not (
            self._offset_x <= x_canvas < self._offset_x + self._largura_exibida
            and self._offset_y <= y_canvas < self._offset_y + self._altura_exibida
        ):
            return None

        altura, largura = self._matriz.shape
        # mapeamento: converte o ponto exibido na tela para a grade real de pixels
        x_relativo = x_canvas - self._offset_x
        y_relativo = y_canvas - self._offset_y
        x_imagem = min(largura - 1, max(0, int(x_relativo * largura / max(self._largura_exibida, 1))))
        y_imagem = min(altura - 1, max(0, int(y_relativo * altura / max(self._altura_exibida, 1))))
        return x_imagem, y_imagem

    def definir_observador_inspecao(
        self,
        observador: Callable[[PainelImagem, tuple[int, int] | None, bool, str], None] | None,
    ) -> None:
        self._observador_inspecao = observador

    def tem_imagem(self) -> bool:
        return self._matriz is not None

    def obter_estado_inspecao(self) -> dict[str, object]:
        return {
            "centro": self._centro_fixado or self._centro_atual,
            "fixada": self._centro_fixado is not None,
            "tamanho_janela": self.tamanho_janela.get(),
        }

    def _emitir_observador_inspecao(self, centro: tuple[int, int] | None, fixada: bool) -> None:
        if self._suspender_observador or self._observador_inspecao is None:
            return
        self._observador_inspecao(self, centro, fixada, self.tamanho_janela.get())

    def aplicar_inspecao_externa(
        self,
        centro: tuple[int, int],
        *,
        fixada: bool,
        tamanho_janela: str | None = None,
    ) -> None:
        if self._matriz is None:
            return

        altura, largura = self._matriz.shape
        x_centro = min(max(int(centro[0]), 0), largura - 1)
        y_centro = min(max(int(centro[1]), 0), altura - 1)

        self._suspender_observador = True
        try:
            if tamanho_janela is not None:
                self.tamanho_janela.set(tamanho_janela)
                self._atualizar_canvas_grade()
            self._centro_fixado = (x_centro, y_centro) if fixada else None
            self._atualizar_inspecao((x_centro, y_centro), fixada=fixada)
        finally:
            self._suspender_observador = False

    def limpar_inspecao_externa(self, *, tamanho_janela: str | None = None) -> None:
        if self._matriz is None:
            return

        self._suspender_observador = True
        try:
            if tamanho_janela is not None:
                self.tamanho_janela.set(tamanho_janela)
                self._atualizar_canvas_grade()
            self._centro_fixado = None
            if self._centro_atual is not None:
                self._atualizar_inspecao(self._centro_atual, fixada=False)
            else:
                self._redesenhar_canvas_imagem()
        finally:
            self._suspender_observador = False

    def _calcular_janela(
        self,
        x_centro: int,
        y_centro: int,
    ) -> tuple[np.ndarray, int, int, int, int, int, int]:
        assert self._matriz is not None
        altura, largura = self._matriz.shape
        tamanho = self._obter_tamanho_janela()
        metade = tamanho // 2

        x_inicial = x_centro - metade
        y_inicial = y_centro - metade
        x_final = x_inicial + tamanho
        y_final = y_inicial + tamanho

        if x_inicial < 0:
            x_final -= x_inicial
            x_inicial = 0
        if y_inicial < 0:
            y_final -= y_inicial
            y_inicial = 0
        if x_final > largura:
            x_inicial = max(0, x_inicial - (x_final - largura))
            x_final = largura
        if y_final > altura:
            y_inicial = max(0, y_inicial - (y_final - altura))
            y_final = altura

        janela = self._matriz[y_inicial:y_final, x_inicial:x_final]
        pixel_local_x = x_centro - x_inicial
        pixel_local_y = y_centro - y_inicial
        return janela, x_inicial, y_inicial, x_final, y_final, pixel_local_x, pixel_local_y

    def _atualizar_inspecao(self, centro: tuple[int, int], *, fixada: bool) -> None:
        if self._matriz is None:
            return

        x_centro, y_centro = centro
        self._centro_atual = centro
        janela, x_inicial, y_inicial, x_final, y_final, pixel_local_x, pixel_local_y = self._calcular_janela(
            x_centro,
            y_centro,
        )

        valor = int(self._matriz[y_centro, x_centro])
        modo = "fixada" if fixada else "tempo real"
        self.texto_cursor.set(f"Pixel ({x_centro}, {y_centro}) | valor {valor} | leitura {modo}.")
        prefixo = "Janela fixada" if fixada else "Janela acompanhando o mouse"
        self.texto_janela.set(
            f"{prefixo}: {janela.shape[1]}x{janela.shape[0]} cobrindo x={x_inicial}:{x_final - 1} e y={y_inicial}:{y_final - 1}."
        )

        self._desenhar_grade(janela, pixel_local_x, pixel_local_y)
        self._redesenhar_canvas_imagem()

    def _desenhar_grade(self, janela: np.ndarray, pixel_local_x: int, pixel_local_y: int) -> None:
        if self.canvas_grade is None:
            return
        self.canvas_grade.delete("all")
        altura, largura = janela.shape
        if altura == 0 or largura == 0:
            self._desenhar_grade_vazia()
            return

        largura_celula = self._tamanho_grade_atual / max(largura, 1)
        altura_celula = self._tamanho_grade_atual / max(altura, 1)
        menor_celula = min(largura_celula, altura_celula)
        tamanho_fonte = max(6, int(menor_celula * 0.425))
        mostrar_texto = menor_celula >= 6

        for linha in range(altura):
            for coluna in range(largura):
                valor = int(janela[linha, coluna])
                cor = f"#{valor:02x}{valor:02x}{valor:02x}"
                x0 = coluna * largura_celula
                y0 = linha * altura_celula
                x1 = x0 + largura_celula
                y1 = y0 + altura_celula
                destaque = linha == pixel_local_y and coluna == pixel_local_x

                self.canvas_grade.create_rectangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    fill=cor,
                    outline=self.COR_DESTAQUE_GRADE if destaque else self.COR_BORDA_GRADE,
                    width=2 if destaque else 1,
                )
                if mostrar_texto:
                    cor_texto = "white" if valor < 120 else tema.COR_TEXTO
                    
                    if menor_celula >= 14:
                        texto = str(valor)
                    else:
                        texto = str(valor)[-2:]
                        
                    self.canvas_grade.create_text(
                        (x0 + x1) / 2,
                        (y0 + y1) / 2,
                        text=texto,
                        fill=cor_texto,
                        font=("Consolas", tamanho_fonte, "bold"),
                    )

        self.canvas_grade.create_rectangle(
            1,
            1,
            self._tamanho_grade_atual - 1,
            self._tamanho_grade_atual - 1,
            outline=self.COR_BORDA_GRADE,
            width=2,
        )

    def _redesenhar_canvas_imagem(self) -> None:
        self.canvas_imagem.delete("all")

        if self._photo is None:
            self._desenhar_imagem_vazia()
            return

        self.canvas_imagem.create_image(self._offset_x, self._offset_y, anchor="nw", image=self._photo)
        if self._centro_fixado is not None:
            self._desenhar_selecao_fixada(self._centro_fixado)

    def _desenhar_selecao_fixada(self, centro: tuple[int, int]) -> None:
        if self._matriz is None:
            return

        x_centro, y_centro = centro
        janela, x_inicial, y_inicial, x_final, y_final, _, _ = self._calcular_janela(x_centro, y_centro)
        if janela.size == 0:
            return

        altura, largura = self._matriz.shape
        # overlay: desenha na imagem a mesma regiao exibida na tabela fixada
        esquerda = self._offset_x + (x_inicial / max(largura, 1)) * self._largura_exibida
        topo = self._offset_y + (y_inicial / max(altura, 1)) * self._altura_exibida
        direita = self._offset_x + (x_final / max(largura, 1)) * self._largura_exibida
        base = self._offset_y + (y_final / max(altura, 1)) * self._altura_exibida
        self.canvas_imagem.create_rectangle(
            esquerda,
            topo,
            direita,
            base,
            outline=tema.COR_DESTAQUE,
            width=2,
        )

        pixel_esquerda = self._offset_x + (x_centro / max(largura, 1)) * self._largura_exibida
        pixel_topo = self._offset_y + (y_centro / max(altura, 1)) * self._altura_exibida
        pixel_direita = self._offset_x + ((x_centro + 1) / max(largura, 1)) * self._largura_exibida
        pixel_base = self._offset_y + ((y_centro + 1) / max(altura, 1)) * self._altura_exibida
        self.canvas_imagem.create_rectangle(
            pixel_esquerda,
            pixel_topo,
            pixel_direita,
            pixel_base,
            outline=tema.COR_SUCESSO,
            width=2,
        )

    def mostrar_imagem(self, imagem: ImagemNetpbm | np.ndarray, *, texto_info: str | None = None) -> None:
        # exibicao: recebe a matriz e atualiza a imagem mostrada no painel
        matriz = imagem.matriz if isinstance(imagem, ImagemNetpbm) else np.asarray(imagem, dtype=np.uint8)
        self._matriz = np.asarray(matriz, dtype=np.uint8)
        self._centro_atual = None
        self._centro_fixado = None
        if self.modo_exibicao == "pixels_reais":
            # escala real: cada pixel da matriz ocupa um pixel da imagem exibida
            self._photo = criar_photoimage_original(self._matriz, self._preview)
            self.barra_vertical.grid()
            self.barra_horizontal.grid()
        else:
            self._photo = criar_photoimage_ajustada(
                self._matriz,
                self._preview,
                largura_max=self.largura_max,
                altura_max=self.altura_max,
            )
            self.barra_vertical.grid_remove()
            self.barra_horizontal.grid_remove()
        self._atualizar_canvas_grade()
        self._largura_exibida = self._photo.width()
        self._altura_exibida = self._photo.height()
        area_largura = max(self.largura_max, self._largura_exibida)
        area_altura = max(self.altura_max, self._altura_exibida)
        self._offset_x = max((area_largura - self._largura_exibida) // 2, 0)
        self._offset_y = max((area_altura - self._altura_exibida) // 2, 0)
        self.canvas_imagem.configure(scrollregion=(0, 0, area_largura, area_altura))
        self.canvas_imagem.xview_moveto(0)
        self.canvas_imagem.yview_moveto(0)
        self._redesenhar_canvas_imagem()
        self.rotulo_info.configure(
            text=texto_info
            or f"{self._matriz.shape[1]} x {self._matriz.shape[0]} pixels",
        )
        centro = (self._matriz.shape[1] // 2, self._matriz.shape[0] // 2)
        self._atualizar_inspecao(centro, fixada=False)

    def limpar(self, mensagem: str = "Nenhuma imagem carregada.") -> None:
        self._photo = None
        self._matriz = None
        self._centro_atual = None
        self._centro_fixado = None
        self._largura_exibida = 0
        self._altura_exibida = 0
        self._offset_x = 0
        self._offset_y = 0
        self._atualizar_canvas_grade()
        self._desenhar_imagem_vazia()
        self._desenhar_grade_vazia()
        self.texto_cursor.set("Passe o mouse sobre a imagem para inspecionar os pixels.")
        self.texto_janela.set("Clique esquerdo fixa a janela. Clique direito limpa a selecao.")
        self.rotulo_info.configure(text=mensagem)


class SincronizadorPaineisImagem:
    def __init__(self, paineis: list[PainelImagem]):
        self.paineis = paineis
        self.habilitado = False
        for painel in self.paineis:
            painel.definir_observador_inspecao(self._ao_receber_inspecao)

    def definir_habilitado(self, habilitado: bool) -> None:
        # espelhamento: quando ativo, replica a mesma leitura de pixels nos outros paineis do grupo
        self.habilitado = habilitado
        if self.habilitado:
            self._sincronizar_estado_existente()

    def _sincronizar_estado_existente(self) -> None:
        for painel in self.paineis:
            if not painel.tem_imagem():
                continue
            estado = painel.obter_estado_inspecao()
            centro = estado["centro"]
            if centro is None:
                continue
            self._ao_receber_inspecao(
                painel,
                centro,
                bool(estado["fixada"]),
                str(estado["tamanho_janela"]),
            )
            return

    def _ao_receber_inspecao(
        self,
        origem: PainelImagem,
        centro: tuple[int, int] | None,
        fixada: bool,
        tamanho_janela: str,
    ) -> None:
        if not self.habilitado:
            return

        for painel in self.paineis:
            if painel is origem:
                continue
            if centro is None:
                painel.limpar_inspecao_externa(tamanho_janela=tamanho_janela)
            else:
                painel.aplicar_inspecao_externa(centro, fixada=fixada, tamanho_janela=tamanho_janela)


class GraficoHistograma(ttk.LabelFrame):
    def __init__(self, master, titulo: str, *, largura: int = 320, altura: int = 180):
        super().__init__(master, text=titulo, padding=8)
        self.configure(style="Card.TLabelframe")
        self.largura = largura
        self.altura = altura
        self._histograma_atual = np.zeros(256, dtype=np.float64)
        self._cor_atual = tema.COR_DESTAQUE
        self.canvas = tk.Canvas(
            self,
            width=largura,
            height=altura,
            bg=tema.COR_FUNDO,
            highlightbackground=tema.COR_BORDA,
            highlightthickness=1,
        )
        self.canvas.pack(fill="both", expand=True)

    def obter_estado(self) -> tuple[np.ndarray, str]:
        return self._histograma_atual.copy(), self._cor_atual

    def ajustar_tamanho(self, largura: int, altura: int) -> None:
        self.largura = max(int(largura), 240)
        self.altura = max(int(altura), 160)
        self.canvas.configure(width=self.largura, height=self.altura)
        self.desenhar(self._histograma_atual, cor=self._cor_atual)

    def desenhar(self, histograma: np.ndarray, *, cor: str = tema.COR_DESTAQUE) -> None:
        # desenho: usa eixos, grade e barras preenchidas para deixar a leitura mais clara
        self._histograma_atual = np.asarray(histograma, dtype=np.float64).reshape(-1).copy()
        self._cor_atual = cor
        self.canvas.delete("all")
        valores = self._histograma_atual
        if valores.size == 0 or np.max(valores) == 0:
            self.canvas.create_text(
                self.largura / 2,
                self.altura / 2,
                text="Histograma indisponivel",
                fill=tema.COR_TEXTO_MUTED,
                font=tema.FONTE_CORPO,
            )
            return

        maximo = float(np.max(valores))
        total_pixels = int(np.sum(valores))
        margem_esquerda = 44
        margem_direita = 18
        margem_superior = 20
        margem_inferior = 30
        esquerda = margem_esquerda
        direita = self.largura - margem_direita
        topo = margem_superior
        base = self.altura - margem_inferior
        largura_grafico = max(direita - esquerda, 1)
        altura_grafico = max(base - topo, 1)
        cor_grade = tema.COR_BORDA
        cor_barras = cor
        cor_realce = tema.COR_DESTAQUE_SUAVE

        self.canvas.create_rectangle(
            esquerda,
            topo,
            direita,
            base,
            fill=tema.COR_PAINEL,
            outline=tema.COR_BORDA,
            width=1,
        )

        for proporcao in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = base - proporcao * altura_grafico
            self.canvas.create_line(esquerda, y, direita, y, fill=cor_grade, dash=(2, 4))
            self.canvas.create_text(
                esquerda - 6,
                y,
                text=str(int(round(maximo * proporcao))),
                anchor="e",
                fill=tema.COR_TEXTO_MUTED,
                font=tema.FONTE_PEQUENA,
            )

        for nivel in (0, 64, 128, 192, 255):
            x = esquerda + (nivel / 255.0) * largura_grafico
            self.canvas.create_line(x, topo, x, base, fill=cor_grade, dash=(2, 4))
            self.canvas.create_text(
                x,
                base + 14,
                text=str(nivel),
                anchor="n",
                fill=tema.COR_TEXTO_MUTED,
                font=tema.FONTE_PEQUENA,
            )

        largura_barra = largura_grafico / 256.0
        for indice, valor in enumerate(valores[:256]):
            altura_barra = (valor / maximo) * altura_grafico
            x0 = esquerda + indice * largura_barra
            x1 = esquerda + (indice + 1) * largura_barra
            y0 = base - altura_barra
            if x1 - x0 < 1.5:
                self.canvas.create_line(x0, base, x0, y0, fill=cor_barras)
                continue
            self.canvas.create_rectangle(x0, y0, x1, base, fill=cor_barras, outline="")
            self.canvas.create_line(x0, y0, x1, y0, fill=cor_realce)

        self.canvas.create_line(esquerda, base, direita, base, fill=tema.COR_TEXTO_MUTED, width=1)
        self.canvas.create_line(esquerda, topo, esquerda, base, fill=tema.COR_TEXTO_MUTED, width=1)
        self.canvas.create_text(
            esquerda,
            10,
            text=f"Pico: {int(maximo)}",
            anchor="w",
            fill=tema.COR_INFO,
            font=tema.FONTE_PEQUENA,
        )
        self.canvas.create_text(
            direita,
            10,
            text=f"Pixels: {total_pixels}",
            anchor="e",
            fill=tema.COR_TEXTO_MUTED,
            font=tema.FONTE_PEQUENA,
        )



