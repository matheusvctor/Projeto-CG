import tkinter as tk
from tkinter import ttk
import os
import sys

# Garante acesso ao theme.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import theme

def open_formas(root):
    """Abre a interface de desenho de primitivas e cônicas em uma nova janela."""
    from apps.formas_simples import AppFormas
    win = tk.Toplevel(root)
    win.title("Primitivas, Cônicas & Curvas de Bézier")
    win.configure(bg=theme.BG_APP)
    AppFormas(win, on_back=win.destroy)

def open_transf(root):
    """Abre a interface de transformações 2D mantendo o menu atual disponível."""
    from apps.transf2d_ui import AppTransf2D
    win = tk.Toplevel(root)
    win.title("Transformações Homogêneas 2D (T, R, S, Sh)")
    win.configure(bg=theme.BG_APP)
    AppTransf2D(win, on_back=win.destroy)

def _center(win, w=640, h=300):
    """Centraliza a janela de menu para evitar que ela abra fora da área útil."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w)//2
    y = (sh - h)//2
    win.geometry(f"{w}x{h}+{x}+{y}")

def main():
    """Exibe o menu intermediário da Questão 1 com visual moderno Dark Slate."""
    root = tk.Tk()
    root.title("Primitivas & Transformações 2D")
    root.configure(bg=theme.BG_APP)
    _center(root, 640, 300)
    root.minsize(580, 260)

    frm = tk.Frame(root, bg=theme.BG_APP, padx=30, pady=25)
    frm.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        frm,
        text="Selecione uma Ferramenta (Questão 1 & 5)",
        font=theme.FONT_TITLE,
        bg=theme.BG_APP,
        fg=theme.CYAN_GLOW
    ).pack(pady=(0, 15))

    btn_f = tk.Button(
        frm,
        text="📐  Formas Simples, Cônicas & Bézier (DDA, Bresenham, Círculos, Elipse)",
        font=theme.FONT_SUBTITLE,
        bg=theme.ACCENT,
        fg="#ffffff",
        activebackground=theme.ACCENT_HOVER,
        activeforeground="#ffffff",
        relief="flat",
        cursor="hand2",
        pady=10,
        command=lambda: open_formas(root)
    )
    btn_f.pack(fill=tk.X, pady=6)

    btn_t = tk.Button(
        frm,
        text="🔄  Transformações Homogêneas 2D (Translação, Rotação, Escala, Cisalhamento)",
        font=theme.FONT_SUBTITLE,
        bg=theme.BG_PANEL,
        fg=theme.FG_TEXT,
        activebackground=theme.BG_INPUT,
        activeforeground=theme.CYAN_GLOW,
        relief="flat",
        cursor="hand2",
        pady=10,
        command=lambda: open_transf(root)
    )
    btn_t.pack(fill=tk.X, pady=6)

    root.mainloop()

if __name__ == "__main__":
    main()
