"""
Interface da Questao 2 - recorte de poligonos com Sutherland-Hodgman.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

from core.cg_utils import QuadroDesenho, Viewport, normalizar_janela, sutherland_hodgman_clip_trace

Point = tuple[float, float]


class AppSutherlandHodgman:
    def __init__(self, root, on_back=None):
        """Interface para recortar polígonos e acompanhar cada etapa do algoritmo."""
        self.on_back = on_back
        self.zoom = tk.IntVar(value=8)
        self.vertex_x = tk.StringVar(value="0")
        self.vertex_y = tk.StringVar(value="0")
        self.vertices_text = tk.StringVar()
        self.xmin = tk.DoubleVar(value=-20)
        self.ymin = tk.DoubleVar(value=-20)
        self.xmax = tk.DoubleVar(value=25)
        self.ymax = tk.DoubleVar(value=20)
        self.show_vertex_markers_var = tk.BooleanVar(value=True)
        self.show_vertex_values_var = tk.BooleanVar(value=True)
        self.show_intersections_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(
            value="Defina a janela, informe os vertices e visualize o poligono original e o recortado."
        )

        self._last = None
        self._drawing_mode = False
        self.draw_button = None
        self._label_boxes: list[tuple[float, float, float, float]] = []
        self._label_font = tkfont.Font(root=root, family="Segoe UI", size=9, weight="bold")

        self._build_ui(root)
        self.carregar_exemplo()

    def _build_ui(self, root):
        """Monta todos os painéis de entrada, desenho, resumo e log da questão."""
        nav = ttk.Frame(root)
        nav.pack(fill=tk.X, padx=10, pady=(8, 2))
        ttk.Button(nav, text="<- Voltar", command=self._voltar).pack(side=tk.LEFT)
        ttk.Label(nav, text="Questao 2 - Sutherland-Hodgman", font=("Segoe UI", 12, "bold")).pack(side=tk.RIGHT)

        controls = ttk.Frame(root, padding=(10, 6, 10, 6))
        controls.pack(fill=tk.X)
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=0)
        controls.columnconfigure(2, weight=0)

        polygon_frame = ttk.LabelFrame(controls, text="Poligono")
        polygon_frame.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        polygon_frame.columnconfigure(5, weight=1)
        ttk.Label(polygon_frame, text="Vertices (x,y; x,y; ...):").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        ttk.Entry(polygon_frame, textvariable=self.vertices_text).grid(row=1, column=0, columnspan=6, sticky="ew", padx=8)

        ttk.Label(polygon_frame, text="X").grid(row=2, column=0, sticky="w", padx=(8, 2), pady=(8, 2))
        ttk.Entry(polygon_frame, textvariable=self.vertex_x, width=8).grid(row=3, column=0, sticky="w", padx=(8, 2), pady=(0, 8))
        ttk.Label(polygon_frame, text="Y").grid(row=2, column=1, sticky="w", padx=2, pady=(8, 2))
        ttk.Entry(polygon_frame, textvariable=self.vertex_y, width=8).grid(row=3, column=1, sticky="w", padx=2, pady=(0, 8))
        ttk.Button(polygon_frame, text="Adicionar ponto", command=self.add_polygon_point).grid(
            row=3, column=2, sticky="w", padx=(10, 6), pady=(0, 8)
        )
        ttk.Button(polygon_frame, text="Remover ultimo", command=self.remove_last_polygon_point).grid(
            row=3, column=3, sticky="w", padx=6, pady=(0, 8)
        )
        self.draw_button = ttk.Button(polygon_frame, text="Desenhar na tela", command=self.toggle_draw_mode)
        self.draw_button.grid(row=3, column=4, sticky="w", padx=6, pady=(0, 8))

        window_frame = ttk.LabelFrame(controls, text="Janela de recorte")
        window_frame.grid(row=0, column=1, sticky="nw", padx=(0, 12))
        self._window_field(window_frame, "X min", self.xmin, 0, 0)
        self._window_field(window_frame, "Y min", self.ymin, 0, 1)
        self._window_field(window_frame, "X max", self.xmax, 1, 0)
        self._window_field(window_frame, "Y max", self.ymax, 1, 1)

        options_frame = ttk.LabelFrame(controls, text="Exibicao")
        options_frame.grid(row=0, column=2, sticky="ne")
        ttk.Label(options_frame, text="zoom (px/unidade):").pack(anchor="w", padx=8, pady=(8, 2))
        zoom_box = ttk.Spinbox(options_frame, from_=1, to=40, textvariable=self.zoom, width=8, command=self._on_zoom_change)
        zoom_box.pack(anchor="w", padx=8)
        zoom_box.bind("<Return>", lambda e: self._on_zoom_change())
        zoom_box.bind("<FocusOut>", lambda e: self._on_zoom_change())
        ttk.Checkbutton(
            options_frame,
            text="Mostrar bolinhas dos vertices",
            variable=self.show_vertex_markers_var,
            command=self._redraw_if_possible,
        ).pack(anchor="w", padx=8, pady=(8, 0))
        ttk.Checkbutton(
            options_frame,
            text="Mostrar valores dos vertices",
            variable=self.show_vertex_values_var,
            command=self._redraw_if_possible,
        ).pack(anchor="w", padx=8, pady=(2, 0))
        ttk.Checkbutton(
            options_frame,
            text="Mostrar interseccoes",
            variable=self.show_intersections_var,
            command=self._redraw_if_possible,
        ).pack(anchor="w", padx=8, pady=(2, 0))
        ttk.Button(options_frame, text="Recortar", command=self.desenhar).pack(fill=tk.X, padx=8, pady=(10, 4))
        ttk.Button(options_frame, text="Enquadrar", command=self.enquadrar).pack(fill=tk.X, padx=8, pady=4)
        ttk.Button(options_frame, text="Exemplo", command=self.carregar_exemplo).pack(fill=tk.X, padx=8, pady=4)
        ttk.Button(options_frame, text="Limpar", command=self.limpar).pack(fill=tk.X, padx=8, pady=(4, 8))

        ttk.Label(root, textvariable=self.status_var, padding=(10, 2, 10, 8)).pack(anchor="w")

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=5)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        plot_frame = ttk.Frame(body)
        plot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        plot_frame.rowconfigure(0, weight=1)
        plot_frame.columnconfigure(0, weight=1)

        self.vp = Viewport(920, 720, escala=self.zoom.get())
        self.canvas = tk.Canvas(plot_frame, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.quadro = QuadroDesenho(self.canvas, self.vp, usar_grade=False)
        self.quadro.set_redraw_callback(self._redesenhar)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_left_release, add="+")
        self.canvas.bind("<Button-3>", self._on_canvas_right_click, add="+")
        plot_frame.bind("<Configure>", lambda e: self.quadro.resize(e.width, e.height))

        side = ttk.Frame(body)
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)
        side.rowconfigure(1, weight=1)

        summary_row = ttk.Frame(side)
        summary_row.grid(row=0, column=0, sticky="ew")
        summary_row.columnconfigure(0, weight=1)
        summary_row.columnconfigure(1, weight=1)
        summary_row.columnconfigure(2, weight=1)

        ttk.Label(summary_row, text="Vertices do poligono").grid(row=0, column=0, sticky="w")
        ttk.Label(summary_row, text="Poligono recortado").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Label(summary_row, text="Interseccoes").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.input_text = self._make_text(summary_row, row=1, column=0, height=6, width=18)
        self.output_text = self._make_text(summary_row, row=1, column=1, height=6, width=18, padx=(10, 0))
        self.intersection_text = self._make_text(summary_row, row=1, column=2, height=6, width=18, padx=(10, 0))

        notebook = ttk.Notebook(side)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        frame_steps = ttk.Frame(notebook)
        frame_help = ttk.Frame(notebook)
        notebook.add(frame_steps, text="Etapas")
        notebook.add(frame_help, text="Como calculamos")

        self.log = tk.Text(frame_steps, wrap="word", font=("Consolas", 9), height=10, width=52)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll = ttk.Scrollbar(frame_steps, orient="vertical", command=self.log.yview)
        log_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.log.configure(yscrollcommand=log_scroll.set)

        self.help = tk.Text(frame_help, wrap="word", font=("Segoe UI", 10), bg="#f7f7f7", height=10, width=52)
        self.help.pack(fill=tk.BOTH, expand=True)
        self._update_help()

    def _window_field(self, parent, label, variable, row, column):
        """Cria um campo simples para um dos quatro limites da janela de recorte."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, sticky="w", padx=8, pady=6)
        ttk.Label(frame, text=label).pack(anchor="w")
        ttk.Entry(frame, textvariable=variable, width=8).pack(anchor="w")

    def _make_text(self, parent, row, column, height, width=20, padx=(0, 0)):
        """Cria uma caixa de texto com barra de rolagem para resumos laterais."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, sticky="nsew", padx=padx)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        text = tk.Text(frame, wrap="word", font=("Consolas", 10), height=height, width=width)
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set, state="disabled")
        return text

    def _voltar(self):
        """Fecha a janela atual ou retorna ao menu quando houver callback."""
        if callable(self.on_back):
            self.on_back()
        else:
            self.canvas.winfo_toplevel().destroy()

    def _update_help(self):
        """Escreve um resumo curto do Sutherland-Hodgman para consulta rápida."""
        texto = (
            "Sutherland-Hodgman\n"
            "- O poligono e recortado contra as quatro bordas da janela.\n"
            "- Para cada borda, percorremos as arestas do poligono atual.\n"
            "- Se a aresta entra na regiao valida, adicionamos interseccao e vertice atual.\n"
            "- Se a aresta sai da regiao valida, adicionamos apenas a interseccao.\n"
            "- O poligono original aparece em vermelho claro e o recortado em azul.\n"
            "- Os vertices sao marcados por pontos e podem ser rotulados.\n"
            "- Use arraste no mouse para pan e a roda para zoom no desenho.\n"
            "- No modo de desenho, clique esquerdo adiciona vertices e clique direito encerra."
        )
        self.help.config(state="normal")
        self.help.delete("1.0", tk.END)
        self.help.insert(tk.END, texto)
        self.help.config(state="disabled")

    def _set_status(self, message: str):
        """Atualiza a barra de status incluindo o aviso do modo desenho quando necessário."""
        if self._drawing_mode:
            message = f"{message} | Modo desenho: clique esquerdo adiciona vertices; clique direito encerra."
        self.status_var.set(message)

    def _update_draw_button(self):
        """Sincroniza o texto do botão com o estado do modo desenho."""
        if self.draw_button is not None:
            self.draw_button.config(text="Parar desenho" if self._drawing_mode else "Desenhar na tela")

    def toggle_draw_mode(self, enabled=None):
        """Liga/desliga o modo de desenhar vértices no canvas com o mouse."""
        if enabled is None:
            enabled = not self._drawing_mode
        self._drawing_mode = bool(enabled)
        self.quadro.set_pan_enabled(not self._drawing_mode)
        self._update_draw_button()
        if self._drawing_mode:
            self._set_status("Modo desenho ativado.")
        else:
            self._set_status("Modo desenho desativado. Pan no botao esquerdo restaurado.")

    def _on_canvas_left_release(self, event):
        """No modo desenho, converte o clique em coordenada de mundo e adiciona vértice."""
        if not self._drawing_mode:
            return
        x, y = self.quadro.canvas_para_mundo(event.x, event.y)
        point = (round(x, 3), round(y, 3))
        self.vertex_x.set(self._format_number(point[0]))
        self.vertex_y.set(self._format_number(point[1]))
        self._append_point(point)

    def _on_canvas_right_click(self, _event):
        """Encerra o modo desenho com um clique direito."""
        if self._drawing_mode:
            self.toggle_draw_mode(False)

    def _on_zoom_change(self):
        """Atualiza a escala do canvas de visualização."""
        try:
            zoom = int(self.zoom.get())
        except Exception:
            return
        zoom = min(40, max(1, zoom))
        self.zoom.set(zoom)
        self.vp.set_escala(zoom)
        self.quadro.redraw()

    def _redraw_if_possible(self):
        """Redesenha apenas se já houver um trace calculado anteriormente."""
        if self._last:
            self.quadro.redraw()

    def _set_text_lines(self, widget, lines):
        """Substitui completamente o conteúdo de uma caixa de texto pelo conjunto de linhas."""
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        for line in lines:
            widget.insert(tk.END, line + "\n")
        widget.config(state="disabled")

    def _format_number(self, value: float) -> str:
        """Formata números removendo zeros desnecessários para melhorar a leitura."""
        text = f"{value:.3f}"
        return text.rstrip("0").rstrip(".") if "." in text else text

    def _format_point(self, point: Point) -> str:
        """Converte um ponto para a notação textual (x, y)."""
        return f"({self._format_number(point[0])}, {self._format_number(point[1])})"

    def _format_named_point(self, name: str, point: Point) -> str:
        """Adiciona um rótulo textual a um ponto formatado."""
        return f"{name}: {self._format_point(point)}"

    def _format_polygon_inline(self, polygon: list[Point]) -> str:
        """Representa um polígono em uma única linha, útil para logs de etapa."""
        if not polygon:
            return "[]"
        return "[" + ", ".join(self._format_point(point) for point in polygon) + "]"

    def _parse_vertices(self, allow_empty=False) -> list[Point]:
        """Lê a string de vértices digitada e converte para lista de tuplas numéricas."""
        raw = self.vertices_text.get().strip()
        if not raw:
            if allow_empty:
                return []
            raise ValueError("Informe ao menos um vertice.")

        vertices = []
        for part in raw.replace("\n", ";").split(";"):
            chunk = part.strip()
            if not chunk:
                continue
            normalized = chunk.replace("(", "").replace(")", "").replace(" ", "")
            coords = normalized.split(",")
            if len(coords) != 2:
                raise ValueError(f"Vertice invalido: {chunk}")
            vertices.append((float(coords[0]), float(coords[1])))
        return vertices

    def _set_vertices(self, vertices: list[Point]):
        """Serializa a lista de vértices de volta para o campo de texto principal."""
        self.vertices_text.set("; ".join(f"{self._format_number(x)},{self._format_number(y)}" for x, y in vertices))

    def _read_window(self):
        """Lê, valida e normaliza a janela de recorte digitada pelo usuário."""
        try:
            xmin = float(self.xmin.get())
            ymin = float(self.ymin.get())
            xmax = float(self.xmax.get())
            ymax = float(self.ymax.get())
        except ValueError as exc:
            raise ValueError("Os limites da janela devem ser numericos.") from exc

        xmin, ymin, xmax, ymax = normalizar_janela(xmin, ymin, xmax, ymax)
        if xmin == xmax or ymin == ymax:
            raise ValueError("A janela deve ter largura e altura positivas.")
        return xmin, ymin, xmax, ymax

    def _append_point(self, point: Point):
        """Adiciona um vértice ao polígono atual e redesenha imediatamente."""
        try:
            vertices = self._parse_vertices(allow_empty=True)
        except ValueError as exc:
            messagebox.showerror("Entrada invalida", str(exc))
            return

        vertices.append(point)
        self._set_vertices(vertices)
        self.desenhar()

    def add_polygon_point(self):
        """Adiciona manualmente um vértice usando os campos X/Y."""
        try:
            point = (float(self.vertex_x.get()), float(self.vertex_y.get()))
        except ValueError as exc:
            messagebox.showerror("Entrada invalida", str(exc))
            return

        self._append_point(point)

    def remove_last_polygon_point(self):
        """Remove o último vértice informado, útil para corrigir a entrada."""
        try:
            vertices = self._parse_vertices(allow_empty=True)
        except ValueError as exc:
            messagebox.showerror("Entrada invalida", str(exc))
            return

        if vertices:
            vertices.pop()
        self._set_vertices(vertices)
        self.desenhar()

    def clear_polygon(self):
        """Apaga apenas os vértices do polígono, mantendo a janela de recorte."""
        self.vertices_text.set("")
        self._reset_view()

    def _canvas_points(self, points: list[Point]) -> list[int]:
        """Converte uma lista de pontos do mundo para coordenadas do canvas Tk."""
        coords = []
        for x, y in points:
            sx, sy = self.quadro.mundo_para_canvas(x, y)
            coords.extend([sx, sy])
        return coords

    def _draw_polygon_shape(self, points: list[Point], outline: str, fill: str, width: int, stipple: str):
        """Desenha um segmento ou polígono preenchido conforme a quantidade de vértices."""
        if len(points) < 2:
            return
        coords = self._canvas_points(points)
        if len(points) >= 3:
            self.canvas.create_polygon(
                coords,
                outline=outline,
                fill=fill,
                width=width,
                stipple=stipple,
                tags="SCENE",
            )
        else:
            self.canvas.create_line(*coords, fill=outline, width=width, tags="SCENE")

    def _draw_window(self, xmin: float, ymin: float, xmax: float, ymax: float):
        """Renderiza o retângulo da janela de recorte na cena atual."""
        coords = self._canvas_points([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])
        self.canvas.create_polygon(coords, outline="#111111", fill="", width=2, tags="SCENE")

    def _text_bbox(self, x: float, y: float, anchor: str, width: int, height: int) -> tuple[float, float, float, float]:
        """Calcula a bounding box de um texto para evitar sobreposição de rótulos."""
        if anchor == "sw":
            return (x, y - height, x + width, y)
        if anchor == "se":
            return (x - width, y - height, x, y)
        if anchor == "nw":
            return (x, y, x + width, y + height)
        return (x - width, y, x, y + height)

    def _boxes_intersect(
        self,
        first: tuple[float, float, float, float],
        second: tuple[float, float, float, float],
        padding: int = 4,
    ) -> bool:
        """Testa se duas caixas de texto se sobrepõem com uma pequena margem."""
        return not (
            first[2] + padding < second[0]
            or second[2] + padding < first[0]
            or first[3] + padding < second[1]
            or second[3] + padding < first[1]
        )

    def _choose_label_position(self, sx: float, sy: float, radius: int, label: str) -> tuple[float, float, str]:
        """Escolhe a melhor posição de rótulo ao redor de um ponto sem poluir a cena."""
        width = self._label_font.measure(label)
        height = self._label_font.metrics("linespace")
        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)
        best_candidate = None
        best_penalty = None

        for distance in (radius + 8, radius + 18, radius + 30):
            candidates = [
                (sx + distance, sy - distance, "sw"),
                (sx - distance, sy - distance, "se"),
                (sx + distance, sy + distance, "nw"),
                (sx - distance, sy + distance, "ne"),
            ]
            for x, y, anchor in candidates:
                bbox = self._text_bbox(x, y, anchor, width, height)
                penalty = distance
                for existing in self._label_boxes:
                    if self._boxes_intersect(bbox, existing):
                        penalty += 10000

                overflow = 0
                if bbox[0] < 0:
                    overflow += -bbox[0]
                if bbox[1] < 0:
                    overflow += -bbox[1]
                if bbox[2] > canvas_w:
                    overflow += bbox[2] - canvas_w
                if bbox[3] > canvas_h:
                    overflow += bbox[3] - canvas_h
                penalty += overflow * 20

                if best_penalty is None or penalty < best_penalty:
                    best_penalty = penalty
                    best_candidate = (x, y, anchor, bbox)
                    if penalty < 10000:
                        break
            if best_penalty is not None and best_penalty < 10000:
                break

        if best_candidate is None:
            fallback_x = sx + radius + 8
            fallback_y = sy - radius - 8
            best_candidate = (
                fallback_x,
                fallback_y,
                "sw",
                self._text_bbox(fallback_x, fallback_y, "sw", width, height),
            )

        self._label_boxes.append(best_candidate[3])
        return best_candidate[0], best_candidate[1], best_candidate[2]

    def _draw_text_label(self, point: Point, color: str, label: str, radius: int):
        """Desenha um texto ao lado de um ponto usando o posicionamento calculado."""
        sx, sy = self.quadro.mundo_para_canvas(point[0], point[1])
        x, y, anchor = self._choose_label_position(sx, sy, radius, label)
        self.canvas.create_text(
            x,
            y,
            text=label,
            fill=color,
            font=self._label_font,
            anchor=anchor,
            tags="SCENE",
        )

    def _draw_marker(self, point: Point, color: str, radius: int, label: str | None = None):
        """Desenha um marcador circular e, opcionalmente, seu rótulo associado."""
        sx, sy = self.quadro.mundo_para_canvas(point[0], point[1])
        self.canvas.create_oval(sx - radius, sy - radius, sx + radius, sy + radius, fill=color, outline=color, tags="SCENE")
        if label is not None:
            self._draw_text_label(point, color, label, radius)

    def _draw_label(self, point: Point, color: str, label: str):
        """Desenha apenas o texto de um ponto sem o marcador visual."""
        self._draw_text_label(point, color, label, 0)

    def _draw_vertices(self, points: list[Point], color: str, prefix: str, radius: int):
        """Desenha os vértices do polígono com prefixos diferentes para original e recortado."""
        for index, point in enumerate(points, start=1):
            label = None
            if self.show_vertex_values_var.get():
                label = f"{prefix}{index} {self._format_point(point)}"
            if self.show_vertex_markers_var.get():
                self._draw_marker(point, color, radius, label)
            elif label is not None:
                self._draw_label(point, color, label)

    def _draw_intersections(self, intersections: list[Point]):
        """Mostra as interseções calculadas tanto no canvas quanto no resumo lateral."""
        if not self.show_intersections_var.get():
            self._set_text_lines(self.intersection_text, ["Interseccoes ocultas."])
            return

        if not intersections:
            self._set_text_lines(self.intersection_text, ["Sem interseccoes."])
            return

        self._set_text_lines(
            self.intersection_text,
            [self._format_named_point(f"I{index}", point) for index, point in enumerate(intersections, start=1)],
        )
        for index, point in enumerate(intersections, start=1):
            self._draw_marker(point, "#d90429", 4, f"I{index}")

    def _draw_scene(self, trace):
        """Renderiza janela, polígono original, polígono recortado e interseções."""
        self.canvas.delete("SCENE")
        self._label_boxes = []
        xmin, ymin, xmax, ymax = trace["window"]
        self._draw_window(xmin, ymin, xmax, ymax)

        if trace["original"]:
            self._draw_polygon_shape(trace["original"], outline="#9a031e", fill="#f4acb7", width=2, stipple="gray50")
            self._draw_vertices(trace["original"], "#9a031e", "V", 4)

        if trace["clipped"]:
            self._draw_polygon_shape(trace["clipped"], outline="#004e89", fill="#4c78d0", width=2, stipple="gray75")
            self._draw_vertices(trace["clipped"], "#005a9c", "C", 5)

        self._draw_intersections(trace["intersections"])

    def _redesenhar(self):
        """Refaz a cena armazenada quando o viewport muda."""
        if self._last:
            self._draw_scene(self._last)

    def _write_polygon_points(self, points: list[Point]):
        """Escreve a lista de vértices de entrada no painel lateral."""
        if not points:
            self._set_text_lines(self.input_text, ["Nenhum ponto cadastrado."])
            return
        self._set_text_lines(
            self.input_text,
            [self._format_named_point(f"V{index}", point) for index, point in enumerate(points, start=1)],
        )

    def _write_polygon_output(self, points: list[Point]):
        """Escreve a lista de vértices do polígono resultante após o recorte."""
        if not points:
            self._set_text_lines(self.output_text, ["Poligono totalmente fora da janela."])
            return
        self._set_text_lines(
            self.output_text,
            [self._format_named_point(f"C{index}", point) for index, point in enumerate(points, start=1)],
        )

    def _write_log(self, trace):
        """Espelha o trace detalhado do algoritmo em linguagem quase passo a passo."""
        self.log.delete("1.0", tk.END)
        xmin, ymin, xmax, ymax = trace["window"]
        self.log.insert(tk.END, f"Janela normalizada: xmin={xmin:g}, ymin={ymin:g}, xmax={xmax:g}, ymax={ymax:g}\n")
        self.log.insert(tk.END, f"Poligono original: {self._format_polygon_inline(trace['original'])}\n")
        for stage in trace["stages"]:
            self.log.insert(tk.END, "\n")
            self.log.insert(tk.END, f"Borda {stage['boundary']} = {stage['boundary_value']:g}\n")
            self.log.insert(tk.END, f"Entrada: {self._format_polygon_inline(stage['before'])}\n")
            for edge in stage.get("edge_steps", []):
                self.log.insert(
                    tk.END,
                    f"\nAresta {edge['edge_index']}: S={self._format_point(edge['start'])} | E={self._format_point(edge['end'])}\n",
                )
                self.log.insert(
                    tk.END,
                    f"Teste: S {'dentro' if edge['start_inside'] else 'fora'} | E {'dentro' if edge['end_inside'] else 'fora'}\n",
                )
                self.log.insert(tk.END, f"Regra aplicada: {edge['rule']}\n")
                self.log.insert(tk.END, f"Resultado: {edge['result']}\n")
                if edge["intersection"] is not None:
                    self.log.insert(tk.END, f"Intersecao calculada: {self._format_point(edge['intersection'])}\n")
                    for line in edge.get("calculation", []):
                        self.log.insert(tk.END, f"  {line}\n")
                if edge.get("added"):
                    self.log.insert(
                        tk.END,
                        "Saida gerada por esta aresta: "
                        f"{self._format_polygon_inline(edge['added'])}\n",
                    )
                else:
                    self.log.insert(tk.END, "Saida gerada por esta aresta: []\n")
            if stage["intersections"]:
                self.log.insert(
                    tk.END,
                    "Intersecoes unicas da etapa: "
                    f"{self._format_polygon_inline(stage['intersections'])}\n",
                )
            else:
                self.log.insert(tk.END, "Intersecoes unicas da etapa: nenhuma\n")
            self.log.insert(tk.END, f"Saida da borda: {self._format_polygon_inline(stage['after'])}\n")
        self.log.insert(tk.END, "\n")
        final_polygon = trace["clipped"] if trace["clipped"] else []
        self.log.insert(tk.END, f"Poligono final: {self._format_polygon_inline(final_polygon)}\n")
        self.log.see("1.0")

    def _fit_trace(self, trace, adjust_zoom=False):
        """Centraliza a câmera no conteúdo e opcionalmente escolhe um zoom que enquadre tudo."""
        values_x = [trace["window"][0], trace["window"][2]]
        values_y = [trace["window"][1], trace["window"][3]]
        for group in (trace["original"], trace["clipped"], trace["intersections"]):
            values_x.extend(point[0] for point in group)
            values_y.extend(point[1] for point in group)

        if not values_x or not values_y:
            return

        min_x, max_x = min(values_x), max(values_x)
        min_y, max_y = min(values_y), max(values_y)
        self.quadro.cxw = (min_x + max_x) / 2.0
        self.quadro.cyw = (min_y + max_y) / 2.0

        if adjust_zoom:
            width = max(1.0, max_x - min_x)
            height = max(1.0, max_y - min_y)
            usable_w = max(220, self.vp.largura - 120)
            usable_h = max(220, self.vp.altura - 120)
            zoom = int(min(usable_w / width, usable_h / height))
            zoom = max(1, min(40, zoom))
            self.zoom.set(zoom)
            self.vp.set_escala(zoom)

    def _reset_view(self):
        """Limpa a visualização e retorna os painéis auxiliares ao estado inicial."""
        self._last = None
        self.canvas.delete("SCENE")
        self.quadro.limpar()
        self._set_text_lines(self.input_text, ["Nenhum ponto cadastrado."])
        self._set_text_lines(self.output_text, ["Sem resultado."])
        self._set_text_lines(self.intersection_text, ["Sem interseccoes."])
        self.log.delete("1.0", tk.END)
        self._set_status("Defina a janela, informe os vertices e visualize o poligono original e o recortado.")

    def limpar(self):
        """Remove os vértices atuais mas preserva a janela de recorte da interface."""
        self.vertices_text.set("")
        try:
            xmin, ymin, xmax, ymax = self._read_window()
        except ValueError:
            self._reset_view()
            return

        self._reset_view()
        trace = {
            "window": (xmin, ymin, xmax, ymax),
            "original": [],
            "clipped": [],
            "intersections": [],
            "stages": [],
        }
        self._last = trace
        self._draw_scene(trace)
        self._set_status("Vertices removidos. A janela de recorte foi mantida.")

    def carregar_exemplo(self):
        """Carrega um polígono de teste que cruza várias bordas da janela."""
        self.vertices_text.set("-45,8; -8,38; 36,28; 45,-6;")
        self.xmin.set(-20)
        self.ymin.set(-20)
        self.xmax.set(25)
        self.ymax.set(20)
        self.desenhar(auto_fit=True)

    def enquadrar(self):
        """Ajusta o centro e o zoom para mostrar a cena inteira confortavelmente."""
        if not self._last:
            return
        self._fit_trace(self._last, adjust_zoom=True)
        self.quadro.redraw()

    def desenhar(self, auto_fit=False):
        """Executa o recorte, atualiza o trace e renderiza os painéis de apoio."""
        try:
            vertices = self._parse_vertices(allow_empty=True)
            xmin, ymin, xmax, ymax = self._read_window()
        except ValueError as exc:
            messagebox.showerror("Entrada invalida", str(exc))
            return

        self._reset_view()
        self._write_polygon_points(vertices)

        if len(vertices) < 3:
            trace = {
                "window": (xmin, ymin, xmax, ymax),
                "original": list(vertices),
                "clipped": [],
                "intersections": [],
                "stages": [],
            }
            self._last = trace
            self._draw_scene(trace)
            self._set_text_lines(self.output_text, ["Adicione pelo menos tres vertices."])
            self._set_text_lines(self.intersection_text, ["Sem interseccoes."])
            self._set_status("Adicione pelo menos tres vertices para aplicar Sutherland-Hodgman.")
            return

        trace = sutherland_hodgman_clip_trace(vertices, xmin, ymin, xmax, ymax)
        self._last = trace
        if auto_fit:
            self._fit_trace(trace, adjust_zoom=True)
        else:
            self._fit_trace(trace, adjust_zoom=False)
        self._draw_scene(trace)
        self._write_polygon_output(trace["clipped"])
        self._write_log(trace)
        self._set_status(
            f"Janela de ({self._format_number(xmin)}, {self._format_number(ymin)}) a "
            f"({self._format_number(xmax)}, {self._format_number(ymax)}). "
            f"Poligono com {len(vertices)} vertices: original em vermelho claro, recortado em azul. "
            "Arraste para mover e use a roda do mouse para zoom."
        )



def main():
    """Ponto de entrada isolado da interface de Sutherland-Hodgman."""
    root = tk.Tk()
    root.title("Questao 2 - Sutherland-Hodgman")
    AppSutherlandHodgman(root)
    root.mainloop()


if __name__ == "__main__":
    main()