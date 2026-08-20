# ==========================================
# TEMA VISUAL - COMPUTAÇÃO GRÁFICA (DARK SLATE & CYAN)
# ==========================================

# Paleta de Cores Principais
BG_APP = "#0f172a"          # Fundo geral Slate Escuro Profundo
BG_PANEL = "#1e293b"        # Painéis, cards e controles
BG_HEADER = "#090d16"       # Topbar e rodapé
BG_CANVAS = "#050811"       # Tela de desenho / Canvas preto nítido
BG_INPUT = "#334155"        # Campos de entrada de texto

# Cores de Tipografia
FG_TEXT = "#f8fafc"         # Texto principal (Branco neve)
FG_SUBTEXT = "#94a3b8"      # Subtexto e descrições (Cinza suave)
FG_MUTED = "#64748b"        # Rótulos secundários

# Cores de Destaque e Ação
ACCENT = "#0284c7"          # Azul vibrante de ação primária
ACCENT_HOVER = "#0ea5e9"    # Ciano/Azul claro (Hover)
CYAN_GLOW = "#38bdf8"       # Ciano fluorescente para realces
SUCCESS = "#10b981"         # Verde Esmeralda (Aplicar/Processar)
SUCCESS_HOVER = "#059669"
DANGER = "#ef4444"          # Vermelho Rubi (Reset/Limpar)
DANGER_HOVER = "#dc2626"
WARNING = "#f59e0b"         # Âmbar (Avisos)

# Cores de Desenho e Grade (Canvas)
GRID_COLOR = "#1e293b"      # Linhas de grade sutis
AXIS_COLOR = "#475569"      # Eixos cartesianos X e Y
BORDER_COLOR = "#334155"    # Bordas de separação
LINE_COLOR_2D = "#38bdf8"   # Retas e primitivas 2D (Ciano)
LINE_COLOR_3D = "#94a3b8"   # Cubo Original 3D (Cinza claro)
LINE_COLOR_3D_PROC = "#10b981" # Cubo Processado / Viewport (Verde)
POINT_COLOR = "#f43f5e"     # Vértices e pontos de controle (Rosa)

# Tipografia
FONT_HEADER = ("Segoe UI", 16, "bold")
FONT_TITLE = ("Segoe UI", 12, "bold")
FONT_SUBTITLE = ("Segoe UI", 10, "bold")
FONT_NORMAL = ("Segoe UI", 9)
FONT_CODE = ("Consolas", 9)


def make_btn(parent, text, command, btn_type="primary", **kwargs):
    """Cria um botão Tkinter padronizado, moderno e responsivo com feedback visual."""
    import tkinter as tk
    configs = {
        "primary": {
            "bg": ACCENT, "fg": "#ffffff",
            "activebackground": ACCENT_HOVER, "activeforeground": "#ffffff",
            "font": FONT_SUBTITLE, "relief": "flat", "cursor": "hand2",
            "padx": 12, "pady": 6
        },
        "success": {
            "bg": SUCCESS, "fg": "#ffffff",
            "activebackground": SUCCESS_HOVER, "activeforeground": "#ffffff",
            "font": FONT_TITLE, "relief": "flat", "cursor": "hand2",
            "padx": 14, "pady": 8
        },
        "danger": {
            "bg": DANGER, "fg": "#ffffff",
            "activebackground": DANGER_HOVER, "activeforeground": "#ffffff",
            "font": FONT_SUBTITLE, "relief": "flat", "cursor": "hand2",
            "padx": 10, "pady": 5
        },
        "secondary": {
            "bg": BG_INPUT, "fg": FG_TEXT,
            "activebackground": BORDER_COLOR, "activeforeground": CYAN_GLOW,
            "font": FONT_NORMAL, "relief": "flat", "cursor": "hand2",
            "padx": 8, "pady": 4
        },
        "action": {
            "bg": CYAN_GLOW, "fg": "#090d16",
            "activebackground": "#7dd3fc", "activeforeground": "#000000",
            "font": FONT_TITLE, "relief": "flat", "cursor": "hand2",
            "padx": 16, "pady": 8
        },
        "warning": {
            "bg": WARNING, "fg": "#000000",
            "activebackground": "#fbbf24", "activeforeground": "#000000",
            "font": FONT_SUBTITLE, "relief": "flat", "cursor": "hand2",
            "padx": 10, "pady": 5
        }
    }
    cfg = configs.get(btn_type, configs["primary"]).copy()
    cfg.update(kwargs)
    return tk.Button(parent, text=text, command=command, **cfg)


def configure_ttk_styles(root=None):
    """Configura o visual escuro elegante para todos os widgets TTK da aplicação."""
    from tkinter import ttk
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(".", background=BG_APP, foreground=FG_TEXT, font=FONT_NORMAL)
    style.configure("TFrame", background=BG_APP)
    style.configure(
        "TLabelframe",
        background=BG_PANEL,
        bordercolor=BORDER_COLOR,
        darkcolor=BORDER_COLOR,
        lightcolor=BORDER_COLOR,
        borderwidth=1,
    )
    style.configure("TLabelframe.Label", background=BG_PANEL, foreground=CYAN_GLOW, font=FONT_SUBTITLE)
    style.configure("TLabel", background=BG_APP, foreground=FG_TEXT, font=FONT_NORMAL)
    style.configure("TCheckbutton", background=BG_APP, foreground=FG_TEXT, font=FONT_NORMAL)
    style.configure(
        "TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_PANEL,
        foreground=FG_TEXT,
        selectbackground=ACCENT,
        selectforeground="#ffffff",
        arrowcolor=CYAN_GLOW,
        font=FONT_NORMAL,
        padding=3,
    )
    style.map(
        "TCombobox",
        fieldbackground=[
            ("readonly", BG_INPUT),
            ("active", BG_INPUT),
            ("focus", BG_INPUT),
            ("disabled", BG_PANEL),
            ("!disabled", BG_INPUT),
        ],
        background=[
            ("readonly", BG_PANEL),
            ("active", BG_PANEL),
            ("focus", BG_PANEL),
            ("disabled", BG_APP),
            ("!disabled", BG_PANEL),
        ],
        foreground=[
            ("readonly", FG_TEXT),
            ("active", FG_TEXT),
            ("focus", FG_TEXT),
            ("disabled", FG_MUTED),
            ("!disabled", FG_TEXT),
        ],
        arrowcolor=[
            ("readonly", CYAN_GLOW),
            ("active", "#ffffff"),
            ("disabled", FG_MUTED),
            ("!disabled", CYAN_GLOW),
        ],
    )
    if root is not None:
        try:
            root.option_add("*TCombobox*Listbox.background", BG_PANEL)
            root.option_add("*TCombobox*Listbox.foreground", FG_TEXT)
            root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
            root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
            root.option_add("*TCombobox*Listbox.font", FONT_NORMAL)
        except Exception:
            pass

    style.configure("TSpinbox", fieldbackground=BG_INPUT, background=BG_PANEL, foreground=FG_TEXT, font=FONT_NORMAL)
    style.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG_TEXT, font=FONT_NORMAL)
    
    style.configure("TNotebook", background=BG_PANEL, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_PANEL, foreground=FG_SUBTEXT, font=FONT_SUBTITLE, padding=(12, 6))
    style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#ffffff")])

    # Estilos customizados para Botões TTK
    style.configure("Action.TButton", background=SUCCESS, foreground="#ffffff", font=FONT_SUBTITLE, padding=(12, 6), borderwidth=0)
    style.map("Action.TButton", background=[("active", SUCCESS_HOVER)])

    style.configure("Primary.TButton", background=ACCENT, foreground="#ffffff", font=FONT_SUBTITLE, padding=(10, 5), borderwidth=0)
    style.map("Primary.TButton", background=[("active", ACCENT_HOVER)])

    style.configure("Danger.TButton", background=DANGER, foreground="#ffffff", font=FONT_SUBTITLE, padding=(10, 5), borderwidth=0)
    style.map("Danger.TButton", background=[("active", DANGER_HOVER)])

    style.configure("Secondary.TButton", background=BG_INPUT, foreground=FG_TEXT, font=FONT_NORMAL, padding=(8, 4), borderwidth=0)
    style.map("Secondary.TButton", background=[("active", BORDER_COLOR)], foreground=[("active", CYAN_GLOW)])
