from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk

import numpy as np

from laboratorio_imagens import tema
from laboratorio_imagens.core import filtros_espaciais
from laboratorio_imagens.core.histograma import calcular_histograma, equalizar_histograma
from laboratorio_imagens.core.io_netpbm import ImagemNetpbm, carregar_imagem, criar_imagem, salvar_imagem
from laboratorio_imagens.core.operacoes_pixel import POS_PROCESSAMENTOS, aplicar_operacao_por_nome
from laboratorio_imagens.core.transformacoes_intensidade import (
    faixa_dinamica,
    funcao_sigmoide,
    negativo,
    transformacao_gamma,
    transformacao_linear,
    transformacao_logaritmica,
)
from laboratorio_imagens.ui.widgets import GraficoHistograma, PainelImagem, SincronizadorPaineisImagem, criar_barra_status, criar_seletor_janela


TIPOS_IMAGEM = [
    ("Todas as Imagens Suportadas", "*.pgm *.pbm *.png *.jpg *.jpeg *.bmp *.webp"),
    ("Imagens Comuns (PNG, JPG)", "*.png *.jpg *.jpeg *.bmp *.webp"),
    ("Imagens NetPBM (PGM, PBM)", "*.pgm *.pbm"),
    ("Todos os Arquivos", "*.*"),
]
NOME_NEGATIVO_IMAGEM = "Negativo de uma imagem"
NOME_TRANSFORMACAO_GAMMA = "Transformação Gamma"
NOME_TRANSFORMACAO_LOGARITMO = "Transformação logaritmo"
NOME_FUNCAO_TRANSFERENCIA_GERAL = "Função de transferência de intensidade geral"
NOME_FUNCAO_TRANSFERENCIA_FAIXA_DINAMICA = "Função de transferência faixa dinâmica"
NOME_FUNCAO_TRANSFERENCIA_LINEAR = "Função de transferência linear"
NOME_EQUALIZE_HISTOGRAMA = "Equalize o histograma"


def _abrir_dialogo_imagem() -> ImagemNetpbm | None:
    caminho = filedialog.askopenfilename(title="Selecione uma imagem", filetypes=TIPOS_IMAGEM)
    if not caminho:
        return None
    return carregar_imagem(caminho)


def _salvar_dialogo_resultado(imagem: ImagemNetpbm) -> Path | None:
    extensao_padrao = ".pbm" if imagem.binaria else ".pgm"
    caminho = filedialog.asksaveasfilename(
        title="Salvar resultado",
        defaultextension=extensao_padrao,
        filetypes=[
            ("PGM (*.pgm)", "*.pgm"),
            ("PBM (*.pbm)", "*.pbm"),
            ("PNG (*.png)", "*.png"),
            ("JPG (*.jpg)", "*.jpg"),
            ("Todos os Arquivos", "*.*"),
        ],
    )
    if not caminho:
        return None
    return salvar_imagem(imagem, caminho)


def _descricao_imagem(imagem: ImagemNetpbm) -> str:
    origem = imagem.caminho_origem.name if imagem.caminho_origem else imagem.nome
    tipo = "PBM (Binária)" if imagem.binaria else f"Tons de cinza ({imagem.formato_origem})"
    return f"{origem} | {imagem.largura} x {imagem.altura} | {tipo}"


def _preencher_grade_mascara(campos: list[list[tk.Entry]], valores: list[list[float]]) -> None:
    for linha in range(3):
        for coluna in range(3):
            campos[linha][coluna].configure(state="normal")
            campos[linha][coluna].delete(0, tk.END)
            valor = valores[linha][coluna]
            texto = str(int(valor)) if float(valor).is_integer() else f"{valor:.4f}".rstrip("0").rstrip(".")
            campos[linha][coluna].insert(0, texto)


def _definir_estado_grade(campos: list[list[tk.Entry]], *, editavel: bool) -> None:
    estado = "normal" if editavel else "disabled"
    fundo = tema.COR_PAINEL_ALT if editavel else tema.COR_PAINEL
    for linha in campos:
        for campo in linha:
            campo.configure(
                state=estado,
                disabledforeground=tema.COR_TEXTO_MUTED,
                disabledbackground=fundo,
                bg=fundo,
                fg=tema.COR_TEXTO,
                insertbackground=tema.COR_TEXTO,
            )


class AbaFiltros(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12, style="Root.TFrame")
        self.imagem_origem: ImagemNetpbm | None = None
        self.imagem_resultado: ImagemNetpbm | None = None
        self.sincronizar_tabelas = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Carregue uma imagem para aplicar os filtros da aula 9.")
        self.filtro_atual = tk.StringVar(value="Filtro da media")
        self.fator_realce = tk.StringVar(value="1.2")
        self.campos_mascara: list[list[tk.Entry]] = []
        self._sincronizador_pixels: SincronizadorPaineisImagem | None = None
        self.fator_realce.trace_add("write", self._ao_alterar_fator_realce)
        self._montar_interface()
        self._ao_mudar_filtro()

    def _montar_interface(self) -> None:
        linha_controles = ttk.Frame(self, style="Root.TFrame")
        linha_controles.pack(fill="x", pady=(0, 12))

        ttk.Button(linha_controles, text="Carregar imagem", command=self.carregar_imagem).pack(side="left")
        ttk.Button(linha_controles, text="Limpar", command=self.limpar_imagens).pack(side="left", padx=(8, 0))
        criar_seletor_janela(linha_controles).pack(side="left", padx=(12, 0))
        ttk.Label(linha_controles, text="Filtro:", style="Texto.TLabel").pack(side="left", padx=(12, 6))

        seletor = ttk.Combobox(
            linha_controles,
            textvariable=self.filtro_atual,
            values=[item.nome for item in filtros_espaciais.FILTROS_DISPONIVEIS],
            state="readonly",
            width=22,
        )
        seletor.pack(side="left")
        seletor.bind("<<ComboboxSelected>>", lambda _evento: self._ao_mudar_filtro())

        self.bloco_parametros_dinamicos = ttk.Frame(linha_controles, style="Root.TFrame")
        self.bloco_parametros_dinamicos.pack(side="left", padx=(12, 0))

        self.bloco_fator_a = ttk.Frame(self.bloco_parametros_dinamicos, style="Root.TFrame")
        self.rotulo_fator_a = ttk.Label(self.bloco_fator_a, text="Fator A:", style="Texto.TLabel")
        self.rotulo_fator_a.pack(side="left", padx=(0, 6))
        self.entrada_fator_a = ttk.Entry(self.bloco_fator_a, textvariable=self.fator_realce, width=8)
        self.entrada_fator_a.pack(side="left")

        ttk.Button(linha_controles, text="Aplicar", command=self.aplicar_filtro).pack(side="left", padx=(12, 0))
        ttk.Button(linha_controles, text="Salvar resultado", command=self.salvar_resultado).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(
            linha_controles,
            text="Sincronizar tabelas",
            variable=self.sincronizar_tabelas,
            command=lambda: self._sincronizador_pixels.definir_habilitado(self.sincronizar_tabelas.get()),
        ).pack(side="left", padx=(10, 0))

        self.painel_auxiliar = ttk.LabelFrame(self, text="Mascara 3x3", padding=10, style="Card.TLabelframe")
        self.painel_auxiliar.pack(fill="x", pady=(0, 12))

        grade = ttk.Frame(self.painel_auxiliar, style="Root.TFrame")
        grade.pack(anchor="w")
        for linha in range(3):
            linha_campos = []
            for coluna in range(3):
                campo = tk.Entry(
                    grade,
                    width=7,
                    justify="center",
                    relief="solid",
                    bd=1,
                    highlightthickness=0,
                    bg=tema.COR_PAINEL,
                    fg=tema.COR_TEXTO,
                )
                campo.grid(row=linha, column=coluna, padx=3, pady=3)
                linha_campos.append(campo)
            self.campos_mascara.append(linha_campos)

        self.rotulo_auxiliar = ttk.Label(
            self.painel_auxiliar,
            text="A matriz vem preenchida com o valor sugerido. Ajuste apenas se quiser testar outra mascara.",
            style="Texto.TLabel",
        )
        self.rotulo_auxiliar.pack(anchor="w", pady=(8, 0))

        paineis = ttk.Frame(self, style="Root.TFrame")
        paineis.pack(fill="both", expand=True)
        paineis.columnconfigure(0, weight=1)
        paineis.columnconfigure(1, weight=1)

        self.painel_original = PainelImagem(paineis, "Imagem original")
        self.painel_original.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self.painel_resultado = PainelImagem(paineis, "Resultado do filtro")
        self.painel_resultado.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self._sincronizador_pixels = SincronizadorPaineisImagem([self.painel_original, self.painel_resultado])

        criar_barra_status(self, self.status).pack(fill="x", pady=(10, 0))

    def _obter_fator_realce_atual(self) -> float:
        try:
            return float(self.fator_realce.get() or "1.2")
        except ValueError:
            return 1.2

    def _obter_mascara_visual(self, filtro: str) -> list[list[float]]:
        # referencia unica: usa exatamente as mascaras definidas no modulo core
        return filtros_espaciais.obter_mascara_visual_filtro(filtro, self._obter_fator_realce_atual()).tolist()

    def _ao_alterar_fator_realce(self, *_args) -> None:
        if self.filtro_atual.get() != "High-boost":
            return
        _preencher_grade_mascara(self.campos_mascara, self._obter_mascara_visual("High-boost"))
        _definir_estado_grade(self.campos_mascara, editavel=False)

    def _ao_mudar_filtro(self) -> None:
        filtro = self.filtro_atual.get()
        _preencher_grade_mascara(self.campos_mascara, self._obter_mascara_visual(filtro))

        if filtro == "High-boost":
            self.fator_realce.set("1.2")
            if not self.bloco_fator_a.winfo_manager():
                self.bloco_fator_a.pack(side="left")
            _definir_estado_grade(self.campos_mascara, editavel=False)
            self.rotulo_auxiliar.configure(
                text="A matriz abaixo mostra a mascara calculada com o fator A atual. Ajuste A se quiser variar o reforco."
            )
            self.status.set("Ajuste o fator A apenas se quiser variar o reforco do high-boost.")
            return

        if self.bloco_fator_a.winfo_manager():
            self.bloco_fator_a.pack_forget()

        if filtro == "Filtro livre":
            self.rotulo_auxiliar.configure(
                text="A matriz abaixo ja vem com um valor inicial. Edite somente se quiser testar outra mascara 3x3."
            )
            _definir_estado_grade(self.campos_mascara, editavel=True)
            self.status.set("Filtro livre selecionado. A mascara 3x3 pode ser ajustada manualmente.")
            return

        _definir_estado_grade(self.campos_mascara, editavel=False)
        if filtro in {"Roberts", "Roberts cruzado", "Prewitt", "Sobel"}:
            self.rotulo_auxiliar.configure(
                text="A grade mostra a mascara principal do operador. A mascara complementar e aplicada internamente."
            )
        elif filtro in {
            "Roberts X",
            "Roberts Y",
            "Roberts cruzado X",
            "Roberts cruzado Y",
            "Prewitt X",
            "Prewitt Y",
            "Sobel X",
            "Sobel Y",
        }:
            self.rotulo_auxiliar.configure(
                text="A grade mostra a mascara exata usada no eixo selecionado do operador."
            )
        else:
            self.rotulo_auxiliar.configure(
                text="A matriz abaixo mostra os valores 3x3 usados pelo filtro selecionado."
            )
        self.status.set(f"Filtro '{filtro}' pronto para aplicacao.")

    def carregar_imagem(self) -> None:
        imagem = _abrir_dialogo_imagem()
        if imagem is None:
            return
        self.imagem_origem = imagem
        self.imagem_resultado = None
        self.painel_original.mostrar_imagem(imagem, texto_info=_descricao_imagem(imagem))
        self.painel_resultado.limpar("Aguardando processamento.")
        self.status.set(f"Imagem carregada: {_descricao_imagem(imagem)}")

    def limpar_imagens(self) -> None:
        self.imagem_origem = None
        self.imagem_resultado = None
        self.painel_original.limpar()
        self.painel_resultado.limpar()
        self.status.set("Imagens removidas. Carregue uma imagem para aplicar os filtros da aula 9.")

    def aplicar_filtro(self) -> None:
        if self.imagem_origem is None:
            self.status.set("Carregue uma imagem antes de aplicar um filtro.")
            return

        filtro = self.filtro_atual.get()
        try:
            # leitura de parametros: monta a mascara 3x3 digitada pelo usuario
            mascara = np.array(
                [[float(self.campos_mascara[i][j].get()) for j in range(3)] for i in range(3)],
                dtype=np.float64,
            )
            resultado = filtros_espaciais.aplicar_filtro_por_nome(
                filtro,
                self.imagem_origem.matriz,
                fator_realce=float(self.fator_realce.get() or "1.2"),
                mascara_personalizada=mascara,
            )
        except ValueError as erro:
            self.status.set(f"Erro ao aplicar filtro: {erro}")
            return

        self.imagem_resultado = criar_imagem(resultado, nome=f"resultado_{filtro.lower().replace(' ', '_')}")
        self.painel_resultado.mostrar_imagem(self.imagem_resultado, texto_info=_descricao_imagem(self.imagem_resultado))
        self.status.set(f"Filtro '{filtro}' aplicado com sucesso.")

    def salvar_resultado(self) -> None:
        if self.imagem_resultado is None:
            self.status.set("Nao ha resultado para salvar.")
            return
        caminho = _salvar_dialogo_resultado(self.imagem_resultado)
        if caminho is not None:
            self.status.set(f"Resultado salvo em: {caminho}")


class AbaOperacoes(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12, style="Root.TFrame")
        self.imagem_a: ImagemNetpbm | None = None
        self.imagem_b: ImagemNetpbm | None = None
        self.imagem_resultado: ImagemNetpbm | None = None
        self.sincronizar_tabelas = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Carregue uma ou duas imagens para usar soma, subtracao, multiplicacao, divisao e operadores logicos.")
        self.operacao_atual = tk.StringVar(value="Soma")
        self.pos_processamento = tk.StringVar(value="Truncamento")
        self._sincronizador_pixels: SincronizadorPaineisImagem | None = None
        self._montar_interface()

    def _montar_interface(self) -> None:
        barra = ttk.Frame(self, style="Root.TFrame")
        barra.pack(fill="x", pady=(0, 12))

        ttk.Button(barra, text="Carregar imagem A", command=lambda: self._carregar("A")).pack(side="left")
        ttk.Button(barra, text="Carregar imagem B", command=lambda: self._carregar("B")).pack(side="left", padx=(8, 0))
        ttk.Button(barra, text="Limpar", command=self.limpar_imagens).pack(side="left", padx=(8, 12))
        criar_seletor_janela(barra).pack(side="left", padx=(0, 12))
        ttk.Label(barra, text="Operacao:", style="Texto.TLabel").pack(side="left", padx=(0, 6))
        ttk.Combobox(
            barra,
            textvariable=self.operacao_atual,
            values=["Soma", "Subtracao", "Multiplicacao", "Divisao", "AND", "OR", "XOR", "NOT"],
            state="readonly",
            width=18,
        ).pack(side="left")

        ttk.Label(barra, text="Pos-processamento:", style="Texto.TLabel").pack(side="left", padx=(12, 6))
        ttk.Combobox(
            barra,
            textvariable=self.pos_processamento,
            values=list(POS_PROCESSAMENTOS),
            state="readonly",
            width=16,
        ).pack(side="left")

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
        for coluna in range(3):
            paineis.columnconfigure(coluna, weight=1)

        self.painel_a = PainelImagem(paineis, "Imagem A", largura_max=180, altura_max=180)
        self.painel_a.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self.painel_b = PainelImagem(paineis, "Imagem B", largura_max=180, altura_max=180)
        self.painel_b.grid(row=0, column=1, padx=8, sticky="nsew")

        self.painel_resultado = PainelImagem(paineis, "Resultado", largura_max=180, altura_max=180)
        self.painel_resultado.grid(row=0, column=2, padx=(8, 0), sticky="nsew")
        self._sincronizador_pixels = SincronizadorPaineisImagem([self.painel_a, self.painel_b, self.painel_resultado])

        criar_barra_status(self, self.status).pack(fill="x", pady=(10, 0))

    def _carregar(self, alvo: str) -> None:
        imagem = _abrir_dialogo_imagem()
        if imagem is None:
            return
        if alvo == "A":
            self.imagem_a = imagem
            self.painel_a.mostrar_imagem(imagem, texto_info=_descricao_imagem(imagem))
        else:
            self.imagem_b = imagem
            self.painel_b.mostrar_imagem(imagem, texto_info=_descricao_imagem(imagem))
        self.status.set(f"Imagem {alvo} carregada: {_descricao_imagem(imagem)}")

    def limpar_imagens(self) -> None:
        self.imagem_a = None
        self.imagem_b = None
        self.imagem_resultado = None
        self.painel_a.limpar()
        self.painel_b.limpar()
        self.painel_resultado.limpar()
        self.status.set("Imagens removidas. Carregue uma ou duas imagens para usar as operacoes.")

    def aplicar_operacao(self) -> None:
        if self.imagem_a is None:
            self.status.set("Carregue a imagem A antes de aplicar uma operacao.")
            return

        operacao = self.operacao_atual.get()
        if operacao != "NOT" and self.imagem_b is None:
            self.status.set("Carregue as duas imagens antes de aplicar esta operacao.")
            return

        # processamento: executa a operacao escolhida e cria uma nova imagem de saida
        resultado = aplicar_operacao_por_nome(
            operacao,
            self.imagem_a.matriz,
            self.imagem_b.matriz if self.imagem_b is not None else None,
            pos_processamento=self.pos_processamento.get(),
        )
        self.imagem_resultado = criar_imagem(
            resultado,
            nome=f"resultado_{operacao.lower()}",
        )
        self.painel_resultado.mostrar_imagem(self.imagem_resultado, texto_info=_descricao_imagem(self.imagem_resultado))

        if operacao == "NOT":
            self.status.set("Operacao 'NOT' executada sobre a imagem A.")
            return

        assert self.imagem_b is not None
        tamanhos_iguais = self.imagem_a.matriz.shape == self.imagem_b.matriz.shape
        ajuste = "" if tamanhos_iguais else " As imagens foram ajustadas para o menor tamanho em comum."
        self.status.set(f"Operacao '{operacao}' executada.{ajuste}")

    def salvar_resultado(self) -> None:
        if self.imagem_resultado is None:
            self.status.set("Nao ha resultado para salvar.")
            return
        caminho = _salvar_dialogo_resultado(self.imagem_resultado)
        if caminho is not None:
            self.status.set(f"Resultado salvo em: {caminho}")


class AbaIntensidadeHistograma(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12, style="Root.TFrame")
        self.imagem_origem: ImagemNetpbm | None = None
        self.imagem_resultado: ImagemNetpbm | None = None
        self.sincronizar_tabelas = tk.BooleanVar(value=False)
        self._janela_zoom_histogramas: tk.Toplevel | None = None
        self._hist_zoom_original: GraficoHistograma | None = None
        self._hist_zoom_resultado: GraficoHistograma | None = None
        self.status = tk.StringVar(
            value="Carregue uma imagem para testar as transforma\u00e7\u00f5es de intensidade e a equaliza\u00e7\u00e3o do histograma."
        )
        self.transformacoes_disponiveis = [
            NOME_NEGATIVO_IMAGEM,
            NOME_TRANSFORMACAO_GAMMA,
            NOME_TRANSFORMACAO_LOGARITMO,
            NOME_FUNCAO_TRANSFERENCIA_GERAL,
            NOME_FUNCAO_TRANSFERENCIA_FAIXA_DINAMICA,
            NOME_FUNCAO_TRANSFERENCIA_LINEAR,
            NOME_EQUALIZE_HISTOGRAMA,
        ]
        self.transformacao = tk.StringVar(value=NOME_NEGATIVO_IMAGEM)
        self.parametro_1 = tk.StringVar(value="")
        self.parametro_2 = tk.StringVar(value="")
        self.rotulo_parametro_1 = tk.StringVar(value="Parametro 1")
        self.rotulo_parametro_2 = tk.StringVar(value="Parametro 2")
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
            values=self.transformacoes_disponiveis,
            state="readonly",
            width=44,
        )
        seletor.pack(side="left")
        seletor.bind("<<ComboboxSelected>>", lambda _evento: self._ao_mudar_transformacao())

        ttk.Label(barra, textvariable=self.rotulo_parametro_1, style="Texto.TLabel").pack(side="left", padx=(12, 6))
        self.entrada_1 = ttk.Entry(barra, textvariable=self.parametro_1, width=10)
        self.entrada_1.pack(side="left")

        ttk.Label(barra, textvariable=self.rotulo_parametro_2, style="Texto.TLabel").pack(side="left", padx=(12, 6))
        self.entrada_2 = ttk.Entry(barra, textvariable=self.parametro_2, width=10)
        self.entrada_2.pack(side="left")

        ttk.Button(barra, text="Aplicar", command=self.aplicar_transformacao).pack(side="left", padx=(12, 0))
        ttk.Button(barra, text="Salvar resultado", command=self.salvar_resultado).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(
            barra,
            text="Sincronizar tabelas",
            variable=self.sincronizar_tabelas,
            command=lambda: self._sincronizador_pixels.definir_habilitado(self.sincronizar_tabelas.get()),
        ).pack(side="left", padx=(10, 0))
        ttk.Button(barra, text="Ampliar histogramas", command=self.abrir_zoom_histogramas).pack(side="left", padx=(8, 0))

        topo = ttk.Frame(self, style="Root.TFrame")
        topo.pack(fill="x", pady=(0, 12))
        topo.columnconfigure(0, weight=1)
        topo.columnconfigure(1, weight=1)

        self.painel_original = PainelImagem(topo, "Imagem original")
        self.painel_original.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.painel_resultado = PainelImagem(topo, "Imagem transformada")
        self.painel_resultado.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self._sincronizador_pixels = SincronizadorPaineisImagem([self.painel_original, self.painel_resultado])

        base_hist = ttk.Frame(self, style="Root.TFrame")
        base_hist.pack(fill="x")
        base_hist.columnconfigure(0, weight=1)
        base_hist.columnconfigure(1, weight=1)

        self.hist_original = GraficoHistograma(base_hist, "Histograma original")
        self.hist_original.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        self.hist_resultado = GraficoHistograma(base_hist, "Histograma resultado")
        self.hist_resultado.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        criar_barra_status(self, self.status).pack(fill="x", pady=(10, 0))

    def _atualizar_histogramas(
        self,
        hist_original: np.ndarray,
        *,
        cor_original: str,
        hist_resultado: np.ndarray,
        cor_resultado: str,
    ) -> None:
        # sincronizacao: atualiza tanto os graficos da aba quanto a janela ampliada, se estiver aberta
        self.hist_original.desenhar(hist_original, cor=cor_original)
        self.hist_resultado.desenhar(hist_resultado, cor=cor_resultado)

        if self._janela_zoom_histogramas is None or not self._janela_zoom_histogramas.winfo_exists():
            return

        if self._hist_zoom_original is not None:
            self._hist_zoom_original.desenhar(hist_original, cor=cor_original)
        if self._hist_zoom_resultado is not None:
            self._hist_zoom_resultado.desenhar(hist_resultado, cor=cor_resultado)

    def _atualizar_tamanho_zoom_histogramas(self) -> None:
        if self._janela_zoom_histogramas is None or not self._janela_zoom_histogramas.winfo_exists():
            return
        if self._hist_zoom_original is None or self._hist_zoom_resultado is None:
            return

        largura_janela = max(self._janela_zoom_histogramas.winfo_width(), 980)
        altura_janela = max(self._janela_zoom_histogramas.winfo_height(), 520)
        largura_grafico = max((largura_janela - 72) // 2, 420)
        altura_grafico = max(altura_janela - 130, 260)

        self._hist_zoom_original.ajustar_tamanho(largura_grafico, altura_grafico)
        self._hist_zoom_resultado.ajustar_tamanho(largura_grafico, altura_grafico)

    def _ao_redimensionar_zoom_histogramas(self, evento: tk.Event) -> None:
        if self._janela_zoom_histogramas is None or evento.widget is not self._janela_zoom_histogramas:
            return
        self._atualizar_tamanho_zoom_histogramas()

    def _ao_fechar_zoom_histogramas(self) -> None:
        if self._janela_zoom_histogramas is not None and self._janela_zoom_histogramas.winfo_exists():
            self._janela_zoom_histogramas.destroy()
        self._janela_zoom_histogramas = None
        self._hist_zoom_original = None
        self._hist_zoom_resultado = None

    def abrir_zoom_histogramas(self) -> None:
        # zoom: abre uma janela auxiliar maior para apresentar os histogramas na tela
        if self._janela_zoom_histogramas is not None and self._janela_zoom_histogramas.winfo_exists():
            self._janela_zoom_histogramas.deiconify()
            self._janela_zoom_histogramas.lift()
            self._janela_zoom_histogramas.focus_force()
            return

        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        largura_janela = min(max(largura_tela - 120, 980), 1280)
        altura_janela = min(max(altura_tela - 180, 520), 760)
        posicao_x = max((largura_tela - largura_janela) // 2, 0)
        posicao_y = max((altura_tela - altura_janela) // 3, 0)

        janela = tk.Toplevel(self)
        janela.title("Histogramas ampliados - UEPB")
        janela.configure(bg=tema.COR_FUNDO)
        janela.geometry(f"{largura_janela}x{altura_janela}+{posicao_x}+{posicao_y}")
        janela.minsize(980, 520)
        janela.transient(self.winfo_toplevel())
        janela.protocol("WM_DELETE_WINDOW", self._ao_fechar_zoom_histogramas)
        janela.bind("<Configure>", self._ao_redimensionar_zoom_histogramas)
        self._janela_zoom_histogramas = janela

        cabecalho = ttk.Frame(janela, padding=(14, 12, 14, 4), style="Root.TFrame")
        cabecalho.pack(fill="x")
        ttk.Label(
            cabecalho,
            text="Visualizacao ampliada dos histogramas para apresentacao.",
            style="Texto.TLabel",
        ).pack(side="left")

        conteudo = ttk.Frame(janela, padding=(14, 8, 14, 14), style="Root.TFrame")
        conteudo.pack(fill="both", expand=True)
        conteudo.columnconfigure(0, weight=1)
        conteudo.columnconfigure(1, weight=1)

        largura_grafico = max((largura_janela - 72) // 2, 420)
        altura_grafico = max(altura_janela - 130, 260)

        self._hist_zoom_original = GraficoHistograma(
            conteudo,
            "Histograma original ampliado",
            largura=largura_grafico,
            altura=altura_grafico,
        )
        self._hist_zoom_original.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self._hist_zoom_resultado = GraficoHistograma(
            conteudo,
            "Histograma resultado ampliado",
            largura=largura_grafico,
            altura=altura_grafico,
        )
        self._hist_zoom_resultado.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        hist_original, cor_original = self.hist_original.obter_estado()
        hist_resultado, cor_resultado = self.hist_resultado.obter_estado()
        self._hist_zoom_original.desenhar(hist_original, cor=cor_original)
        self._hist_zoom_resultado.desenhar(hist_resultado, cor=cor_resultado)
        self._atualizar_tamanho_zoom_histogramas()

    def _ao_mudar_transformacao(self) -> None:
        # parametros: ajusta os campos visiveis de acordo com a transformacao escolhida
        nome = self.transformacao.get()
        configuracoes = {
            NOME_NEGATIVO_IMAGEM: ("", "", False, False),
            NOME_TRANSFORMACAO_GAMMA: ("Gamma", "Constante c", True, True),
            NOME_TRANSFORMACAO_LOGARITMO: ("Constante a", "", True, False),
            NOME_FUNCAO_TRANSFERENCIA_GERAL: ("Centro", "Largura", True, True),
            NOME_FUNCAO_TRANSFERENCIA_FAIXA_DINAMICA: ("Faixa de saida", "", True, False),
            NOME_FUNCAO_TRANSFERENCIA_LINEAR: ("Coeficiente a", "Coeficiente b", True, True),
            NOME_EQUALIZE_HISTOGRAMA: ("", "", False, False),
        }
        rotulo_1, rotulo_2, usa_1, usa_2 = configuracoes[nome]
        self.rotulo_parametro_1.set(rotulo_1 or "Parametro 1")
        self.rotulo_parametro_2.set(rotulo_2 or "Parametro 2")

        padroes = {
            NOME_NEGATIVO_IMAGEM: ("", ""),
            NOME_TRANSFORMACAO_GAMMA: ("0.6", "1.0"),
            NOME_TRANSFORMACAO_LOGARITMO: ("", ""),
            NOME_FUNCAO_TRANSFERENCIA_GERAL: ("127", "25"),
            NOME_FUNCAO_TRANSFERENCIA_FAIXA_DINAMICA: ("255", ""),
            NOME_FUNCAO_TRANSFERENCIA_LINEAR: ("1.2", "0"),
            NOME_EQUALIZE_HISTOGRAMA: ("", ""),
        }
        self.parametro_1.set(padroes[nome][0])
        self.parametro_2.set(padroes[nome][1])

        self.entrada_1.configure(state="normal" if usa_1 else "disabled")
        self.entrada_2.configure(state="normal" if usa_2 else "disabled")

    def carregar_imagem(self) -> None:
        imagem = _abrir_dialogo_imagem()
        if imagem is None:
            return
        self.imagem_origem = imagem
        self.imagem_resultado = None
        self.painel_original.mostrar_imagem(imagem, texto_info=_descricao_imagem(imagem))
        self.painel_resultado.limpar("Aguardando transformacao.")
        histograma = calcular_histograma(imagem.matriz)
        self._atualizar_histogramas(
            histograma,
            cor_original=tema.COR_DESTAQUE,
            hist_resultado=histograma,
            cor_resultado=tema.COR_DESTAQUE_SUAVE,
        )
        self.status.set(f"Imagem carregada: {_descricao_imagem(imagem)}")

    def limpar_imagens(self) -> None:
        self.imagem_origem = None
        self.imagem_resultado = None
        self.painel_original.limpar()
        self.painel_resultado.limpar()
        self.hist_original.desenhar(np.zeros(256, dtype=np.float64), cor=tema.COR_DESTAQUE)
        self.hist_resultado.desenhar(np.zeros(256, dtype=np.float64), cor=tema.COR_DESTAQUE_SUAVE)
        if self._hist_zoom_original is not None:
            self._hist_zoom_original.desenhar(np.zeros(256, dtype=np.float64), cor=tema.COR_DESTAQUE)
        if self._hist_zoom_resultado is not None:
            self._hist_zoom_resultado.desenhar(np.zeros(256, dtype=np.float64), cor=tema.COR_DESTAQUE_SUAVE)
        self.status.set("Imagens removidas. Carregue uma imagem para testar as transforma\u00e7\u00f5es de intensidade.")

    def aplicar_transformacao(self) -> None:
        if self.imagem_origem is None:
            self.status.set("Carregue uma imagem antes de aplicar uma transformacao.")
            return

        nome = self.transformacao.get()
        matriz = self.imagem_origem.matriz
        try:
            # selecao: chama a funcao de intensidade correspondente ao item da interface
            if nome == NOME_NEGATIVO_IMAGEM:
                resultado = negativo(matriz)
            elif nome == NOME_TRANSFORMACAO_GAMMA:
                resultado = transformacao_gamma(matriz, float(self.parametro_1.get() or "0.6"), float(self.parametro_2.get() or "1.0"))
            elif nome == NOME_TRANSFORMACAO_LOGARITMO:
                constante = float(self.parametro_1.get()) if self.parametro_1.get() else None
                resultado = transformacao_logaritmica(matriz, constante)
            elif nome == NOME_FUNCAO_TRANSFERENCIA_LINEAR:
                resultado = transformacao_linear(matriz, float(self.parametro_1.get() or "1.0"), float(self.parametro_2.get() or "0.0"))
            elif nome == NOME_FUNCAO_TRANSFERENCIA_FAIXA_DINAMICA:
                resultado = faixa_dinamica(matriz, int(float(self.parametro_1.get() or "255")))
            elif nome == NOME_FUNCAO_TRANSFERENCIA_GERAL:
                resultado = funcao_sigmoide(matriz, float(self.parametro_1.get() or "127"), float(self.parametro_2.get() or "25"))
            else:
                resultado, hist_original, hist_resultado = equalizar_histograma(matriz)
                self._atualizar_histogramas(
                    hist_original,
                    cor_original=tema.COR_DESTAQUE,
                    hist_resultado=hist_resultado,
                    cor_resultado=tema.COR_SUCESSO,
                )
                self.imagem_resultado = criar_imagem(resultado, nome="histograma_equalizado")
                self.painel_resultado.mostrar_imagem(self.imagem_resultado, texto_info=_descricao_imagem(self.imagem_resultado))
                self.status.set("Equaliza\u00e7\u00e3o de histograma concluida.")
                return
        except ValueError as erro:
            self.status.set(f"Parametros invalidos: {erro}")
            return

        nomes_saida = {
            NOME_NEGATIVO_IMAGEM: "negativo_imagem",
            NOME_TRANSFORMACAO_GAMMA: "transformacao_gamma",
            NOME_TRANSFORMACAO_LOGARITMO: "transformacao_logaritmo",
            NOME_FUNCAO_TRANSFERENCIA_GERAL: "funcao_transferencia_intensidade_geral",
            NOME_FUNCAO_TRANSFERENCIA_FAIXA_DINAMICA: "funcao_transferencia_faixa_dinamica",
            NOME_FUNCAO_TRANSFERENCIA_LINEAR: "funcao_transferencia_linear",
            NOME_EQUALIZE_HISTOGRAMA: "equalize_histograma",
        }
        self.imagem_resultado = criar_imagem(resultado, nome=nomes_saida[nome])
        self.painel_resultado.mostrar_imagem(self.imagem_resultado, texto_info=_descricao_imagem(self.imagem_resultado))
        self._atualizar_histogramas(
            calcular_histograma(self.imagem_origem.matriz),
            cor_original=tema.COR_DESTAQUE,
            hist_resultado=calcular_histograma(resultado),
            cor_resultado=tema.COR_SUCESSO,
        )
        self.status.set(f"Transformacao '{nome}' aplicada com sucesso.")

    def salvar_resultado(self) -> None:
        if self.imagem_resultado is None:
            self.status.set("Nao ha resultado para salvar.")
            return
        caminho = _salvar_dialogo_resultado(self.imagem_resultado)
        if caminho is not None:
            self.status.set(f"Resultado salvo em: {caminho}")
