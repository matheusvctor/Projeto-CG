#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk


def open_cohen_sutherland(root):
    """Abre a interface de recorte de retas por Cohen-Sutherland."""
    from apps.cohen_sutherland_ui import AppCohenSutherland

    win = tk.Toplevel(root)
    win.title("Questao 2 - Cohen-Sutherland")
    AppCohenSutherland(win, on_back=win.destroy)


def open_sutherland_hodgman(root):
    """Abre a interface de recorte de polígonos por Sutherland-Hodgman."""
    from apps.sutherland_hodgman_ui import AppSutherlandHodgman

    win = tk.Toplevel(root)
    win.title("Questao 2 - Sutherland-Hodgman")
    _center(win, 1320, 760)
    win.minsize(1100, 680)
    AppSutherlandHodgman(win, on_back=win.destroy)


def _center(win, w=900, h=280):
    """Centraliza a janela de seleção da Questão 2 na tela."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def main():
    """Mostra o menu da Questão 2 para escolher entre os dois algoritmos de recorte."""
    root = tk.Tk()
    root.title("Projeto 1 - Questao 2")
    _center(root, 900, 280)
    root.minsize(700, 220)

    frm = ttk.Frame(root, padding=20)
    frm.pack(fill=tk.BOTH, expand=True)

    ttk.Label(
        frm,
        text="Questao 2 - Recorte de Janela",
        font=("Segoe UI", 14, "bold"),
    ).pack(pady=(0, 12))
    ttk.Button(
        frm,
        text="Cohen-Sutherland",
        command=lambda: open_cohen_sutherland(root),
    ).pack(fill=tk.X, ipady=12, pady=6)
    ttk.Button(
        frm,
        text="Sutherland-Hodgman",
        command=lambda: open_sutherland_hodgman(root),
    ).pack(fill=tk.X, ipady=12, pady=6)
    ttk.Button(frm, text="Sair", command=root.destroy).pack(fill=tk.X, ipady=10, pady=(18, 0))

    root.mainloop()


if __name__ == "__main__":
    main()
