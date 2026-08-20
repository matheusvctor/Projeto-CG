from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from laboratorio_imagens import tema
from laboratorio_imagens.ui.abas_avancadas import AbaGeometria, AbaMorfismo, AbaMorfologia
from laboratorio_imagens.ui.abas_processamento import AbaFiltros, AbaIntensidadeHistograma, AbaOperacoes
from laboratorio_imagens.ui.widgets import FrameRolavel


def _criar_aba_rolavel(master, classe_aba):
    contenedor = FrameRolavel(master, padding=0, style="Root.TFrame")
    aba = classe_aba(contenedor.conteudo)
    aba.pack(fill="x", anchor="n")
    return contenedor


class JanelaPrincipal(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Processamento de Imagens")
        largura_inicial = 1420
        altura_inicial = 880
        self.geometry(f"{largura_inicial}x{altura_inicial}")
        self.configure(bg=tema.COR_FUNDO)
        self._centralizar_janela(largura_inicial, altura_inicial)
        self._configurar_estilo()

        self._modulos: dict[str, dict] = {}
        self._botoes_sidebar: dict[str, tk.Frame] = {}
        self._modulo_ativo: str | None = None

        self._montar_interface()

    def _centralizar_janela(self, largura: int, altura: int) -> None:
        self.update_idletasks()
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        posicao_x = max((largura_tela - largura) // 2, 0)
        posicao_y = max((altura_tela - altura) // 2, 15)
        self.geometry(f"{largura}x{altura}+{posicao_x}+{posicao_y}")

    def _configurar_estilo(self) -> None:
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except Exception:
            pass
        tema.configure_ttk_styles(self)

        estilo.configure("Root.TFrame", background=tema.COR_FUNDO)
        estilo.configure(
            "Card.TLabelframe",
            background=tema.COR_PAINEL,
            bordercolor=tema.COR_BORDA,
            lightcolor=tema.COR_BORDA,
            darkcolor=tema.COR_BORDA,
            borderwidth=1,
            relief="solid",
        )
        estilo.configure(
            "Card.TLabelframe.Label",
            background=tema.COR_PAINEL,
            foreground=tema.COR_TEXTO,
            font=tema.FONTE_SUBTITULO,
        )
        estilo.configure("Texto.TLabel", background=tema.COR_FUNDO, foreground=tema.COR_TEXTO, font=tema.FONTE_CORPO)
        estilo.configure("Status.TLabel", background=tema.COR_FUNDO, foreground=tema.COR_TEXTO_MUTED, font=tema.FONTE_PEQUENA)

        estilo.configure(
            "Action.TButton",
            background=tema.COR_DESTAQUE,
            foreground="#000000",
            font=tema.FONTE_SUBTITULO,
            padding=(14, 6),
            borderwidth=0,
            relief="flat",
        )
        estilo.map(
            "Action.TButton",
            background=[("active", tema.COR_DESTAQUE_HOVER), ("disabled", tema.COR_PAINEL_ALT)],
            foreground=[("disabled", tema.COR_TEXTO_MUTED)],
        )

        estilo.configure(
            "Secondary.TButton",
            background=tema.COR_PAINEL_ALT,
            foreground=tema.COR_TEXTO,
            font=tema.FONTE_CORPO,
            padding=(10, 5),
            borderwidth=0,
            relief="flat",
        )
        estilo.map(
            "Secondary.TButton",
            background=[("active", tema.COR_BORDA)],
        )

    def _montar_interface(self) -> None:
        # Container principal dividido em Sidebar e Área de Conteúdo
        container_principal = tk.Frame(self, bg=tema.COR_FUNDO)
        container_principal.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # 1. SIDEBAR LATERAL (Menu de Navegação)
        # ----------------------------------------------------
        sidebar = tk.Frame(container_principal, bg=tema.COR_SIDEBAR, width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Header limpo da Sidebar
        topo_sidebar = tk.Frame(sidebar, bg=tema.COR_SIDEBAR, padx=18, pady=24)
        topo_sidebar.pack(fill="x")

        tk.Label(
            topo_sidebar,
            text="Menu Principal",
            bg=tema.COR_SIDEBAR,
            fg=tema.COR_TEXTO,
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")

        # Divisor sutil
        tk.Frame(sidebar, bg=tema.COR_BORDA, height=1).pack(fill="x", padx=16, pady=(0, 16))

        # Menu de Itens da Sidebar
        self.container_menu = tk.Frame(sidebar, bg=tema.COR_SIDEBAR)
        self.container_menu.pack(fill="x", expand=True, anchor="n")

        # ----------------------------------------------------
        # 2. ÁREA DE CONTEÚDO À DIREITA
        # ----------------------------------------------------
        area_direita = tk.Frame(container_principal, bg=tema.COR_FUNDO)
        area_direita.pack(side="right", fill="both", expand=True)

        # Barra Superior de Contexto
        topbar = tk.Frame(area_direita, bg=tema.COR_PAINEL, height=52, padx=22)
        topbar.pack(fill="x")

        self.rotulo_breadcrumb = tk.Label(
            topbar,
            text="Filtros Espaciais",
            bg=tema.COR_PAINEL,
            fg=tema.COR_DESTAQUE,
            font=("Segoe UI", 12, "bold"),
        )
        self.rotulo_breadcrumb.pack(side="left", pady=14)

        # Container dos Módulos (telas trocadas)
        self.container_conteudo = tk.Frame(area_direita, bg=tema.COR_FUNDO, padx=16, pady=12)
        self.container_conteudo.pack(fill="both", expand=True)

        # Inicialização dos Módulos
        self._registrar_modulos()
        self._selecionar_modulo("filtros")

    def _registrar_modulos(self) -> None:
        itens_modulo = [
            ("filtros", "⚡  Filtros Espaciais", "Filtros Espaciais", AbaFiltros, True),
            ("operacoes", "🔀  Operações & Lógica", "Operações Aritméticas e Lógicas", AbaOperacoes, True),
            ("intensidade", "📊  Intensidade & Histograma", "Transformações de Intensidade e Histograma", AbaIntensidadeHistograma, True),
            ("morfologia", "🧩  Morfologia Matemática", "Morfologia Binária e Nível de Cinza", AbaMorfologia, True),
            ("geometria", "📐  Transformações 2D", "Transformações Geométricas", AbaGeometria, True),
            ("morfismo", "⏳  Morfismo Temporal", "Morfismo Temporal e Triangulação", AbaMorfismo, False),
        ]

        for chave, titulo_menu, titulo_breadcrumb, classe_aba, rolavel in itens_modulo:
            # Criação do item de menu na sidebar
            item_btn = tk.Frame(self.container_menu, bg=tema.COR_SIDEBAR, cursor="hand2")
            item_btn.pack(fill="x", padx=10, pady=3)

            barra_indicadora = tk.Frame(item_btn, bg=tema.COR_SIDEBAR, width=4)
            barra_indicadora.pack(side="left", fill="y")

            rotulo = tk.Label(
                item_btn,
                text=titulo_menu,
                bg=tema.COR_SIDEBAR,
                fg=tema.COR_TEXTO_MUTED,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
                padx=10,
                pady=10,
                cursor="hand2",
            )
            rotulo.pack(side="left", fill="both", expand=True)

            # Instanciação do frame de conteúdo
            if rolavel:
                frame_modulo = _criar_aba_rolavel(self.container_conteudo, classe_aba)
            else:
                frame_modulo = classe_aba(self.container_conteudo)

            self._modulos[chave] = {
                "titulo": titulo_breadcrumb,
                "frame": frame_modulo,
                "item_btn": item_btn,
                "rotulo": rotulo,
                "indicador": barra_indicadora,
            }

            # Binds de clique e hover
            for widget in (item_btn, rotulo):
                widget.bind("<Button-1>", lambda _e, c=chave: self._selecionar_modulo(c))
                widget.bind("<Enter>", lambda _e, c=chave: self._ao_hover_menu(c, True))
                widget.bind("<Leave>", lambda _e, c=chave: self._ao_hover_menu(c, False))

    def _ao_hover_menu(self, chave: str, ativo: bool) -> None:
        if chave == self._modulo_ativo:
            return
        dados = self._modulos[chave]
        cor_fundo = tema.COR_PAINEL if ativo else tema.COR_SIDEBAR
        cor_texto = tema.COR_TEXTO if ativo else tema.COR_TEXTO_MUTED
        dados["item_btn"].configure(bg=cor_fundo)
        dados["rotulo"].configure(bg=cor_fundo, fg=cor_texto)

    def _selecionar_modulo(self, chave: str) -> None:
        if self._modulo_ativo == chave:
            return

        # Desativa o módulo anterior
        if self._modulo_ativo is not None:
            dados_antigos = self._modulos[self._modulo_ativo]
            dados_antigos["frame"].pack_forget()
            dados_antigos["item_btn"].configure(bg=tema.COR_SIDEBAR)
            dados_antigos["rotulo"].configure(bg=tema.COR_SIDEBAR, fg=tema.COR_TEXTO_MUTED)
            dados_antigos["indicador"].configure(bg=tema.COR_SIDEBAR)

        # Ativa o novo módulo
        self._modulo_ativo = chave
        dados_novos = self._modulos[chave]

        dados_novos["item_btn"].configure(bg=tema.COR_PAINEL)
        dados_novos["rotulo"].configure(bg=tema.COR_PAINEL, fg="#ffffff")
        dados_novos["indicador"].configure(bg=tema.COR_DESTAQUE)

        self.rotulo_breadcrumb.configure(text=dados_novos["titulo"])
        dados_novos["frame"].pack(fill="both", expand=True)
