from __future__ import annotations

from pathlib import Path
import queue
import tempfile
import threading
import uuid
import tkinter as tk
from tkinter import filedialog, ttk

from laboratorio_imagens import tema
from laboratorio_imagens.core.exemplos_morfismo import (
    carregar_exemplo_luiz as carregar_exemplo_luiz_padrao,
    exemplo_luiz_disponivel,
)
from laboratorio_imagens.core.io_netpbm import ImagemNetpbm, criar_imagem, salvar_imagem
from laboratorio_imagens.core.morfismo import (
    PreparacaoMorfismo,
    contar_mudancas_entre_imagens,
    gerar_frame_preparado,
    gerar_frame_morfado,
    gerar_sequencia_preparada,
    gerar_sequencia_morfismo,
    gerar_tempos_uniformes,
    preparar_morfismo,
    redimensionar_para_limite,
    salvar_gif_animado,
)
from laboratorio_imagens.core.operacoes_morfologicas import (
    ELEMENTOS_ESTRUTURANTES,
    MASCARAS_HIT_OR_MISS,
    abertura_binaria,
    abertura_cinza,
    bottom_hat_binario,
    bottom_hat_cinza,
    contorno_externo_binario,
    contorno_externo_cinza,
    contorno_interno_binario,
    contorno_interno_cinza,
    dilatacao_binaria,
    dilatacao_cinza,
    erosao_binaria,
    erosao_cinza,
    fechamento_binaria,
    fechamento_cinza,
    gradiente_morfologico_binario,
    gradiente_morfologico_cinza,
    hit_or_miss,
    top_hat_binario,
    top_hat_cinza,
)
from laboratorio_imagens.core.transformacoes_geometricas import cisalhar, escalar, refletir, rotacionar, transladar
from laboratorio_imagens.core.utilidades_matriz import limiarizar_pela_media, limiarizar_por_valor
from laboratorio_imagens.ui.abas_processamento import (
    TIPOS_IMAGEM,
    _abrir_dialogo_imagem,
    _descricao_imagem,
    _salvar_dialogo_resultado,
)
from laboratorio_imagens.ui.widgets import PainelImagem, SincronizadorPaineisImagem, criar_barra_status, criar_photoimage_ajustada, criar_seletor_janela


class AbaMorfologia(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12, style="Root.TFrame")
        self.imagem_origem: ImagemNetpbm | None = None
        self.imagem_resultado: ImagemNetpbm | None = None
        self.sincronizar_tabelas = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Carregue uma imagem para executar morfologia binaria ou em nivel de cinza.")
        self.modo_operacao = tk.StringVar(value="Binaria")
        self.operacao = tk.StringVar(value="Dilatacao")
        self.elemento = tk.StringVar(value="Quadrado 3x3")
        self.limiar = tk.StringVar(value="")
        self.mascara_hit = tk.StringVar(value="Ponto isolado")
        self._sincronizador_pixels: SincronizadorPaineisImagem | None = None
        self._montar_interface()
        self._ao_mudar_modo()

    def _montar_interface(self) -> None:
        barra = ttk.Frame(self, style="Root.TFrame")
        barra.pack(fill="x", pady=(0, 12))

        ttk.Button(barra, text="Carregar imagem", command=self.carregar_imagem).pack(side="left")
        ttk.Button(barra, text="Limpar", command=self.limpar_imagens).pack(side="left", padx=(8, 0))
        criar_seletor_janela(barra).pack(side="left", padx=(12, 0))

        ttk.Label(barra, text="Modo:", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        combo_modo = ttk.Combobox(
            barra,
            textvariable=self.modo_operacao,
            values=["Binaria", "Nivel de cinza"],
            state="readonly",
            width=16,
        )
        combo_modo.pack(side="left")
        combo_modo.bind("<<ComboboxSelected>>", lambda _evento: self._ao_mudar_modo())

        ttk.Label(barra, text="Operacao:", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        self.combo_operacao = ttk.Combobox(barra, textvariable=self.operacao, state="readonly", width=20)
        self.combo_operacao.pack(side="left")

        ttk.Label(barra, text="Elemento:", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        ttk.Combobox(
            barra,
            textvariable=self.elemento,
            values=list(ELEMENTOS_ESTRUTURANTES.keys()),
            state="readonly",
            width=16,
        ).pack(side="left")

        ttk.Label(barra, text="Limiar:", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        ttk.Entry(barra, textvariable=self.limiar, width=8).pack(side="left")

        ttk.Label(barra, text="Mascara H/M:", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        self.combo_hit = ttk.Combobox(
            barra,
            textvariable=self.mascara_hit,
            values=list(MASCARAS_HIT_OR_MISS.keys()),
            state="readonly",
            width=18,
        )
        self.combo_hit.pack(side="left")

        ttk.Button(barra, text="Aplicar", command=self.aplicar_operacao).pack(side="left", padx=(12, 0))
        ttk.Button(barra, text="Salvar resultado", command=self.salvar_resultado).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(
            barra,
            text="Sincronizar tabelas",
            variable=self.sincronizar_tabelas,
            command=lambda: self._sincronizador_pixels.definir_habilitado(self.sincronizar_tabelas.get()),
        ).pack(side="left", padx=(10, 0))

        paineis = ttk.Frame(self, style="Root.TFrame")
        paineis.pack(fill="both", expand=True)
        paineis.columnconfigure(0, weight=1)
        paineis.columnconfigure(1, weight=1)

        self.painel_original = PainelImagem(paineis, "Entrada")
        self.painel_original.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.painel_resultado = PainelImagem(paineis, "Resultado morfologico")
        self.painel_resultado.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self._sincronizador_pixels = SincronizadorPaineisImagem([self.painel_original, self.painel_resultado])

        criar_barra_status(self, self.status).pack(fill="x", pady=(10, 0))

    def _ao_mudar_modo(self) -> None:
        if self.modo_operacao.get() == "Binaria":
            operacoes = [
                "Dilatacao",
                "Erosao",
                "Abertura",
                "Fechamento",
                "Hit-or-miss",
                "Contorno interno",
                "Contorno externo",
                "Gradiente morfologico",
                "Top-hat",
                "Bottom-hat",
            ]
            self.combo_hit.configure(state="readonly")
        else:
            operacoes = [
                "Dilatacao",
                "Erosao",
                "Abertura",
                "Fechamento",
                "Contorno interno",
                "Contorno externo",
                "Gradiente morfologico",
                "Top-hat",
                "Bottom-hat",
            ]
            self.combo_hit.configure(state="disabled")
            if self.operacao.get() == "Hit-or-miss":
                self.operacao.set("Dilatacao")
        self.combo_operacao.configure(values=operacoes)
        if self.operacao.get() not in operacoes:
            self.operacao.set(operacoes[0])

    def carregar_imagem(self) -> None:
        imagem = _abrir_dialogo_imagem()
        if imagem is None:
            return
        self.imagem_origem = imagem
        self.imagem_resultado = None
        self.painel_original.mostrar_imagem(imagem, texto_info=_descricao_imagem(imagem))
        self.painel_resultado.limpar("Aguardando operacao.")
        self.status.set(f"Imagem carregada: {_descricao_imagem(imagem)}")

    def limpar_imagens(self) -> None:
        self.imagem_origem = None
        self.imagem_resultado = None
        self.painel_original.limpar()
        self.painel_resultado.limpar()
        self.status.set("Imagens removidas. Carregue uma imagem para executar morfologia.")

    def _obter_matriz_entrada(self) -> tuple[ImagemNetpbm, bool]:
        assert self.imagem_origem is not None
        if self.modo_operacao.get() == "Nivel de cinza":
            return self.imagem_origem, False

        # binarizacao: se a imagem nao for binaria, gera uma versao PBM para as operacoes binarias
        if self.imagem_origem.binaria:
            return self.imagem_origem, False

        if self.limiar.get():
            limiar = int(float(self.limiar.get()))
            matriz_binaria = limiarizar_por_valor(self.imagem_origem.matriz, limiar)
            return criar_imagem(matriz_binaria, nome=f"{self.imagem_origem.nome}_binaria", binaria=True), True

        matriz_binaria = limiarizar_pela_media(self.imagem_origem.matriz)
        return criar_imagem(matriz_binaria, nome=f"{self.imagem_origem.nome}_binaria", binaria=True), True

    def aplicar_operacao(self) -> None:
        if self.imagem_origem is None:
            self.status.set("Carregue uma imagem antes de aplicar a morfologia.")
            return

        try:
            imagem_entrada, entrada_binarizada = self._obter_matriz_entrada()
        except ValueError as erro:
            self.status.set(f"Limiar invalido: {erro}")
            return
        elemento = ELEMENTOS_ESTRUTURANTES[self.elemento.get()]
        operacao = self.operacao.get()

        if self.modo_operacao.get() == "Binaria":
            # morfologia binaria: usa mascara logica e devolve uma imagem PBM-like
            base = imagem_entrada.matriz
            mapa = {
                "Dilatacao": dilatacao_binaria,
                "Erosao": erosao_binaria,
                "Abertura": abertura_binaria,
                "Fechamento": fechamento_binaria,
                "Contorno interno": contorno_interno_binario,
                "Contorno externo": contorno_externo_binario,
                "Gradiente morfologico": gradiente_morfologico_binario,
                "Top-hat": top_hat_binario,
                "Bottom-hat": bottom_hat_binario,
            }
            if operacao == "Hit-or-miss":
                resultado = hit_or_miss(base, MASCARAS_HIT_OR_MISS[self.mascara_hit.get()])
            else:
                resultado = mapa[operacao](base, elemento)
            self.imagem_resultado = criar_imagem(resultado, nome=f"morfologia_{operacao.lower()}", binaria=True)
        else:
            # morfologia em cinza: usa maximos/minimos locais na vizinhanca
            base = self.imagem_origem.matriz
            mapa = {
                "Dilatacao": dilatacao_cinza,
                "Erosao": erosao_cinza,
                "Abertura": abertura_cinza,
                "Fechamento": fechamento_cinza,
                "Contorno interno": contorno_interno_cinza,
                "Contorno externo": contorno_externo_cinza,
                "Gradiente morfologico": gradiente_morfologico_cinza,
                "Top-hat": top_hat_cinza,
                "Bottom-hat": bottom_hat_cinza,
            }
            resultado = mapa[operacao](base, elemento)
            self.imagem_resultado = criar_imagem(resultado, nome=f"morfologia_{operacao.lower()}")

        if entrada_binarizada:
            self.painel_original.mostrar_imagem(imagem_entrada, texto_info="Entrada binarizada automaticamente")
        else:
            self.painel_original.mostrar_imagem(imagem_entrada, texto_info=_descricao_imagem(imagem_entrada))
        self.painel_resultado.mostrar_imagem(self.imagem_resultado, texto_info=_descricao_imagem(self.imagem_resultado))
        self.status.set(f"Operacao morfologica '{operacao}' aplicada com sucesso.")

    def salvar_resultado(self) -> None:
        if self.imagem_resultado is None:
            self.status.set("Nao ha resultado para salvar.")
            return
        caminho = _salvar_dialogo_resultado(self.imagem_resultado)
        if caminho is not None:
            self.status.set(f"Resultado salvo em: {caminho}")


class AbaGeometria(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12, style="Root.TFrame")
        self.imagem_origem: ImagemNetpbm | None = None
        self.imagem_resultado: ImagemNetpbm | None = None
        self.sincronizar_tabelas = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Carregue uma imagem para aplicar escala, translacao, reflexao, cisalhamento e rotacao.")
        self.transformacao = tk.StringVar(value="Escala")
        self.parametro_1 = tk.StringVar(value="1.2")
        self.parametro_2 = tk.StringVar(value="1.2")
        self.reflexao = tk.StringVar(value="Horizontal")
        self.rotulo_parametro_1 = tk.StringVar(value="Fator X")
        self.rotulo_parametro_2 = tk.StringVar(value="Fator Y")
        self._sincronizador_pixels: SincronizadorPaineisImagem | None = None
        self._montar_interface()
        self._ao_mudar_transformacao()

    def _montar_interface(self) -> None:
        barra = ttk.Frame(self, style="Root.TFrame")
        barra.pack(fill="x", pady=(0, 12))

        ttk.Button(barra, text="Carregar imagem", command=self.carregar_imagem).pack(side="left")
        ttk.Button(barra, text="Limpar", command=self.limpar_imagens).pack(side="left", padx=(8, 0))
        criar_seletor_janela(barra).pack(side="left", padx=(12, 0))
        ttk.Label(barra, text="Transformacao:", style="Texto.TLabel").pack(side="left", padx=(12, 6))

        seletor = ttk.Combobox(
            barra,
            textvariable=self.transformacao,
            values=["Escala", "Translacao", "Reflexao", "Cisalhamento", "Rotacao"],
            state="readonly",
            width=18,
        )
        seletor.pack(side="left")
        seletor.bind("<<ComboboxSelected>>", lambda _evento: self._ao_mudar_transformacao())

        ttk.Label(barra, textvariable=self.rotulo_parametro_1, style="Texto.TLabel").pack(side="left", padx=(12, 6))
        self.entrada_1 = ttk.Entry(barra, textvariable=self.parametro_1, width=10)
        self.entrada_1.pack(side="left")

        ttk.Label(barra, textvariable=self.rotulo_parametro_2, style="Texto.TLabel").pack(side="left", padx=(12, 6))
        self.entrada_2 = ttk.Entry(barra, textvariable=self.parametro_2, width=10)
        self.entrada_2.pack(side="left")

        ttk.Label(barra, text="Eixo:", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        self.combo_reflexao = ttk.Combobox(
            barra,
            textvariable=self.reflexao,
            values=["Horizontal", "Vertical", "Ambos"],
            state="readonly",
            width=12,
        )
        self.combo_reflexao.pack(side="left")

        ttk.Button(barra, text="Aplicar", command=self.aplicar_transformacao).pack(side="left", padx=(12, 0))
        ttk.Button(barra, text="Salvar resultado", command=self.salvar_resultado).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(
            barra,
            text="Sincronizar tabelas",
            variable=self.sincronizar_tabelas,
            command=lambda: self._sincronizador_pixels.definir_habilitado(self.sincronizar_tabelas.get()),
        ).pack(side="left", padx=(10, 0))

        paineis = ttk.Frame(self, style="Root.TFrame")
        paineis.pack(fill="both", expand=True)
        paineis.columnconfigure(0, weight=1)
        paineis.columnconfigure(1, weight=1)

        # escala visual: na geometria a exibicao usa modo ajustar para nao exibir barras de rolagem
        self.painel_original = PainelImagem(
            paineis,
            "Imagem original",
            largura_max=280,
            altura_max=280,
            modo_exibicao="ajustar",
        )
        self.painel_original.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.painel_resultado = PainelImagem(
            paineis,
            "Transformacao geometrica",
            largura_max=280,
            altura_max=280,
            modo_exibicao="ajustar",
        )
        self.painel_resultado.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self._sincronizador_pixels = SincronizadorPaineisImagem([self.painel_original, self.painel_resultado])

        criar_barra_status(self, self.status).pack(fill="x", pady=(10, 0))

    def _ao_mudar_transformacao(self) -> None:
        nome = self.transformacao.get()
        configuracoes = {
            "Escala": ("Fator X", "Fator Y", "1.2", "1.2", True, True, False),
            "Translacao": ("dx", "dy", "50", "30", True, True, False),
            "Reflexao": ("", "", "", "", False, False, True),
            "Cisalhamento": ("Fator X", "Fator Y", "0.3", "0.0", True, True, False),
            "Rotacao": ("Angulo", "", "30", "", True, False, False),
        }
        rotulo_1, rotulo_2, valor_1, valor_2, usa_1, usa_2, usa_combo = configuracoes[nome]
        self.rotulo_parametro_1.set(rotulo_1 or "Parametro 1")
        self.rotulo_parametro_2.set(rotulo_2 or "Parametro 2")
        self.parametro_1.set(valor_1)
        self.parametro_2.set(valor_2)
        self.entrada_1.configure(state="normal" if usa_1 else "disabled")
        self.entrada_2.configure(state="normal" if usa_2 else "disabled")
        self.combo_reflexao.configure(state="readonly" if usa_combo else "disabled")

    def carregar_imagem(self) -> None:
        imagem = _abrir_dialogo_imagem()
        if imagem is None:
            return
        self.imagem_origem = imagem
        self.imagem_resultado = None
        self.painel_original.mostrar_imagem(imagem, texto_info=_descricao_imagem(imagem))
        self.painel_resultado.limpar("Aguardando transformacao.")
        self.status.set(f"Imagem carregada: {_descricao_imagem(imagem)}")

    def limpar_imagens(self) -> None:
        self.imagem_origem = None
        self.imagem_resultado = None
        self.painel_original.limpar()
        self.painel_resultado.limpar()
        self.status.set("Imagens removidas. Carregue uma imagem para aplicar uma transformacao geometrica.")

    def aplicar_transformacao(self) -> None:
        if self.imagem_origem is None:
            self.status.set("Carregue uma imagem antes de aplicar uma transformacao.")
            return

        base = self.imagem_origem.matriz
        nome = self.transformacao.get()
        try:
            # afim: seleciona a transformacao geometrica e aplica sobre a matriz da imagem
            if nome == "Escala":
                resultado = escalar(base, float(self.parametro_1.get()), float(self.parametro_2.get()))
            elif nome == "Translacao":
                resultado = transladar(base, float(self.parametro_1.get()), float(self.parametro_2.get()))
            elif nome == "Reflexao":
                resultado = refletir(base, self.reflexao.get())
            elif nome == "Cisalhamento":
                resultado = cisalhar(base, float(self.parametro_1.get()), float(self.parametro_2.get()))
            else:
                resultado = rotacionar(base, float(self.parametro_1.get()))
        except ValueError as erro:
            self.status.set(f"Parametros invalidos: {erro}")
            return

        self.imagem_resultado = criar_imagem(resultado, nome=f"transformacao_{nome.lower()}")
        self.painel_resultado.mostrar_imagem(self.imagem_resultado, texto_info=_descricao_imagem(self.imagem_resultado))
        self.status.set(f"Transformacao '{nome}' aplicada com sucesso.")

    def salvar_resultado(self) -> None:
        if self.imagem_resultado is None:
            self.status.set("Nao ha resultado para salvar.")
            return
        caminho = _salvar_dialogo_resultado(self.imagem_resultado)
        if caminho is not None:
            self.status.set(f"Resultado salvo em: {caminho}")
class AbaMorfismo(ttk.Frame):
    TAMANHO_CANVAS = 360
    ATRASO_PREVIEW_MS = 90
    INTERVALO_ANIMACAO_MS = 120
    PASSO_ANIMACAO = 0.05
    LIMITE_DIMENSAO_TRABALHO = 320

    def __init__(self, master):
        super().__init__(master, padding=0, style="Root.TFrame")
        self.imagem_inicial: ImagemNetpbm | None = None
        self.imagem_final: ImagemNetpbm | None = None
        self.imagem_resultado: ImagemNetpbm | None = None
        self.status = tk.StringVar(value="Carregue duas imagens e marque pontos correspondentes na mesma ordem para gerar o morfismo.")
        self.tempo = tk.DoubleVar(value=0.5)
        self.rotulo_tempo = tk.StringVar(value="t = 0.50")
        self.rotulo_animacao = tk.StringVar(value="Animar")
        self.rotulo_salvar_animacao = tk.StringVar(value="Salvar animacao")
        self.contagem_pontos = tk.StringVar(value="Pontos: 0 na imagem inicial | 0 na imagem final")
        self.total_quadros_animacao = tk.StringVar(value="18")
        self.atraso_animacao_ms = tk.StringVar(value="75")
        self.pontos_iniciais: list[tuple[float, float]] = []
        self.pontos_finais: list[tuple[float, float]] = []
        self.previews = {
            "inicial": Path(tempfile.gettempdir()) / f"morfismo_inicial_{uuid.uuid4().hex}.pgm",
            "final": Path(tempfile.gettempdir()) / f"morfismo_final_{uuid.uuid4().hex}.pgm",
        }
        self.estado_canvases = {
            "inicial": {"photo": None, "offset_x": 0, "offset_y": 0, "largura": 0, "altura": 0},
            "final": {"photo": None, "offset_x": 0, "offset_y": 0, "largura": 0, "altura": 0},
        }
        self._preview_after_id: str | None = None
        self._preview_em_andamento = False
        self._preview_requisicao_atual = 0
        self._preview_pendente: dict[str, object] | None = None
        self._fila_preview: queue.Queue[tuple[dict[str, object], object, Exception | None]] = queue.Queue()
        self._preparacao_cache: PreparacaoMorfismo | None = None
        self._preparacao_assinatura: tuple[object, ...] | None = None
        self._arrastando_tempo = False
        self._animacao_em_execucao = False
        self._animacao_after_id: str | None = None
        self._animacao_conclusao_pendente = False
        self._animacao_mudancas_total = 0
        self._animacao_etapas_com_mudanca = 0
        self._animacao_ultimo_frame = None
        self._exportacao_animacao_em_andamento = False
        self._fila_animacao: queue.Queue[tuple[Path | None, int, tuple[int, int] | None, Exception | None]] = queue.Queue()
        self._montar_interface()
        self.bind_all("<MouseWheel>", self._ao_rolar_mouse, add="+")
        self.bind_all("<Button-4>", self._ao_rolar_mouse_linux, add="+")
        self.bind_all("<Button-5>", self._ao_rolar_mouse_linux, add="+")
        self.after_idle(self._carregar_exemplo_automatico)

    def _montar_interface(self) -> None:
        self.canvas_scroll = tk.Canvas(self, bg=tema.COR_FUNDO, highlightthickness=0)
        self.canvas_scroll.pack(side="left", fill="both", expand=True)

        self.barra_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas_scroll.yview)
        self.barra_scroll.pack(side="right", fill="y")
        self.canvas_scroll.configure(yscrollcommand=self.barra_scroll.set)

        self.conteudo = ttk.Frame(self.canvas_scroll, padding=12, style="Root.TFrame")
        self._janela_scroll = self.canvas_scroll.create_window((0, 0), window=self.conteudo, anchor="nw")
        self.conteudo.bind("<Configure>", self._ao_configurar_conteudo)
        self.canvas_scroll.bind("<Configure>", self._ao_configurar_canvas_scroll)

        barra = ttk.Frame(self.conteudo, style="Root.TFrame")
        barra.pack(fill="x", pady=(0, 12))

        ttk.Button(barra, text="Carregar caso teste de morfismo", command=self.carregar_exemplo_luiz).pack(side="left")
        ttk.Button(barra, text="Carregar imagem inicial", command=lambda: self._carregar("inicial")).pack(side="left", padx=(8, 0))
        ttk.Button(barra, text="Carregar imagem final", command=lambda: self._carregar("final")).pack(side="left", padx=(8, 12))
        ttk.Button(barra, text="Limpar", command=self.limpar_tudo).pack(side="left", padx=(0, 8))
        criar_seletor_janela(barra).pack(side="left", padx=(0, 8))
        ttk.Button(barra, text="Limpar pontos", command=self.limpar_pontos).pack(side="left")
        ttk.Button(barra, text="Remover ultimo par", command=self.remover_ultimo_par).pack(side="left", padx=(8, 12))
        ttk.Button(barra, text="Gerar frame", command=self.gerar_frame).pack(side="left")
        ttk.Button(barra, text="Salvar frame", command=self.salvar_frame).pack(side="left", padx=(8, 0))
        ttk.Button(barra, textvariable=self.rotulo_salvar_animacao, command=self.salvar_animacao).pack(side="left", padx=(8, 0))
        ttk.Button(barra, text="Salvar sequencia", command=self.salvar_sequencia).pack(side="left", padx=(8, 0))

        controles_tempo = ttk.Frame(self.conteudo, style="Root.TFrame")
        controles_tempo.pack(fill="x", pady=(0, 12))
        ttk.Label(controles_tempo, text="Tempo do morfismo:", style="Texto.TLabel").pack(side="left")
        self.escala_tempo = ttk.Scale(
            controles_tempo,
            from_=0.0,
            to=1.0,
            variable=self.tempo,
            command=self._ao_mudar_tempo,
        )
        self.escala_tempo.pack(side="left", fill="x", expand=True, padx=12)
        self.escala_tempo.bind("<ButtonPress-1>", self._ao_iniciar_arraste_tempo)
        self.escala_tempo.bind("<ButtonRelease-1>", self._ao_soltar_tempo)
        ttk.Label(controles_tempo, textvariable=self.rotulo_tempo, style="Texto.TLabel").pack(side="left")
        ttk.Button(controles_tempo, textvariable=self.rotulo_animacao, command=self.alternar_animacao).pack(side="left", padx=(12, 0))
        ttk.Label(controles_tempo, text="Quadros:", style="Texto.TLabel").pack(side="left", padx=(18, 6))
        ttk.Entry(controles_tempo, textvariable=self.total_quadros_animacao, width=5).pack(side="left")
        ttk.Label(controles_tempo, text="Atraso (ms):", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        ttk.Entry(controles_tempo, textvariable=self.atraso_animacao_ms, width=6).pack(side="left")

        ttk.Label(
            self.conteudo,
            text="Marque os pontos na mesma ordem nas duas imagens. A barra de tempo atualiza a previa automaticamente. Quadros define quantas imagens intermediarias a animacao vai ter, e atraso (ms) define o tempo entre um quadro e outro.",
            style="Texto.TLabel",
            wraplength=900,
        ).pack(fill="x", pady=(0, 8))
        ttk.Label(self.conteudo, textvariable=self.contagem_pontos, style="Texto.TLabel").pack(fill="x", pady=(0, 8))

        area = ttk.Frame(self.conteudo, style="Root.TFrame")
        area.pack(fill="both", expand=True)
        area.columnconfigure(0, weight=1)
        area.columnconfigure(1, weight=1)
        area.columnconfigure(2, weight=1)

        quadro_inicial = ttk.LabelFrame(area, text="Imagem inicial", padding=8, style="Card.TLabelframe")
        quadro_inicial.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        corpo_inicial = tk.Frame(quadro_inicial, bg=tema.COR_PAINEL)
        corpo_inicial.pack(fill="both", expand=True)
        moldura_inicial = tk.Frame(corpo_inicial, bg=tema.COR_FUNDO, width=self.TAMANHO_CANVAS, height=self.TAMANHO_CANVAS)
        moldura_inicial.pack(padx=8, pady=8)
        moldura_inicial.pack_propagate(False)
        self.canvas_inicial = tk.Canvas(
            moldura_inicial,
            width=self.TAMANHO_CANVAS,
            height=self.TAMANHO_CANVAS,
            bg=tema.COR_FUNDO,
            highlightbackground=tema.COR_BORDA,
            highlightthickness=1,
        )
        self.canvas_inicial.pack(fill="both", expand=True)
        self.canvas_inicial.bind("<Button-1>", lambda evento: self._registrar_ponto("inicial", evento))

        quadro_final = ttk.LabelFrame(area, text="Imagem final", padding=8, style="Card.TLabelframe")
        quadro_final.grid(row=0, column=1, padx=8, sticky="nsew")
        corpo_final = tk.Frame(quadro_final, bg=tema.COR_PAINEL)
        corpo_final.pack(fill="both", expand=True)
        moldura_final = tk.Frame(corpo_final, bg=tema.COR_FUNDO, width=self.TAMANHO_CANVAS, height=self.TAMANHO_CANVAS)
        moldura_final.pack(padx=8, pady=8)
        moldura_final.pack_propagate(False)
        self.canvas_final = tk.Canvas(
            moldura_final,
            width=self.TAMANHO_CANVAS,
            height=self.TAMANHO_CANVAS,
            bg=tema.COR_FUNDO,
            highlightbackground=tema.COR_BORDA,
            highlightthickness=1,
        )
        self.canvas_final.pack(fill="both", expand=True)
        self.canvas_final.bind("<Button-1>", lambda evento: self._registrar_ponto("final", evento))

        self.painel_resultado = PainelImagem(
            area,
            "Frame morfado",
            largura_max=self.TAMANHO_CANVAS,
            altura_max=self.TAMANHO_CANVAS,
            inspector_posicao="bottom",
        )
        self.painel_resultado.grid(row=0, column=2, padx=(8, 0), sticky="nsew")

        criar_barra_status(self.conteudo, self.status).pack(fill="x", pady=(10, 0))

        self._desenhar_canvas("inicial")
        self._desenhar_canvas("final")

    def _atualizar_scrollregion(self) -> None:
        self.update_idletasks()
        bbox = self.canvas_scroll.bbox("all")
        if bbox:
            x1, y1, x2, y2 = bbox
            canvas_height = self.canvas_scroll.winfo_height()
            if y2 - y1 < canvas_height:
                y2 = y1 + canvas_height
            canvas_width = self.canvas_scroll.winfo_width()
            if x2 - x1 < canvas_width:
                x2 = x1 + canvas_width
            self.canvas_scroll.configure(scrollregion=(x1, y1, x2, y2))

    def _ao_configurar_conteudo(self, _evento) -> None:
        self._atualizar_scrollregion()

    def _ao_configurar_canvas_scroll(self, evento) -> None:
        self.canvas_scroll.itemconfigure(self._janela_scroll, width=evento.width)
        self._atualizar_scrollregion()

    def _widget_pertence_a_aba(self, widget) -> bool:
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
        if not self.winfo_ismapped() or not self._widget_pertence_a_aba(widget):
            return
        if evento.delta == 0:
            return
        direcao = -1 if evento.delta > 0 else 1
        passos = max(1, abs(int(evento.delta)) // 120)
        self.canvas_scroll.yview_scroll(direcao * passos, "units")

    def _ao_rolar_mouse_linux(self, evento) -> None:
        widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        if not self.winfo_ismapped() or not self._widget_pertence_a_aba(widget):
            return
        direcao = -1 if evento.num == 4 else 1
        self.canvas_scroll.yview_scroll(direcao, "units")

    def _otimizar_imagem_para_morfismo(self, imagem: ImagemNetpbm) -> ImagemNetpbm:
        matriz_otimizada = redimensionar_para_limite(imagem.matriz, self.LIMITE_DIMENSAO_TRABALHO)
        if matriz_otimizada.shape == imagem.matriz.shape:
            return imagem
        return criar_imagem(
            matriz_otimizada,
            nome=imagem.nome,
            caminho_origem=imagem.caminho_origem,
        )

    def _carregar_exemplo_automatico(self) -> None:
        if not exemplo_luiz_disponivel():
            return
        if self.imagem_inicial is not None or self.imagem_final is not None:
            return
        self.carregar_exemplo_luiz(automatico=True)

    def carregar_exemplo_luiz(self, *, automatico: bool = False) -> None:
        try:
            exemplo = carregar_exemplo_luiz_padrao(limite_dimensao=self.LIMITE_DIMENSAO_TRABALHO)
        except Exception as erro:
            if not automatico:
                self.status.set(f"Não foi possível carregar a amostra demonstrativa: {erro}")
            return

        self.imagem_inicial = exemplo.imagem_inicial
        self.imagem_final = exemplo.imagem_final
        self.pontos_iniciais = list(exemplo.pontos_iniciais)
        self.pontos_finais = list(exemplo.pontos_finais)
        self.total_quadros_animacao.set(str(exemplo.total_quadros_gif))
        self.atraso_animacao_ms.set(str(exemplo.atraso_gif_ms))
        self._invalidar_preview_em_cache()
        self._desenhar_canvas("inicial")
        self._desenhar_canvas("final")
        self._atualizar_contagem()
        self.painel_resultado.limpar("Gerando prévia do morfismo.")
        self.status.set(
            "Amostra demonstrativa de morfismo carregada com pontos correspondentes prontos para execução."
        )
        self._agendar_preview_morfismo(atualizar_status=False, imediato=True)

    def _assinatura_preparacao_morfismo(self) -> tuple[object, ...] | None:
        if not self._estado_morfismo_valido():
            return None
        assert self.imagem_inicial is not None and self.imagem_final is not None
        return (
            id(self.imagem_inicial.matriz),
            self.imagem_inicial.matriz.shape,
            id(self.imagem_final.matriz),
            self.imagem_final.matriz.shape,
            tuple(self.pontos_iniciais),
            tuple(self.pontos_finais),
        )

    def _obter_preparacao_morfismo(self) -> PreparacaoMorfismo:
        assinatura = self._assinatura_preparacao_morfismo()
        if assinatura is None or self.imagem_inicial is None or self.imagem_final is None:
            raise ValueError("As imagens e os pontos correspondentes ainda nao estao prontos para o morfismo.")
        if assinatura == self._preparacao_assinatura and self._preparacao_cache is not None:
            return self._preparacao_cache
        self._preparacao_cache = preparar_morfismo(
            self.imagem_inicial.matriz,
            self.imagem_final.matriz,
            self.pontos_iniciais,
            self.pontos_finais,
        )
        self._preparacao_assinatura = assinatura
        return self._preparacao_cache

    def _ao_mudar_tempo(self, _valor: str) -> None:
        self.rotulo_tempo.set(f"t = {self.tempo.get():.2f}")
        if self._arrastando_tempo or self._animacao_em_execucao:
            return
        if not self._estado_morfismo_valido():
            return
        self._agendar_preview_morfismo(atualizar_status=False, imediato=True)

    def _ao_iniciar_arraste_tempo(self, _evento) -> None:
        self._parar_animacao(atualizar_status=False)
        self._arrastando_tempo = True
        self._cancelar_preview_agendado()
        self._preview_requisicao_atual += 1
        self._preview_pendente = None

    def _ao_soltar_tempo(self, _evento) -> None:
        self._arrastando_tempo = False
        self.rotulo_tempo.set(f"t = {self.tempo.get():.2f}")
        if not self._estado_morfismo_valido():
            return
        self._agendar_preview_morfismo(atualizar_status=False, imediato=True)

    def _carregar(self, lado: str) -> None:
        imagem_original = _abrir_dialogo_imagem()
        if imagem_original is None:
            return
        imagem = self._otimizar_imagem_para_morfismo(imagem_original)
        houve_otimizacao = imagem.matriz.shape != imagem_original.matriz.shape
        if lado == "inicial":
            self.imagem_inicial = imagem
            self.pontos_iniciais.clear()
        else:
            self.imagem_final = imagem
            self.pontos_finais.clear()
        self._invalidar_preview_em_cache()
        self._desenhar_canvas(lado)
        self._atualizar_contagem()
        self.painel_resultado.limpar("Aguardando gerar frame.")
        complemento = " Imagem ajustada automaticamente para acelerar a animacao." if houve_otimizacao else ""
        self.status.set(f"Imagem {lado} carregada: {_descricao_imagem(imagem)}.{complemento}")

    def _registrar_ponto(self, lado: str, evento) -> None:
        imagem = self.imagem_inicial if lado == "inicial" else self.imagem_final
        if imagem is None:
            self.status.set(f"Carregue a imagem {lado} antes de marcar pontos.")
            return

        estado = self.estado_canvases[lado]
        x_relativo = evento.x - estado["offset_x"]
        y_relativo = evento.y - estado["offset_y"]
        if not (0 <= x_relativo <= estado["largura"] and 0 <= y_relativo <= estado["altura"]):
            return

        x_original = x_relativo * imagem.largura / max(estado["largura"], 1)
        y_original = y_relativo * imagem.altura / max(estado["altura"], 1)

        if lado == "inicial":
            self.pontos_iniciais.append((x_original, y_original))
        else:
            self.pontos_finais.append((x_original, y_original))

        self._invalidar_preview_em_cache()
        self._desenhar_canvas(lado)
        self._atualizar_contagem()
        if self._estado_morfismo_valido():
            self.status.set(f"Ponto adicionado na imagem {lado}. Previa do morfismo atualizada automaticamente.")
            self._agendar_preview_morfismo(atualizar_status=False)
        else:
            self.painel_resultado.limpar("Aguardando gerar frame.")
            self.status.set(f"Ponto adicionado na imagem {lado}.")

    def _atualizar_contagem(self) -> None:
        self.contagem_pontos.set(
            f"Pontos: {len(self.pontos_iniciais)} na imagem inicial | {len(self.pontos_finais)} na imagem final"
        )

    def _desenhar_canvas(self, lado: str) -> None:
        canvas = self.canvas_inicial if lado == "inicial" else self.canvas_final
        imagem = self.imagem_inicial if lado == "inicial" else self.imagem_final
        pontos = self.pontos_iniciais if lado == "inicial" else self.pontos_finais
        canvas.delete("all")

        if imagem is None:
            canvas.create_text(
                self.TAMANHO_CANVAS / 2,
                self.TAMANHO_CANVAS / 2,
                text="Nenhuma imagem carregada",
                fill=tema.COR_TEXTO,
            )
            return

        photo = criar_photoimage_ajustada(
            imagem.matriz,
            self.previews[lado],
            largura_max=self.TAMANHO_CANVAS - 20,
            altura_max=self.TAMANHO_CANVAS - 20,
        )
        largura = photo.width()
        altura = photo.height()
        offset_x = (self.TAMANHO_CANVAS - largura) // 2
        offset_y = (self.TAMANHO_CANVAS - altura) // 2

        estado = self.estado_canvases[lado]
        estado["photo"] = photo
        estado["offset_x"] = offset_x
        estado["offset_y"] = offset_y
        estado["largura"] = largura
        estado["altura"] = altura

        canvas.create_image(offset_x, offset_y, anchor="nw", image=photo)

        for indice, ponto in enumerate(pontos, start=1):
            x = offset_x + ponto[0] * largura / max(imagem.largura, 1)
            y = offset_y + ponto[1] * altura / max(imagem.altura, 1)
            canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=tema.COR_DESTAQUE, outline="")
            canvas.create_text(x + 10, y - 8, text=str(indice), fill=tema.COR_TEXTO, font=tema.FONTE_PEQUENA)

    def limpar_pontos(self) -> None:
        self.pontos_iniciais.clear()
        self.pontos_finais.clear()
        self._invalidar_preview_em_cache()
        self._desenhar_canvas("inicial")
        self._desenhar_canvas("final")
        self._atualizar_contagem()
        self.painel_resultado.limpar("Aguardando gerar frame.")
        self.status.set("Todos os pontos correspondentes foram removidos.")

    def limpar_tudo(self) -> None:
        self.imagem_inicial = None
        self.imagem_final = None
        self.imagem_resultado = None
        self.pontos_iniciais.clear()
        self.pontos_finais.clear()
        self._invalidar_preview_em_cache()
        self._desenhar_canvas("inicial")
        self._desenhar_canvas("final")
        self._atualizar_contagem()
        self.painel_resultado.limpar("Aguardando gerar frame.")
        self.status.set("Imagens e pontos removidos. Carregue novamente as imagens para gerar o morfismo.")

    def remover_ultimo_par(self) -> None:
        if len(self.pontos_iniciais) > len(self.pontos_finais) and self.pontos_iniciais:
            self.pontos_iniciais.pop()
        elif len(self.pontos_finais) > len(self.pontos_iniciais) and self.pontos_finais:
            self.pontos_finais.pop()
        elif self.pontos_iniciais and self.pontos_finais:
            self.pontos_iniciais.pop()
            self.pontos_finais.pop()
        else:
            self.status.set("Nao ha pontos para remover.")
            return

        self._invalidar_preview_em_cache()
        self._desenhar_canvas("inicial")
        self._desenhar_canvas("final")
        self._atualizar_contagem()
        self.painel_resultado.limpar("Aguardando gerar frame.")
        self.status.set("Ultimo ponto ou ultimo par removido.")

    def _estado_morfismo_valido(self) -> bool:
        if self.imagem_inicial is None or self.imagem_final is None:
            return False
        if len(self.pontos_iniciais) != len(self.pontos_finais):
            return False
        return True

    def _reiniciar_metricas_animacao(self) -> None:
        self._animacao_conclusao_pendente = False
        self._animacao_mudancas_total = 0
        self._animacao_etapas_com_mudanca = 0
        self._animacao_ultimo_frame = None

    def _registrar_mudancas_animacao(self, frame) -> None:
        if self._animacao_ultimo_frame is None:
            self._animacao_ultimo_frame = frame.copy()
            return

        mudancas = contar_mudancas_entre_imagens(self._animacao_ultimo_frame, frame)
        if mudancas > 0:
            self._animacao_mudancas_total += mudancas
            self._animacao_etapas_com_mudanca += 1
        self._animacao_ultimo_frame = frame.copy()

    def _resumo_animacao(self) -> str:
        total_mudancas = self._animacao_mudancas_total
        total_etapas = self._animacao_etapas_com_mudanca
        palavra_mudanca = "mudanca" if total_mudancas == 1 else "mudancas"
        palavra_etapa = "etapa" if total_etapas == 1 else "etapas"
        return (
            f"Foram observadas {total_mudancas} {palavra_mudanca} de pixel "
            f"em {total_etapas} {palavra_etapa} da transicao."
        )

    def _invalidar_preview_em_cache(self) -> None:
        self.imagem_resultado = None
        self._parar_animacao(atualizar_status=False)
        self._reiniciar_metricas_animacao()
        self._preview_requisicao_atual += 1
        self._preview_pendente = None
        self._preparacao_cache = None
        self._preparacao_assinatura = None
        self._cancelar_preview_agendado()

    def alternar_animacao(self) -> None:
        # animacao: percorre o valor de t aos poucos para mostrar a transicao completa
        if self._animacao_em_execucao:
            self._parar_animacao(atualizar_status=True)
            return
        if not self._estado_morfismo_valido():
            self.status.set("Carregue as duas imagens e marque a mesma quantidade de pontos antes de animar o morfismo.")
            return
        self._reiniciar_metricas_animacao()
        self._animacao_em_execucao = True
        self.rotulo_animacao.set("Parar animacao")
        self.tempo.set(0.0)
        self.rotulo_tempo.set("t = 0.00")
        self.status.set("Animacao do morfismo em andamento.")
        self._agendar_preview_morfismo(atualizar_status=False, imediato=True, origem_animacao=True)
        self._animacao_after_id = self.after(self.INTERVALO_ANIMACAO_MS, self._avancar_animacao)

    def _parar_animacao(self, *, atualizar_status: bool, concluida: bool = False) -> None:
        if self._animacao_after_id is not None:
            self.after_cancel(self._animacao_after_id)
            self._animacao_after_id = None
        estava_animando = self._animacao_em_execucao
        self._animacao_em_execucao = False
        self._animacao_conclusao_pendente = False
        self.rotulo_animacao.set("Animar")
        if not atualizar_status or not estava_animando:
            return
        if concluida:
            self.status.set(f"Animacao do morfismo concluida. {self._resumo_animacao()}")
        else:
            self.status.set("Animacao do morfismo interrompida.")

    def _avancar_animacao(self) -> None:
        if not self._animacao_em_execucao:
            return
        proximo_tempo = min(1.0, float(self.tempo.get()) + self.PASSO_ANIMACAO)
        self.tempo.set(proximo_tempo)
        self.rotulo_tempo.set(f"t = {proximo_tempo:.2f}")
        self._agendar_preview_morfismo(atualizar_status=False, origem_animacao=True)
        if proximo_tempo >= 1.0:
            self._animacao_conclusao_pendente = True
            self._animacao_after_id = None
            return
        self._animacao_after_id = self.after(self.INTERVALO_ANIMACAO_MS, self._avancar_animacao)

    def _cancelar_preview_agendado(self) -> None:
        if self._preview_after_id is not None:
            self.after_cancel(self._preview_after_id)
            self._preview_after_id = None

    def _agendar_preview_morfismo(
        self,
        atualizar_status: bool,
        *,
        imediato: bool = False,
        origem_animacao: bool = False,
    ) -> None:
        if not self._estado_morfismo_valido():
            return

        try:
            preparacao = self._obter_preparacao_morfismo()
        except Exception as erro:
            if atualizar_status:
                self.status.set(f"Nao foi possivel preparar o morfismo: {erro}")
            return

        self._preview_requisicao_atual += 1
        self._preview_pendente = {
            "token": self._preview_requisicao_atual,
            "tempo": float(self.tempo.get()),
            "preparacao": preparacao,
            "atualizar_status": atualizar_status,
            "origem_animacao": origem_animacao,
        }

        self._cancelar_preview_agendado()
        if imediato:
            if not self._preview_em_andamento:
                self._iniciar_preview_pendente()
            return
        self._preview_after_id = self.after(self.ATRASO_PREVIEW_MS, self._iniciar_preview_pendente)

    def _iniciar_preview_pendente(self) -> None:
        self._preview_after_id = None
        if self._preview_em_andamento or self._preview_pendente is None:
            return

        requisicao = self._preview_pendente
        self._preview_pendente = None
        self._preview_em_andamento = True

        worker = threading.Thread(
            target=self._executar_preview_morfismo,
            args=(requisicao,),
            daemon=True,
        )
        worker.start()
        self.after(15, self._processar_resultados_preview)

    def _executar_preview_morfismo(self, requisicao: dict[str, object]) -> None:
        erro: Exception | None = None
        frame = None
        try:
            resultado = gerar_frame_preparado(requisicao["preparacao"], requisicao["tempo"])
            frame = resultado.frame
        except Exception as exc:  # pragma: no cover - defesa para ambiente do usuario
            erro = exc

        self._fila_preview.put((requisicao, frame, erro))

    def _processar_resultados_preview(self) -> None:
        try:
            requisicao, frame, erro = self._fila_preview.get_nowait()
        except queue.Empty:
            if self._preview_em_andamento:
                self.after(15, self._processar_resultados_preview)
            return

        self._finalizar_preview_morfismo(requisicao, frame, erro)

    def _finalizar_preview_morfismo(
        self,
        requisicao: dict[str, object],
        frame,
        erro: Exception | None,
    ) -> None:
        self._preview_em_andamento = False

        token = int(requisicao["token"])
        atualizar_status = bool(requisicao["atualizar_status"])
        origem_animacao = bool(requisicao.get("origem_animacao", False))
        requisicao_ainda_atual = token == self._preview_requisicao_atual and self._preview_pendente is None

        if erro is not None:
            if origem_animacao and requisicao_ainda_atual:
                self._parar_animacao(atualizar_status=False)
                self.status.set(f"Nao foi possivel gerar o morfismo durante a animacao: {erro}")
            elif atualizar_status and requisicao_ainda_atual:
                self.status.set(f"Nao foi possivel gerar o morfismo: {erro}")
        elif requisicao_ainda_atual and frame is not None:
            tempo = float(requisicao["tempo"])
            if origem_animacao:
                self._registrar_mudancas_animacao(frame)
            self.imagem_resultado = criar_imagem(frame, nome=f"morfismo_t_{tempo:.2f}")
            self.painel_resultado.mostrar_imagem(self.imagem_resultado, texto_info=_descricao_imagem(self.imagem_resultado))
            if origem_animacao and tempo >= 1.0 and self._animacao_conclusao_pendente:
                self._parar_animacao(atualizar_status=True, concluida=True)
            elif atualizar_status:
                self.status.set(
                    f"Frame gerado em t = {tempo:.2f}. "
                    "Se nao houver pontos extras alem do contorno, o efeito sera uma dissolucao simples."
                )

        if self._preview_pendente is not None:
            self._iniciar_preview_pendente()

    def gerar_frame(self) -> None:
        if self.imagem_inicial is None or self.imagem_final is None:
            self.status.set("Carregue a imagem inicial e a final antes de gerar o morfismo.")
            return
        if len(self.pontos_iniciais) != len(self.pontos_finais):
            self.status.set("A quantidade de pontos nas duas imagens precisa ser igual.")
            return
        self.status.set(f"Gerando frame para t = {self.tempo.get():.2f}...")
        self._agendar_preview_morfismo(atualizar_status=True)
        self._iniciar_preview_pendente()

    def salvar_frame(self) -> None:
        if self.imagem_resultado is None:
            self.status.set("Gere um frame antes de salvar.")
            return
        caminho = _salvar_dialogo_resultado(self.imagem_resultado)
        if caminho is not None:
            self.status.set(f"Frame salvo em: {caminho}")

    def salvar_animacao(self) -> None:
        if self._exportacao_animacao_em_andamento:
            self.status.set("A exportacao da animacao ja esta em andamento.")
            return
        if not self._estado_morfismo_valido():
            self.status.set("Carregue as duas imagens e ajuste os pontos antes de salvar a animacao.")
            return

        try:
            total_quadros = max(2, int(self.total_quadros_animacao.get()))
            atraso_ms = max(20, int(self.atraso_animacao_ms.get()))
            preparacao = self._obter_preparacao_morfismo()
        except ValueError as erro:
            self.status.set(f"Parametros da animacao invalidos: {erro}")
            return
        except Exception as erro:
            self.status.set(f"Nao foi possivel preparar a animacao: {erro}")
            return

        nome_base = "animacao_morfismo"
        if self.imagem_inicial is not None and self.imagem_final is not None:
            nome_base = f"animacao_{self.imagem_inicial.nome}_{self.imagem_final.nome}".replace(" ", "_")

        caminho = filedialog.asksaveasfilename(
            title="Salvar animacao do morfismo",
            defaultextension=".gif",
            initialfile=nome_base,
            filetypes=[("Animacao", "*.gif")],
        )
        if not caminho:
            return

        self._parar_animacao(atualizar_status=False)
        self._exportacao_animacao_em_andamento = True
        self.rotulo_salvar_animacao.set("Gerando animacao...")
        self.status.set(
            f"Gerando animacao com {total_quadros} quadros e atraso de {atraso_ms} ms entre quadros."
        )

        requisicao = {
            "caminho": Path(caminho),
            "tempos": gerar_tempos_uniformes(total_quadros),
            "duracao_ms": atraso_ms,
            "preparacao": preparacao,
        }
        worker = threading.Thread(
            target=self._executar_exportacao_animacao,
            args=(requisicao,),
            daemon=True,
        )
        worker.start()
        self.after(30, self._processar_exportacao_animacao)

    def _executar_exportacao_animacao(self, requisicao: dict[str, object]) -> None:
        erro: Exception | None = None
        dimensao = None
        total_quadros = 0
        caminho_saida = None

        try:
            sequencia = gerar_sequencia_preparada(requisicao["preparacao"], requisicao["tempos"])
            caminho_saida = salvar_gif_animado(
                sequencia,
                requisicao["caminho"],
                duracao_ms=int(requisicao["duracao_ms"]),
            )
            total_quadros = len(sequencia)
            if sequencia:
                dimensao = (int(sequencia[0].shape[1]), int(sequencia[0].shape[0]))
        except Exception as exc:  # pragma: no cover - defesa para ambiente do usuario
            erro = exc

        self._fila_animacao.put((caminho_saida, total_quadros, dimensao, erro))

    def _processar_exportacao_animacao(self) -> None:
        try:
            caminho_saida, total_quadros, dimensao, erro = self._fila_animacao.get_nowait()
        except queue.Empty:
            if self._exportacao_animacao_em_andamento:
                self.after(30, self._processar_exportacao_animacao)
            return

        self._exportacao_animacao_em_andamento = False
        self.rotulo_salvar_animacao.set("Salvar animacao")

        if erro is not None:
            self.status.set(f"Nao foi possivel exportar a animacao: {erro}")
            return

        if caminho_saida is None:
            self.status.set("A exportacao terminou sem gerar um arquivo de animacao.")
            return

        detalhe_dimensao = ""
        if dimensao is not None:
            detalhe_dimensao = f" em {dimensao[0]}x{dimensao[1]}"
        self.status.set(
            f"Animacao salva em: {caminho_saida} | {total_quadros} quadros{detalhe_dimensao}."
        )

    def salvar_sequencia(self) -> None:
        if self.imagem_inicial is None or self.imagem_final is None:
            self.status.set("Carregue as duas imagens antes de salvar uma sequencia.")
            return
        if len(self.pontos_iniciais) != len(self.pontos_finais):
            self.status.set("A quantidade de pontos nas duas imagens precisa ser igual.")
            return

        pasta = filedialog.askdirectory(title="Selecione a pasta para salvar a sequencia")
        if not pasta:
            return

        tempos = gerar_tempos_uniformes(11)
        try:
            sequencia = gerar_sequencia_preparada(self._obter_preparacao_morfismo(), tempos)
        except Exception as erro:  # pragma: no cover - defesa para ambiente do usuario
            self.status.set(f"Nao foi possivel gerar a sequencia: {erro}")
            return

        pasta_saida = Path(pasta)
        for tempo, frame in zip(tempos, sequencia, strict=True):
            imagem = criar_imagem(frame, nome=f"morfismo_{tempo:.2f}")
            salvar_imagem(imagem, pasta_saida / f"morfismo_{tempo:.2f}.pgm", formato="P5")
        self.status.set(f"Sequencia de morfismo salva em: {pasta_saida}")
