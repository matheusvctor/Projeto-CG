import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import sys

# Garante acesso à raiz do projeto
sys.path.insert(0, os.path.dirname(__file__))
import theme


def _executar_modulo(nome_modulo: str):
    """Executa diretamente o módulo solicitado dentro do mesmo processo ou subprocesso."""
    diretorio_base = os.path.dirname(__file__)
    
    if nome_modulo == "q1_primitivas":
        caminho_q1 = os.path.join(diretorio_base, "mod_primitivas", "Questao1")
        sys.path.insert(0, caminho_q1)
        from mod_primitivas.Questao1.run_menu import main as main_q1
        main_q1()
    elif nome_modulo == "q2_cohen":
        caminho_q2 = os.path.join(diretorio_base, "mod_recortes", "Questao2")
        sys.path.insert(0, caminho_q2)
        from mod_recortes.Questao2.apps.cohen_sutherland_ui import AppCohenSutherland
        root = tk.Tk()
        AppCohenSutherland(root)
        root.mainloop()
    elif nome_modulo == "q2_sutherland":
        caminho_q2 = os.path.join(diretorio_base, "mod_recortes", "Questao2")
        sys.path.insert(0, caminho_q2)
        from mod_recortes.Questao2.apps.sutherland_hodgman_ui import AppSutherlandHodgman
        root = tk.Tk()
        AppSutherlandHodgman(root)
        root.mainloop()
    elif nome_modulo == "q2_weiler":
        caminho_q2 = os.path.join(diretorio_base, "mod_recortes", "Questao2")
        sys.path.insert(0, caminho_q2)
        from mod_recortes.Questao2.apps.weiler_atherton_ui import AppWeilerAtherton
        root = tk.Tk()
        AppWeilerAtherton(root)
        root.mainloop()
    elif nome_modulo == "q3_3d":
        caminho_q3 = os.path.join(diretorio_base, "mod_3d", "Questao3")
        sys.path.insert(0, caminho_q3)
        import importlib.util
        spec = importlib.util.spec_from_file_location("questao3_mod", os.path.join(caminho_q3, "Questao3..py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["questao3_mod"] = mod
        spec.loader.exec_module(mod)
        mod.setup_tkinter()
        mod.root.mainloop()
    elif nome_modulo == "q4_imagens":
        caminho_q4 = os.path.join(diretorio_base, "mod_imagens", "Questao4")
        sys.path.insert(0, caminho_q4)
        import importlib.util
        spec = importlib.util.spec_from_file_location("questao4_mod", os.path.join(caminho_q4, "transformacoes.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules["questao4_mod"] = mod
        spec.loader.exec_module(mod)
        if hasattr(mod, "main"):
            mod.main()


class MainMenu:
    def __init__(self, root):
        """Configura a janela principal moderna com barra lateral e painel central interativo."""
        self.root = root
        self.root.title("Laboratório de Computação Gráfica")
        self.root.geometry("1080x700")
        self.root.minsize(980, 620)
        self.root.configure(bg=theme.BG_APP)
        self.root.eval('tk::PlaceWindow . center')

        self.modulos = [
            {
                "id": "q1_primitivas",
                "titulo": "Primitivas, Cônicas & Bézier",
                "subtitulo": "Questão 1 & Questão 5",
                "icone": "📐",
                "descricao": "Rasterização por DDA e Ponto Médio em todos os oitantes, circunferências, elipse, parábola, hipérbole e Curvas de Bézier cúbicas com 4 pontos de controle.",
                "tags": ["DDA", "Bresenham", "Cônicas", "Splines Bézier"],
                "pasta": "mod_primitivas/Questao1",
                "script": "run_menu.py"
            },
            {
                "id": "q2_cohen",
                "titulo": "Recorte Cohen-Sutherland",
                "subtitulo": "Questão 2 (Linhas)",
                "icone": "✂️",
                "descricao": "Algoritmo de recorte de segmentos por códigos de região (Outcodes de 4 bits: TOP, BOTTOM, RIGHT, LEFT) com modo de animação contínua em rotação horária.",
                "tags": ["Outcodes", "Rejeição Trivial", "Animação Rotativa"],
                "pasta": "mod_recortes/Questao2",
                "script": "apps/cohen_sutherland_ui.py"
            },
            {
                "id": "q2_sutherland",
                "titulo": "Recorte Sutherland-Hodgman",
                "subtitulo": "Questão 2 (Polígonos Convexos)",
                "icone": "⬡",
                "descricao": "Recorte de polígonos contra as 4 bordas da janela com rastreamento visual das regras e cálculo analítico de interseções.",
                "tags": ["Polígonos", "4 Bordas", "Passo a Passo"],
                "pasta": "mod_recortes/Questao2",
                "script": "apps/sutherland_hodgman_ui.py"
            },
            {
                "id": "q2_weiler",
                "titulo": "Recorte Weiler-Atherton",
                "subtitulo": "Questão 2 (Polígonos Côncavos)",
                "icone": "✂️",
                "descricao": "Recorte avançado de polígonos côncavos arbitrários e geração de múltiplos sub-polígonos desconectados por travessia de listas encadeadas circulares.",
                "tags": ["Polígonos Côncavos", "Múltiplos Sub-polígonos", "Entrada/Saída"],
                "pasta": "mod_recortes/Questao2",
                "script": "apps/weiler_atherton_ui.py"
            },
            {
                "id": "q3_3d",
                "titulo": "Modelagem 3D & Viewport",
                "subtitulo": "Questão 3 (3D / Isométrica)",
                "icone": "📦",
                "descricao": "Composição de transformações tridimensionais (X, Y, Z), Projeção Paralela Isométrica e mapeamento da Janela do Mundo para a Viewport com histórico.",
                "tags": ["3D", "Projeção Isométrica", "Viewport", "Cisalhamento 3D"],
                "pasta": "mod_3d/Questao3",
                "script": "Questao3..py"
            },
            {
                "id": "q4_imagens",
                "titulo": "Transformações em Imagens PGM",
                "subtitulo": "Questão 4 (Matrizes de Imagem)",
                "icone": "🖼️",
                "descricao": "Operadores espaciais em matrizes de imagem PGM por Mapeamento Inverso e interpolação: Escala, Rotação, Translação, Cisalhamento e Reflexão.",
                "tags": ["PGM NetPBM", "Mapeamento Inverso", "Bounding Box"],
                "pasta": "mod_imagens/Questao4",
                "script": "transformacoes.py"
            }
        ]

        self.modulo_ativo = self.modulos[0]
        self.build_ui()

    def build_ui(self):
        """Monta o layout com Sidebar à esquerda e Card de apresentação à direita (sem navbar superior)."""
        # Corpo principal (ocupa toda a janela)
        corpo = tk.Frame(self.root, bg=theme.BG_APP)
        corpo.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Barra Lateral (Sidebar)
        sidebar = tk.Frame(corpo, bg=theme.BG_PANEL, width=320)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Título e Identidade integrados na própria Sidebar
        tk.Label(
            sidebar,
            text="⬢ COMPUTACÃO GRÁFICA",
            font=theme.FONT_HEADER,
            bg=theme.BG_PANEL,
            fg=theme.CYAN_GLOW
        ).pack(anchor="w", padx=20, pady=(20, 2))

        tk.Label(
            sidebar,
            text="Ambiente Integrado — Unidade 1",
            font=theme.FONT_NORMAL,
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # Linha divisória sutil
        tk.Frame(sidebar, bg=theme.BORDER_COLOR, height=1).pack(fill=tk.X, padx=20, pady=(0, 15))

        tk.Label(
            sidebar,
            text="MÓDULOS DO PROJETO",
            font=theme.FONT_SUBTITLE,
            bg=theme.BG_PANEL,
            fg=theme.FG_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 10))


        self.botoes_sidebar = []
        for mod in self.modulos:
            btn = tk.Button(
                sidebar,
                text=f"{mod['icone']}  {mod['titulo']}",
                font=theme.FONT_NORMAL,
                bg=theme.BG_PANEL,
                fg=theme.FG_TEXT,
                activebackground=theme.BG_INPUT,
                activeforeground=theme.CYAN_GLOW,
                anchor="w",
                relief="flat",
                cursor="hand2",
                padx=15,
                pady=10,
                command=lambda m=mod: self.selecionar_modulo(m)
            )
            btn.pack(fill=tk.X, padx=10, pady=3)
            self.botoes_sidebar.append((mod["id"], btn))

        # Painel Central de Detalhes e Ação
        self.painel_conteudo = tk.Frame(corpo, bg=theme.BG_APP, padx=40, pady=30)
        self.painel_conteudo.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.renderizar_detalhes_modulo()

    def selecionar_modulo(self, mod):
        """Atualiza a seleção do módulo e renderiza os detalhes correspondentes."""
        self.modulo_ativo = mod
        for mod_id, btn in self.botoes_sidebar:
            if mod_id == mod["id"]:
                btn.config(bg=theme.ACCENT, fg="#ffffff")
            else:
                btn.config(bg=theme.BG_PANEL, fg=theme.FG_TEXT)
        self.renderizar_detalhes_modulo()

    def renderizar_detalhes_modulo(self):
        """Renderiza o card visual interativo do módulo selecionado."""
        for widget in self.painel_conteudo.winfo_children():
            widget.destroy()

        mod = self.modulo_ativo

        # Card Principal
        card = tk.Frame(self.painel_conteudo, bg=theme.BG_PANEL, bd=1, relief="solid")
        card.pack(fill=tk.BOTH, expand=True, pady=10)

        # Header do Card
        head = tk.Frame(card, bg=theme.BG_PANEL, padx=25, pady=20)
        head.pack(fill=tk.X)

        tk.Label(
            head,
            text=f"{mod['icone']}  {mod['titulo']}",
            font=theme.FONT_HEADER,
            bg=theme.BG_PANEL,
            fg=theme.CYAN_GLOW
        ).pack(anchor="w")

        tk.Label(
            head,
            text=mod["subtitulo"],
            font=theme.FONT_SUBTITLE,
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT
        ).pack(anchor="w", pady=(2, 0))

        # Divisor
        tk.Frame(card, bg=theme.BORDER_COLOR, height=1).pack(fill=tk.X, padx=25)

        # Corpo do Card
        body = tk.Frame(card, bg=theme.BG_PANEL, padx=25, pady=25)
        body.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            body,
            text="Descrição Técnica:",
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL,
            fg=theme.FG_TEXT
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            body,
            text=mod["descricao"],
            font=theme.FONT_NORMAL,
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT,
            wraplength=580,
            justify="left"
        ).pack(anchor="w", pady=(0, 20))

        # Tags de Funcionalidades
        tk.Label(
            body,
            text="Recursos Implementados:",
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL,
            fg=theme.FG_TEXT
        ).pack(anchor="w", pady=(0, 8))

        tag_frame = tk.Frame(body, bg=theme.BG_PANEL)
        tag_frame.pack(anchor="w", pady=(0, 30))

        for tag in mod["tags"]:
            tk.Label(
                tag_frame,
                text=f" ✓ {tag} ",
                font=theme.FONT_NORMAL,
                bg=theme.BG_INPUT,
                fg=theme.CYAN_GLOW,
                padx=8,
                pady=4
            ).pack(side=tk.LEFT, padx=(0, 8))

        # Botão de Ação / Lançamento
        btn_action = tk.Button(
            body,
            text=f"Abrir Módulo: {mod['titulo']} ➔",
            font=theme.FONT_TITLE,
            bg=theme.SUCCESS,
            fg="#ffffff",
            activebackground=theme.SUCCESS_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=25,
            pady=14,
            command=lambda: self.abrir_modulo(mod["id"], mod["pasta"], mod["script"])
        )
        btn_action.pack(anchor="w", pady=(10, 0))

    def abrir_modulo(self, chave_modulo, pasta_base, script):
        """Abre o módulo de forma autônoma e compatível com PyInstaller."""
        diretorio_trabalho = os.path.join(os.path.dirname(__file__), pasta_base)
        caminho_script = os.path.join(diretorio_trabalho, script)
        
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(__file__) + os.pathsep + diretorio_trabalho + os.pathsep + env.get("PYTHONPATH", "")

        if getattr(sys, 'frozen', False):
            try:
                subprocess.Popen([sys.executable, "--modulo", chave_modulo], cwd=os.path.dirname(__file__), env=env)
                return
            except Exception:
                pass

        try:
            subprocess.Popen([sys.executable, caminho_script], cwd=diretorio_trabalho, env=env)
        except Exception:
            try:
                subprocess.Popen(["python", caminho_script], cwd=diretorio_trabalho, env=env)
            except Exception:
                _executar_modulo(chave_modulo)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--modulo":
        _executar_modulo(sys.argv[2])
    else:
        root = tk.Tk()
        app = MainMenu(root)
        root.mainloop()
