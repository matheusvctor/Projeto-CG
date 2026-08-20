#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk


import os
import sys

_dir_modulo = os.path.abspath(os.path.dirname(__file__))
_dir_raiz = os.path.abspath(os.path.join(_dir_modulo, ".."))
if _dir_modulo not in sys.path:
    sys.path.insert(0, _dir_modulo)
if _dir_raiz not in sys.path:
    sys.path.insert(0, _dir_raiz)

import theme


def open_cohen_sutherland(root):
    """Abre a interface de recorte de retas por Cohen-Sutherland."""
    from apps.cohen_sutherland_ui import AppCohenSutherland

    win = tk.Toplevel(root)
    win.title("Questão 2 - Cohen-Sutherland")
    AppCohenSutherland(win, on_back=win.destroy)


def open_sutherland_hodgman(root):
    """Abre a interface de recorte de polígonos por Sutherland-Hodgman."""
    from apps.sutherland_hodgman_ui import AppSutherlandHodgman

    win = tk.Toplevel(root)
    win.title("Questão 2 - Sutherland-Hodgman")
    _center(win, 1320, 760)
    win.minsize(1100, 680)
    AppSutherlandHodgman(win, on_back=win.destroy)


def open_weiler_atherton(root):
    """Abre a interface de recorte de polígonos côncavos por Weiler-Atherton."""
    from apps.weiler_atherton_ui import AppWeilerAtherton

    win = tk.Toplevel(root)
    win.title("Questão 2 - Weiler-Atherton")
    _center(win, 1320, 760)
    win.minsize(1100, 680)
    AppWeilerAtherton(win, on_back=win.destroy)


def _center(win, w=900, h=360):
    """Centraliza a janela de seleção da Questão 2 na tela."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def main():
    """Mostra o menu da Questão 2 para escolher entre os três algoritmos de recorte."""
    root = tk.Tk()
    root.title("Projeto 1 - Questão 2 (Algoritmos de Recorte)")
    root.configure(bg=theme.BG_APP)
    theme.configure_ttk_styles(root)
    _center(root, 750, 380)
    root.minsize(650, 320)

    frm = tk.Frame(root, bg=theme.BG_PANEL, padx=30, pady=25)
    frm.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    tk.Label(
        frm,
        text="Questão 2 — Algoritmos de Recorte de Janela",
        font=theme.FONT_TITLE,
        bg=theme.BG_PANEL,
        fg=theme.CYAN_GLOW
    ).pack(pady=(0, 16))

    theme.make_btn(
        frm,
        "📏 1. Cohen-Sutherland (Recorte de Retas & Animação)",
        lambda: open_cohen_sutherland(root),
        "primary",
        padx=16,
        pady=8
    ).pack(fill=tk.X, pady=5)

    theme.make_btn(
        frm,
        "📐 2. Sutherland-Hodgman (Recorte de Polígonos Convexos)",
        lambda: open_sutherland_hodgman(root),
        "secondary",
        padx=16,
        pady=8
    ).pack(fill=tk.X, pady=5)

    theme.make_btn(
        frm,
        "✂ 3. Weiler-Atherton (Recorte de Polígonos Côncavos & Sub-regiões)",
        lambda: open_weiler_atherton(root),
        "action",
        padx=16,
        pady=8
    ).pack(fill=tk.X, pady=5)

    theme.make_btn(
        frm,
        "✕ Fechar",
        root.destroy,
        "danger",
        padx=16,
        pady=6
    ).pack(fill=tk.X, pady=(15, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
