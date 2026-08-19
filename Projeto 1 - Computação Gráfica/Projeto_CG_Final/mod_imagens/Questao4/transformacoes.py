#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mod_imagens/Questao4/transformacoes.py
Transformações Afins em Imagens PGM por Mapeamento Inverso (Questão 4).
"""

import math
import os
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Importa o tema global da raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import theme

from image_utils import apply_image_transformation, read_pgm, write_pgm_p5
from matrix_utils import (
    identity_3x3,
    multiply_3x3,
    reflect_both_2d,
    reflect_x_2d,
    reflect_y_2d,
    rotate_2d,
    scale_2d,
    shear_2d,
    translate_2d,
)


class AppTransformacoesPGM:
    def __init__(self, root, on_back=None):
        self.root = root
        self.on_back = on_back
        self.root.title("Transformações Afins em Imagens PGM — Questão 4")
        self.root.geometry("1180x760")
        self.root.minsize(1020, 680)
        self.root.configure(bg=theme.BG_APP)

        # Estado da Imagem
        self.img_original_pixels = None
        self.img_transformada_pixels = None
        self.cols = 0
        self.rows = 0
        self.nome_arquivo_atual = "Nenhum arquivo"
        self.trans_cols = 0
        self.trans_rows = 0

        # Caminhos dos arquivos temporários de exibição
        self.temp_dir = tempfile.gettempdir()
        self.temp_orig = os.path.join(self.temp_dir, "cg_q4_temp_orig.pgm")
        self.temp_trans = os.path.join(self.temp_dir, "cg_q4_temp_trans.pgm")

        # Variáveis de Interface
        self.operacao_var = tk.StringVar(value="Rotação")
        self.cor_fundo_var = tk.StringVar(value="Preto (0)")
        self.enquadramento_var = tk.StringVar(value="Bounding Box")
        self.inputs = {}

        self._criar_layout()
        self._carregar_imagem_padrao()

    def _criar_layout(self):
        # Corpo principal (ocupa toda a tela, sem navbar superior desnecessária)
        corpo = tk.Frame(self.root, bg=theme.BG_APP)
        corpo.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Barra Lateral de Controles (Esquerda)
        sidebar = tk.Frame(corpo, bg=theme.BG_PANEL, width=350, padx=14, pady=12)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        self._montar_controles(sidebar)

        # Painel Central de Imagens (Direita)
        painel_imagens = tk.Frame(corpo, bg=theme.BG_APP, padx=10, pady=5)
        painel_imagens.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._montar_paineis_imagem(painel_imagens)

    def _montar_controles(self, parent):
        # Topo da Sidebar: Botão Voltar e Título
        topo_sidebar = tk.Frame(parent, bg=theme.BG_PANEL)
        topo_sidebar.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            topo_sidebar,
            text="◀ Voltar",
            command=self._voltar,
            bg=theme.ACCENT,
            fg="#ffffff",
            activebackground=theme.ACCENT_HOVER,
            activeforeground="#ffffff",
            font=theme.FONT_SUBTITLE,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
        ).pack(side=tk.LEFT)

        tk.Label(
            topo_sidebar,
            text="Transformações PGM",
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL,
            fg=theme.CYAN_GLOW,
        ).pack(side=tk.LEFT, padx=10)

        # Linha divisória
        tk.Frame(parent, bg=theme.BORDER_COLOR, height=1).pack(fill=tk.X, pady=(0, 10))

        # Card 1: Arquivo e Amostras
        card_arquivo = tk.LabelFrame(
            parent,
            text="Arquivo de Imagem PGM",
            bg=theme.BG_PANEL,
            fg=theme.CYAN_GLOW,
            font=theme.FONT_SUBTITLE,
            padx=8,
            pady=8,
            relief="solid",
            bd=1,
        )
        card_arquivo.pack(fill=tk.X, pady=(0, 10))

        btn_carregar = tk.Button(
            card_arquivo,
            text="📁 Abrir Arquivo PGM (.pgm)",
            command=self.carregar_imagem,
            bg=theme.ACCENT,
            fg="#ffffff",
            activebackground=theme.ACCENT_HOVER,
            activeforeground="#ffffff",
            font=theme.FONT_NORMAL,
            relief="flat",
            cursor="hand2",
            pady=6,
        )
        btn_carregar.pack(fill=tk.X, pady=(0, 6))

        # Botões rápidos de amostra
        frame_amostras = tk.Frame(card_arquivo, bg=theme.BG_PANEL)
        frame_amostras.pack(fill=tk.X, pady=(0, 6))

        tk.Button(
            frame_amostras,
            text="Lena",
            command=lambda: self.carregar_amostra("lena.pgm"),
            bg=theme.BG_INPUT,
            fg=theme.FG_TEXT,
            relief="flat",
            cursor="hand2",
            font=theme.FONT_NORMAL,
            width=10,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))

        tk.Button(
            frame_amostras,
            text="Avião",
            command=lambda: self.carregar_amostra("Airplane.pgm"),
            bg=theme.BG_INPUT,
            fg=theme.FG_TEXT,
            relief="flat",
            cursor="hand2",
            font=theme.FONT_NORMAL,
            width=10,
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(3, 0))

        self.lbl_info_img = tk.Label(
            card_arquivo,
            text="Nenhuma imagem carregada",
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT,
            font=theme.FONT_CODE,
            anchor="w",
            justify="left",
        )
        self.lbl_info_img.pack(fill=tk.X)

        # Card 2: Seleção da Operação Afim
        card_op = tk.LabelFrame(
            parent,
            text="Transformação Afim",
            bg=theme.BG_PANEL,
            fg=theme.CYAN_GLOW,
            font=theme.FONT_SUBTITLE,
            padx=8,
            pady=8,
            relief="solid",
            bd=1,
        )
        card_op.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            card_op,
            text="Tipo de Operação:",
            bg=theme.BG_PANEL,
            fg=theme.FG_TEXT,
            font=theme.FONT_NORMAL,
        ).pack(anchor="w", pady=(0, 4))

        menu_op = tk.OptionMenu(
            card_op,
            self.operacao_var,
            "Escala",
            "Rotação",
            "Translação",
            "Cisalhamento",
            "Reflexão",
            command=self.atualizar_inputs,
        )
        menu_op.config(
            bg=theme.BG_INPUT,
            fg=theme.FG_TEXT,
            activebackground=theme.ACCENT,
            activeforeground="#ffffff",
            font=theme.FONT_NORMAL,
            relief="flat",
            highlightthickness=0,
        )
        menu_op["menu"].config(
            bg=theme.BG_PANEL,
            fg=theme.FG_TEXT,
            font=theme.FONT_NORMAL,
            activebackground=theme.ACCENT,
            activeforeground="#ffffff",
        )
        menu_op.pack(fill=tk.X, pady=(0, 8))

        # Frame dinâmico para os campos de parâmetros
        self.frame_inputs = tk.Frame(card_op, bg=theme.BG_PANEL)
        self.frame_inputs.pack(fill=tk.X, pady=(0, 6))

        # Enquadramento (Quadro Fixo vs Bounding Box)
        f_enq = tk.Frame(card_op, bg=theme.BG_PANEL)
        f_enq.pack(fill=tk.X, pady=(4, 2))
        tk.Label(
            f_enq,
            text="Enquadramento:",
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT,
            font=theme.FONT_NORMAL,
        ).pack(side=tk.LEFT)
        menu_enq = tk.OptionMenu(f_enq, self.enquadramento_var, "Quadro Fixo", "Bounding Box")
        menu_enq.config(
            bg=theme.BG_INPUT,
            fg=theme.FG_TEXT,
            relief="flat",
            highlightthickness=0,
            font=theme.FONT_NORMAL,
        )
        menu_enq.pack(side=tk.RIGHT)

        # Fundo do Bounding Box
        f_fundo = tk.Frame(card_op, bg=theme.BG_PANEL)
        f_fundo.pack(fill=tk.X, pady=(2, 0))
        tk.Label(
            f_fundo,
            text="Cor de Fundo:",
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT,
            font=theme.FONT_NORMAL,
        ).pack(side=tk.LEFT)
        menu_fundo = tk.OptionMenu(f_fundo, self.cor_fundo_var, "Preto (0)", "Branco (255)")
        menu_fundo.config(
            bg=theme.BG_INPUT,
            fg=theme.FG_TEXT,
            relief="flat",
            highlightthickness=0,
            font=theme.FONT_NORMAL,
        )
        menu_fundo.pack(side=tk.RIGHT)

        # Card 3: Botões de Ação
        card_acoes = tk.Frame(parent, bg=theme.BG_PANEL)
        card_acoes.pack(fill=tk.X, pady=(0, 10))

        btn_aplicar = tk.Button(
            card_acoes,
            text="Aplicar Transformação ➔",
            command=self.aplicar,
            bg=theme.SUCCESS,
            fg="#ffffff",
            activebackground=theme.SUCCESS_HOVER,
            activeforeground="#ffffff",
            font=theme.FONT_TITLE,
            relief="flat",
            cursor="hand2",
            pady=8,
        )
        btn_aplicar.pack(fill=tk.X, pady=(0, 5))

        btn_reset = tk.Button(
            card_acoes,
            text="↺ Restaurar Imagem Original",
            command=self.resetar,
            bg=theme.DANGER,
            fg="#ffffff",
            activebackground=theme.DANGER_HOVER,
            activeforeground="#ffffff",
            font=theme.FONT_NORMAL,
            relief="flat",
            cursor="hand2",
            pady=4,
        )
        btn_reset.pack(fill=tk.X, pady=(0, 5))

        btn_ajuda = tk.Button(
            card_acoes,
            text="❓ Como Calculamos?",
            command=self.cmd_como_calculamos,
            bg=theme.ACCENT,
            fg="#ffffff",
            activebackground=theme.ACCENT_HOVER,
            activeforeground="#ffffff",
            font=theme.FONT_NORMAL,
            relief="flat",
            cursor="hand2",
            pady=4,
        )
        btn_ajuda.pack(fill=tk.X)

        # Card 4: Terminal de Log de Matrizes
        card_log = tk.LabelFrame(
            parent,
            text="Log & Matriz Homogênea 3x3",
            bg=theme.BG_PANEL,
            fg=theme.CYAN_GLOW,
            font=theme.FONT_SUBTITLE,
            padx=6,
            pady=6,
            relief="solid",
            bd=1,
        )
        card_log.pack(fill=tk.BOTH, expand=True)

        self.text_log = tk.Text(
            card_log,
            height=5,
            bg=theme.BG_CANVAS,
            fg=theme.CYAN_GLOW,
            insertbackground="#ffffff",
            font=theme.FONT_CODE,
            relief="flat",
            wrap="word",
        )
        self.text_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_log = ttk.Scrollbar(card_log, orient="vertical", command=self.text_log.yview)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_log.config(yscrollcommand=scroll_log.set)

        self.atualizar_inputs()


    def _montar_paineis_imagem(self, parent):
        # Grid com 2 colunas para exibição limpa
        parent.columnconfigure(0, weight=1, uniform="imgs")
        parent.columnconfigure(1, weight=1, uniform="imgs")
        parent.rowconfigure(0, weight=1)

        # ---------------- Painel 1: Imagem Original ----------------
        card_orig = tk.Frame(parent, bg=theme.BG_PANEL, relief="solid", bd=1, padx=10, pady=10)
        card_orig.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)

        header_orig = tk.Frame(card_orig, bg=theme.BG_PANEL)
        header_orig.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            header_orig,
            text="🖼️ Imagem Original",
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL,
            fg=theme.CYAN_GLOW,
        ).pack(side=tk.LEFT)

        self.lbl_dim_orig = tk.Label(
            header_orig,
            text="[— x —]",
            font=theme.FONT_CODE,
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT,
        )
        self.lbl_dim_orig.pack(side=tk.RIGHT)

        self.container_canvas_orig = tk.Frame(card_orig, bg=theme.BG_CANVAS)
        self.container_canvas_orig.pack(fill=tk.BOTH, expand=True)

        self.painel_original = tk.Label(
            self.container_canvas_orig,
            text="Nenhuma imagem carregada\n\nAbra um arquivo .pgm para começar",
            bg=theme.BG_CANVAS,
            fg=theme.FG_MUTED,
            font=theme.FONT_NORMAL,
        )
        self.painel_original.pack(fill=tk.BOTH, expand=True)

        # ---------------- Painel 2: Imagem Transformada ----------------
        card_trans = tk.Frame(parent, bg=theme.BG_PANEL, relief="solid", bd=1, padx=10, pady=10)
        card_trans.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)

        header_trans = tk.Frame(card_trans, bg=theme.BG_PANEL)
        header_trans.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            header_trans,
            text="✨ Imagem Transformada",
            font=theme.FONT_TITLE,
            bg=theme.BG_PANEL,
            fg=theme.SUCCESS,
        ).pack(side=tk.LEFT)

        self.lbl_dim_trans = tk.Label(
            header_trans,
            text="[— x —]",
            font=theme.FONT_CODE,
            bg=theme.BG_PANEL,
            fg=theme.FG_SUBTEXT,
        )
        self.lbl_dim_trans.pack(side=tk.RIGHT)

        self.container_canvas_trans = tk.Frame(card_trans, bg=theme.BG_CANVAS)
        self.container_canvas_trans.pack(fill=tk.BOTH, expand=True)

        self.painel_transformada = tk.Label(
            self.container_canvas_trans,
            text="Aguardando aplicação de algoritmo...",
            bg=theme.BG_CANVAS,
            fg=theme.FG_MUTED,
            font=theme.FONT_NORMAL,
        )
        self.painel_transformada.pack(fill=tk.BOTH, expand=True)

    def _voltar(self):
        if callable(self.on_back):
            self.on_back()
        else:
            self.root.destroy()

    def log(self, mensagem):
        self.text_log.config(state=tk.NORMAL)
        self.text_log.insert(tk.END, mensagem + "\n")
        self.text_log.see(tk.END)
        self.text_log.config(state=tk.DISABLED)

    def _carregar_imagem_padrao(self):
        # Tenta carregar 'lena.pgm' ou 'Airplane.pgm' da própria pasta
        diretorio_atual = os.path.dirname(__file__)
        candidatos = [
            os.path.join(diretorio_atual, "lena.pgm"),
            os.path.join(diretorio_atual, "Airplane.pgm"),
        ]
        for c in candidatos:
            if os.path.exists(c):
                self._processar_leitura(c)
                return

    def carregar_amostra(self, nome_arquivo):
        caminho = os.path.join(os.path.dirname(__file__), nome_arquivo)
        if os.path.exists(caminho):
            self._processar_leitura(caminho)
        else:
            messagebox.showwarning("Aviso", f"Arquivo de amostra '{nome_arquivo}' não encontrado.")

    def carregar_imagem(self):
        caminho = filedialog.askopenfilename(
            filetypes=[
                ("Imagens NetPBM PGM", "*.pgm"),
                ("Todos os Arquivos", "*.*"),
            ]
        )
        if caminho:
            self._processar_leitura(caminho)

    def _processar_leitura(self, caminho):
        try:
            w, h, maxv, pix = read_pgm(caminho)
            self.cols, self.rows = w, h
            self.img_original_pixels = pix
            self.img_transformada_pixels = pix.copy()
            self.trans_cols, self.trans_rows = w, h
            self.nome_arquivo_atual = os.path.basename(caminho)

            self.lbl_info_img.config(
                text=f"Arquivo: {self.nome_arquivo_atual}\nDimensões: {w} × {h} px ({len(pix)} pixels)"
            )
            self.lbl_dim_orig.config(text=f"[{w} × {h}]")
            self.lbl_dim_trans.config(text=f"[{w} × {h}]")

            self.log(f"➔ Imagem carregada: {self.nome_arquivo_atual} ({w}x{h})")
            self.atualizar_telas()
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Falha ao ler arquivo PGM:\n{e}")

    def mostrar(self, pixels, w, h, painel, temp_filename):
        if pixels is None or painel is None:
            return
        try:
            write_pgm_p5(temp_filename, w, h, pixels)
            img_tk = tk.PhotoImage(file=temp_filename)
            painel.config(image=img_tk, text="")
            painel.image = img_tk
        except Exception as e:
            self.log(f"Erro ao renderizar imagem: {e}")

    def atualizar_telas(self):
        self.mostrar(self.img_original_pixels, self.cols, self.rows, self.painel_original, self.temp_orig)
        self.mostrar(
            self.img_transformada_pixels,
            self.trans_cols,
            self.trans_rows,
            self.painel_transformada,
            self.temp_trans,
        )

    def resetar(self):
        if self.img_original_pixels is not None:
            self.img_transformada_pixels = self.img_original_pixels.copy()
            self.trans_cols, self.trans_rows = self.cols, self.rows
            self.lbl_dim_trans.config(text=f"[{self.cols} × {self.rows}]")
            self.log("↺ Imagem transformada resetada para o estado original.")
            self.atualizar_telas()

    def atualizar_inputs(self, event=None):
        if self.frame_inputs is None:
            return
        self.inputs.clear()
        for widget in self.frame_inputs.winfo_children():
            widget.destroy()

        op = self.operacao_var.get()
        if op == "Escala":
            self.enquadramento_var.set("Bounding Box")
            self.criar_input("Fator SX:", "1.5")
            self.criar_input("Fator SY:", "1.5")
        elif op == "Rotação":
            self.enquadramento_var.set("Bounding Box")
            self.criar_input("Ângulo (° anti-horário):", "45")
        elif op == "Translação":
            # Para translação, o padrão é Quadro Fixo para que o deslocamento dentro da imagem seja visível
            self.enquadramento_var.set("Quadro Fixo")
            self.criar_input("Deslocamento TX (px):", "30")
            self.criar_input("Deslocamento TY (px):", "20")
        elif op == "Cisalhamento":
            self.enquadramento_var.set("Bounding Box")
            self.criar_input("Fator SHX:", "0.3")
            self.criar_input("Fator SHY:", "0.0")
        elif op == "Reflexão":
            self.enquadramento_var.set("Bounding Box")
            self.criar_input("Eixo (X, Y ou Ambos):", "Y")

    def criar_input(self, nome, default=""):
        f = tk.Frame(self.frame_inputs, bg=theme.BG_PANEL)
        f.pack(fill=tk.X, pady=3)
        tk.Label(
            f,
            text=nome,
            bg=theme.BG_PANEL,
            fg=theme.FG_TEXT,
            font=theme.FONT_NORMAL,
            anchor="w",
        ).pack(side=tk.LEFT)
        e = tk.Entry(
            f,
            width=8,
            bg=theme.BG_INPUT,
            fg=theme.FG_TEXT,
            insertbackground="#ffffff",
            relief="flat",
            font=theme.FONT_NORMAL,
        )
        e.insert(0, default)
        e.pack(side=tk.RIGHT)
        self.inputs[nome] = e

    def _formatar_matriz_str(self, M):
        linhas = []
        for r in M:
            linhas.append("| " + "  ".join(f"{v:7.3f}" for v in r) + " |")
        return "\n".join(linhas)

    def aplicar(self):
        if self.img_original_pixels is None:
            messagebox.showwarning("Aviso", "Por favor, carregue uma imagem PGM primeiro.")
            return

        op = self.operacao_var.get()
        bg_val = 0 if "Preto" in self.cor_fundo_var.get() else 255
        expand = (self.enquadramento_var.get() == "Bounding Box")

        try:
            if op == "Escala":
                sx = float(self.inputs["Fator SX:"].get())
                sy = float(self.inputs["Fator SY:"].get())
                if sx <= 0 or sy <= 0:
                    messagebox.showerror("Erro", "Os fatores de escala devem ser maiores que zero.")
                    return
                M = scale_2d(sx, sy)
                desc = f"Escala (SX={sx}, SY={sy})"

            elif op == "Rotação":
                ang = float(self.inputs["Ângulo (° anti-horário):"].get())
                M = rotate_2d(ang)
                desc = f"Rotação ({ang}° anti-horário)"

            elif op == "Translação":
                tx = float(self.inputs["Deslocamento TX (px):"].get())
                ty = float(self.inputs["Deslocamento TY (px):"].get())
                M = translate_2d(tx, ty)
                desc = f"Translação (TX={tx}, TY={ty})"

            elif op == "Cisalhamento":
                shx = float(self.inputs["Fator SHX:"].get())
                shy = float(self.inputs["Fator SHY:"].get())
                M = shear_2d(shx, shy)
                desc = f"Cisalhamento (SHX={shx}, SHY={shy})"

            elif op == "Reflexão":
                eixo_input = self.inputs["Eixo (X, Y ou Ambos):"].get().strip().upper()
                if "AMBOS" in eixo_input or "ORIGEM" in eixo_input:
                    M = reflect_both_2d()
                    desc = "Reflexão (Ambos os Eixos)"
                elif "X" in eixo_input:
                    M = reflect_x_2d()
                    desc = "Reflexão Vertical (Eixo X)"
                elif "Y" in eixo_input:
                    M = reflect_y_2d()
                    desc = "Reflexão Horizontal (Eixo Y)"
                else:
                    messagebox.showerror("Eixo Inválido", "Informe 'X', 'Y' ou 'Ambos' para o eixo de reflexão.")
                    return

            # Executa a transformação por Mapeamento Inverso
            new_pixels, new_w, new_h = apply_image_transformation(
                self.img_original_pixels, self.cols, self.rows, M, bg_color=bg_val, expand_canvas=expand
            )

            self.img_transformada_pixels = new_pixels
            self.trans_cols = new_w
            self.trans_rows = new_h

            modo_enq = "Bounding Box Expandido" if expand else "Quadro Fixo (W × H)"
            self.lbl_dim_trans.config(text=f"[{new_w} × {new_h}]")
            self.log(f"★ {desc} [{modo_enq}]\nDimensão resultante: {new_w} × {new_h} px\nMatriz Afim Aplicada:\n{self._formatar_matriz_str(M)}\n" + "-" * 32)
            self.atualizar_telas()

        except Exception as e:
            messagebox.showerror("Erro de Execução", f"Falha ao aplicar {op}:\n{e}")
            self.log(f"ERRO ao aplicar {op}: {e}")


    def cmd_como_calculamos(self):
        janela = tk.Toplevel(self.root)
        janela.title("Como Calculamos — Transformações Afins em Imagens PGM")
        janela.geometry("640x480")
        janela.configure(bg=theme.BG_PANEL)

        topo = tk.Frame(janela, bg=theme.BG_HEADER, padx=15, pady=10)
        topo.pack(fill=tk.X)
        tk.Label(
            topo,
            text="Fundamentação Matemática (Questão 4)",
            font=theme.FONT_TITLE,
            bg=theme.BG_HEADER,
            fg=theme.CYAN_GLOW,
        ).pack(anchor="w")

        conteudo = tk.Frame(janela, bg=theme.BG_PANEL, padx=20, pady=15)
        conteudo.pack(fill=tk.BOTH, expand=True)

        texto = """1. Matriz de Transformação Homogênea (3x3):
As coordenadas [x, y, 1] de cada ponto são transformadas através de 
multiplicação matricial:
- Rotação: [[cos(θ), -sin(θ), 0], [sin(θ), cos(θ), 0], [0, 0, 1]]
- Escala: [[sx, 0, 0], [0, sy, 0], [0, 0, 1]]
- Cisalhamento: [[1, shx, 0], [shy, 1, 0], [0, 0, 1]]
- Translação: [[1, 0, tx], [0, 1, ty], [0, 0, 1]]

2. Bounding Box Dinâmico (Sem corte da imagem):
Multiplicamos os 4 vértices da imagem original (0,0), (W-1,0), (0,H-1) e (W-1,H-1) 
pela matriz M para obter a caixa envolvente com dimensões exatas:
  nova_largura = max_x - min_x + 1
  nova_altura  = max_y - min_y + 1

3. Mapeamento Inverso (Prevenção de Buracos / Aliasing):
Para cada pixel (nx, ny) da imagem de saída, calculamos:
  (wx, wy) = (nx + min_x, ny + min_y)
  (ox, oy) = M⁻¹ * [wx, wy, 1]
Se (ox, oy) estiver dentro dos limites [0, W) e [0, H), copiamos a intensidade de 
cinza original. Caso contrário, preenchemos com a cor de fundo."""

        lbl = tk.Label(
            conteudo,
            text=texto,
            justify="left",
            font=theme.FONT_NORMAL,
            bg=theme.BG_PANEL,
            fg=theme.FG_TEXT,
            wraplength=580,
        )
        lbl.pack(fill=tk.BOTH, expand=True)

        tk.Button(
            janela,
            text="Fechar",
            command=janela.destroy,
            bg=theme.ACCENT,
            fg="#ffffff",
            relief="flat",
            font=theme.FONT_NORMAL,
            pady=4,
        ).pack(pady=(0, 15))


def main():
    root = tk.Tk()
    app = AppTransformacoesPGM(root)
    root.mainloop()


if __name__ == "__main__":
    main()

