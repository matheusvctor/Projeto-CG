import tkinter as tk
from tkinter import ttk
import subprocess
import os
import theme

class MainMenu:
    def __init__(self, root):
        """Configura a janela principal que serve como hub das quatro questões."""
        self.root = root
        self.root.title("Motor de Computação Gráfica - UEPB")
        self.root.geometry("800x610")
        self.root.configure(bg=theme.BG_APP)
        self.root.eval('tk::PlaceWindow . center')

        self.build_ui()

    def build_ui(self):
        """Monta os botões e associa cada opção ao script responsável pelo módulo."""
        header = tk.Frame(self.root, bg=theme.BG_PANEL, height=100)
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(header, text="COMPUTAÇÃO GRÁFICA", font=("Segoe UI", 24, "bold"), 
                 bg=theme.BG_PANEL, fg=theme.ACCENT).pack(pady=(20, 5))
        tk.Label(header, text="Projeto 1", font=theme.FONT_TITLE, 
                 bg=theme.BG_PANEL, fg=theme.FG_TEXT).pack(pady=(0, 20))

        container = tk.Frame(self.root, bg=theme.BG_APP)
        container.pack(expand=True)

        botoes = [
            ("Formas Simples e Transformações 2D", "mod_primitivas/Questao1", "run_menu.py"),
            ("Recorte de Janela (Cohen-Sutherland)", "mod_recortes/Questao2", "apps/cohen_sutherland_ui.py"),
            ("Recorte de Polígonos (Sutherland-Hodgman)", "mod_recortes/Questao2", "apps/sutherland_hodgman_ui.py"),
            ("Transformações 3D", "mod_3d/Questao3", "Questao3..py"),
            ("Operações com Imagens", "mod_imagens/Questao4", "transformacoes.py")
        ]

        for texto, pasta, script in botoes:
            btn = tk.Button(container, text=texto, font=theme.FONT_TITLE, bg=theme.ACCENT, fg="white",
                            activebackground=theme.ACCENT_HOVER, activeforeground="white",
                            relief="flat", cursor="hand2", width=45, pady=10,
                            command=lambda p=pasta, s=script: self.abrir_modulo(p, s))
            btn.pack(pady=10)

    def abrir_modulo(self, pasta_base, script):
        """Abre o módulo escolhido em outro processo Python, preservando o PYTHONPATH local."""
        diretorio_trabalho = os.path.join(os.path.dirname(__file__), pasta_base)
        caminho_script = os.path.join(diretorio_trabalho, script)
        
        env = os.environ.copy()
        env["PYTHONPATH"] = diretorio_trabalho + os.pathsep + env.get("PYTHONPATH", "")
        
        try:
            subprocess.Popen(["python", caminho_script], cwd=diretorio_trabalho, env=env)
        except Exception as e:
            print(f"Erro ao abrir módulo: {e}")
            subprocess.Popen(["python3", caminho_script], cwd=diretorio_trabalho, env=env)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainMenu(root)
    root.mainloop()
