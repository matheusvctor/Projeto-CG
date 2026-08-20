import tkinter as tk
from tkinter import ttk

COR_FUNDO = "#090d16"          # Obsidian escuro profundo
COR_SIDEBAR = "#0f172a"        # Sidebar escura elegante
COR_PAINEL = "#131d31"         # Slate/Navy escuro para cartões
COR_PAINEL_ALT = "#1e2c47"     # Superfície de controles e entradas
COR_DESTAQUE = "#06b6d4"       # Cyan elétrico vibrante
COR_DESTAQUE_HOVER = "#0891b2" # Cyan escuro no hover
COR_DESTAQUE_SUAVE = "#38bdf8" # Sky blue para realces
COR_ACCENT_ALT = "#10b981"     # Emerald moderno para ações secundárias
COR_INFO = "#38bdf8"           # Cyan suave
COR_TEXTO = "#f1f5f9"          # Branco suave de alto contraste
COR_TEXTO_MUTED = "#94a3b8"    # Texto secundário
COR_BORDA = "#1e2c47"          # Linhas de separação e bordas
COR_BORDA_FOCO = "#06b6d4"     # Borda ativa
COR_SUCESSO = "#10b981"        # Emerald
COR_AVISO = "#f59e0b"          # Amber
COR_ERRO = "#f43f5e"           # Rose

# Botões e Ações
PRIMARY = "#0284c7"
PRIMARY_HOVER = "#0369a1"
SUCCESS = "#10b981"
SUCCESS_HOVER = "#059669"
DANGER = "#ef4444"
DANGER_HOVER = "#dc2626"
WARNING = "#f59e0b"
WARNING_HOVER = "#d97706"
SECONDARY = "#334155"
SECONDARY_HOVER = "#475569"
ACCENT = "#06b6d4"
ACCENT_HOVER = "#0891b2"

FONTE_TITULO = ("Segoe UI", 15, "bold")
FONTE_SUBTITULO = ("Segoe UI", 10, "bold")
FONTE_CORPO = ("Segoe UI", 9)
FONTE_PEQUENA = ("Segoe UI", 8)
FONTE_CODE = ("Consolas", 9)


import os
from pathlib import Path
import subprocess
import webbrowser


def abrir_na_ide(caminho_relativo: str | Path, linha: int = 1) -> None:
    """Abre o arquivo fonte na IDE (VS Code / Cursor / Antigravity) na linha exata."""
    # Resolve caminho absoluto a partir do pacote ou da raiz do repositorio
    raiz_projeto = Path(__file__).resolve().parent.parent.parent
    caminho_abs = (raiz_projeto / caminho_relativo).resolve()
    if not caminho_abs.exists():
        caminho_abs = Path(caminho_relativo).resolve()
        
    caminho_str = str(caminho_abs).replace("\\", "/")

    # 1. Tenta abrir via CLI do VS Code com foco na linha exata (-g goto)
    try:
        subprocess.Popen(f'code -g "{caminho_str}:{linha}"', shell=True)
        return
    except Exception:
        pass

    # 2. Tenta via Protocolo URI vscode://
    try:
        if webbrowser.open(f"vscode://file/{caminho_str}:{linha}"):
            return
    except Exception:
        pass

    # 3. Fallback nativo do Windows
    try:
        os.startfile(caminho_str)
    except Exception:
        pass


def make_btn_insp(parent, callback_info):
    """Cria um botão compacto e elegante 'Inspecionar Código'."""
    def _acao():
        info = callback_info() if callable(callback_info) else callback_info
        if isinstance(info, tuple) and len(info) >= 2:
            arquivo, linha = info[0], info[1]
            abrir_na_ide(arquivo, linha)
        elif isinstance(info, str):
            abrir_na_ide(info, 1)

    return make_btn(
        parent,
        text="🔍 Inspecionar Código",
        command=_acao,
        btn_type="secondary",
        padx=8,
        pady=4,
    )


def make_btn(parent, text="", command=None, btn_type="primary", font=None, padx=12, pady=5, textvariable=None, width=None, **kwargs):
    """Cria um botão estilizado de acordo com o design escuro moderno com feedback de hover."""
    styles = {
        "primary": (PRIMARY, PRIMARY_HOVER, "#ffffff"),
        "success": (SUCCESS, SUCCESS_HOVER, "#ffffff"),
        "action": (SUCCESS, SUCCESS_HOVER, "#ffffff"),
        "danger": (DANGER, DANGER_HOVER, "#ffffff"),
        "warning": (WARNING, WARNING_HOVER, "#ffffff"),
        "secondary": (SECONDARY, SECONDARY_HOVER, "#f8fafc"),
        "accent": (ACCENT, ACCENT_HOVER, "#ffffff"),
    }
    bg_col, hov_col, fg_col = styles.get(btn_type, styles["primary"])
    btn_font = font if font is not None else ("Segoe UI", 9, "bold")

    btn_args = {
        "bg": bg_col,
        "fg": fg_col,
        "activebackground": hov_col,
        "activeforeground": fg_col,
        "font": btn_font,
        "relief": "flat",
        "cursor": "hand2",
        "padx": padx,
        "pady": pady,
        "command": command,
        **kwargs
    }
    if textvariable is not None:
        btn_args["textvariable"] = textvariable
    elif text:
        btn_args["text"] = text

    if width is not None:
        btn_args["width"] = width

    btn = tk.Button(parent, **btn_args)

    def _on_enter(e):
        try:
            if btn["state"] != tk.DISABLED:
                btn["bg"] = hov_col
        except Exception:
            pass

    def _on_leave(e):
        try:
            if btn["state"] != tk.DISABLED:
                btn["bg"] = bg_col
        except Exception:
            pass

    btn.bind("<Enter>", _on_enter, add="+")
    btn.bind("<Leave>", _on_leave, add="+")
    return btn


def configure_ttk_styles(root=None):
    """Configura o tema TTK escuro consistente com o projeto."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(".", background=COR_PAINEL, foreground=COR_TEXTO, font=FONTE_CORPO)
    style.configure("TFrame", background=COR_PAINEL)
    style.configure("Root.TFrame", background=COR_FUNDO)
    style.configure("TLabelframe", background=COR_PAINEL, foreground=COR_TEXTO, bordercolor=COR_BORDA)
    style.configure("TLabelframe.Label", background=COR_PAINEL, foreground=COR_INFO, font=FONTE_SUBTITULO)
    style.configure("Card.TLabelframe", background=COR_PAINEL, foreground=COR_TEXTO, bordercolor=COR_BORDA)
    style.configure("Card.TLabelframe.Label", background=COR_PAINEL, foreground=COR_INFO, font=FONTE_SUBTITULO)
    style.configure("TLabel", background=COR_PAINEL, foreground=COR_TEXTO, font=FONTE_CORPO)
    style.configure("Texto.TLabel", background=COR_FUNDO, foreground=COR_TEXTO, font=FONTE_CORPO)
    style.configure("Status.TLabel", background=COR_FUNDO, foreground=COR_TEXTO_MUTED, font=FONTE_PEQUENA)
    style.configure("TEntry", fieldbackground=COR_PAINEL_ALT, foreground=COR_TEXTO, insertcolor="#ffffff")
    style.configure("TSpinbox", fieldbackground=COR_PAINEL_ALT, foreground=COR_TEXTO, insertcolor="#ffffff")
    style.configure(
        "TCombobox",
        background=COR_PAINEL_ALT,
        fieldbackground=COR_PAINEL_ALT,
        foreground=COR_TEXTO,
        selectbackground=COR_DESTAQUE,
        selectforeground="#000000",
        arrowcolor=COR_DESTAQUE,
        bordercolor=COR_BORDA,
        darkcolor=COR_PAINEL_ALT,
        lightcolor=COR_PAINEL_ALT,
        relief="flat",
        padding=4,
    )
    style.map(
        "TCombobox",
        fieldbackground=[
            ("readonly", COR_PAINEL_ALT),
            ("active", COR_PAINEL_ALT),
            ("focus", COR_PAINEL_ALT),
            ("disabled", COR_PAINEL),
            ("!disabled", COR_PAINEL_ALT),
        ],
        background=[
            ("readonly", COR_PAINEL_ALT),
            ("active", COR_PAINEL_ALT),
            ("focus", COR_PAINEL_ALT),
            ("disabled", COR_PAINEL),
            ("!disabled", COR_PAINEL_ALT),
        ],
        foreground=[
            ("readonly", COR_TEXTO),
            ("active", COR_TEXTO),
            ("focus", COR_TEXTO),
            ("disabled", COR_TEXTO_MUTED),
            ("!disabled", COR_TEXTO),
        ],
        arrowcolor=[
            ("readonly", COR_DESTAQUE),
            ("active", "#ffffff"),
            ("disabled", COR_TEXTO_MUTED),
            ("!disabled", COR_DESTAQUE),
        ],
    )

    if root is not None:
        try:
            root.option_add("*TCombobox*Listbox.background", COR_PAINEL)
            root.option_add("*TCombobox*Listbox.foreground", COR_TEXTO)
            root.option_add("*TCombobox*Listbox.selectBackground", COR_DESTAQUE)
            root.option_add("*TCombobox*Listbox.selectForeground", "#000000")
            root.option_add("*TCombobox*Listbox.font", FONTE_CORPO)
        except Exception:
            pass

    style.configure("TNotebook", background=COR_FUNDO, borderwidth=0)
    style.configure("TNotebook.Tab", background=COR_PAINEL_ALT, foreground=COR_TEXTO_MUTED, padding=[12, 5], font=FONTE_SUBTITULO)
    style.map("TNotebook.Tab",
        background=[("selected", COR_PAINEL)],
        foreground=[("selected", COR_DESTAQUE)]
    )

