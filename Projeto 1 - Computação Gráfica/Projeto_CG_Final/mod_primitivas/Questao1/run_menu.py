import tkinter as tk
from tkinter import ttk

def open_formas(root):
    """Abre a interface de desenho de primitivas e cônicas em uma nova janela."""
    from apps.formas_simples import AppFormas
    win = tk.Toplevel(root)
    win.title("Lab2 - Formas Simples")
    AppFormas(win, on_back=win.destroy)

def open_transf(root):
    """Abre a interface de transformações 2D mantendo o menu atual disponível."""
    from apps.transf2d_ui import AppTransf2D
    win = tk.Toplevel(root)
    win.title("Transformações 2D - Editor Gráfico")
    AppTransf2D(win, on_back=win.destroy)

def _center(win, w=900, h=220):
    """Centraliza a janela de menu para evitar que ela abra fora da área útil."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w)//2
    y = (sh - h)//2
    win.geometry(f"{w}x{h}+{x}+{y}")

def main():
    """Exibe o menu intermediário da Questão 1 com as duas subpartes do módulo."""
    root = tk.Tk()
    root.title("CG - Selecione um módulo")
    _center(root, 900, 220)
    root.minsize(700, 180)

    frm = ttk.Frame(root, padding=20)
    frm.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frm, text="Selecione um módulo", font=("Segoe UI", 14, "bold")).pack(pady=(0,12))
    ttk.Button(frm, text="Formas Simples e Cônicas", command=lambda: open_formas(root)).pack(fill=tk.X, ipady=12, pady=6)
    ttk.Button(frm, text="Transformações 2D (T, R, S, Sh)", command=lambda: open_transf(root)).pack(fill=tk.X, ipady=12, pady=6)
    ttk.Button(frm, text="Sair", command=root.destroy).pack(fill=tk.X, ipady=10, pady=(18,0))
    root.mainloop()

if __name__ == "__main__":
    main()
