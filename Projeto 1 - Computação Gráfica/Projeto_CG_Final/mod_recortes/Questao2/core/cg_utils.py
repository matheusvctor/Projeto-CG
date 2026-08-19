#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core.cg_utils - drawing helpers and clipping routines.
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Iterable


class Viewport:
    def __init__(self, largura=900, altura=700, escala=1):
        """Representa a área visível e o zoom do canvas de recorte."""
        self.largura = int(largura)
        self.altura = int(altura)
        self.escala = max(1, int(escala))

    def set_escala(self, escala_px_un):
        """Atualiza a escala em pixels por unidade."""
        self.escala = max(1, int(escala_px_un))

    def set_size(self, largura, altura):
        """Atualiza o tamanho lógico do canvas."""
        self.largura = int(max(1, largura))
        self.altura = int(max(1, altura))


class QuadroDesenho:
    def __init__(self, canvas: tk.Canvas, vp: Viewport, usar_grade=True):
        """Encapsula pan, zoom e conversões entre mundo e canvas nas telas de recorte."""
        self.cv = canvas
        self.vp = vp
        self.usar_grade = usar_grade
        self.cxw = 0.0
        self.cyw = 0.0
        self._drag_last = None
        self.on_redraw = None
        self.pan_enabled = True
        self.limpar()
        self._bind_interactions()

    def set_redraw_callback(self, fn):
        """Registra a função chamada após cada limpeza/redesenho do canvas."""
        self.on_redraw = fn

    def set_pan_enabled(self, enabled: bool):
        """Habilita ou desabilita o pan do botão esquerdo, útil no modo desenho."""
        self.pan_enabled = bool(enabled)
        if not self.pan_enabled:
            self._drag_last = None

    def _bind_interactions(self):
        self.cv.bind("<ButtonPress-1>", self._on_pan_start)
        self.cv.bind("<B1-Motion>", self._on_pan_drag)
        self.cv.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag_last", None))
        self.cv.bind("<MouseWheel>", self._on_wheel)
        self.cv.bind("<Button-4>", lambda e: self._on_wheel_like(e, +120))
        self.cv.bind("<Button-5>", lambda e: self._on_wheel_like(e, -120))

    def _on_pan_start(self, e):
        if not self.pan_enabled:
            self._drag_last = None
            return
        self._drag_last = (e.x, e.y)

    def _on_pan_drag(self, e):
        if not self.pan_enabled or not self._drag_last:
            return
        sx0, sy0 = self._drag_last
        dx, dy = e.x - sx0, e.y - sy0
        if dx or dy:
            self.cxw -= dx / self.vp.escala
            self.cyw += dy / self.vp.escala
            self._drag_last = (e.x, e.y)
            self.redraw()

    def _on_wheel_like(self, e, delta):
        class E:
            pass

        ev = E()
        ev.x, ev.y, ev.delta = e.x, e.y, delta
        self._on_wheel(ev)

    def _on_wheel(self, e):
        old = self.vp.escala
        new = max(1, int(round(old * (1.15 if e.delta > 0 else 1 / 1.15))))
        if new == old:
            new = old + (1 if e.delta > 0 else -1)
            if new < 1:
                new = 1
        wx, wy = self.canvas_para_mundo(e.x, e.y)
        self.vp.set_escala(new)
        cx, cy = self.vp.largura // 2, self.vp.altura // 2
        self.cxw = wx - (e.x - cx) / self.vp.escala
        self.cyw = wy - (cy - e.y) / self.vp.escala
        self.redraw()

    def mundo_para_canvas(self, x, y):
        cx, cy = self.vp.largura // 2, self.vp.altura // 2
        sx = int(round(cx + (x - self.cxw) * self.vp.escala))
        sy = int(round(cy - (y - self.cyw) * self.vp.escala))
        return sx, sy

    def canvas_para_mundo(self, sx, sy):
        cx, cy = self.vp.largura // 2, self.vp.altura // 2
        x = self.cxw + (sx - cx) / self.vp.escala
        y = self.cyw + (cy - sy) / self.vp.escala
        return x, y

    def limpar(self):
        self.cv.delete("all")
        if self.usar_grade:
            self._desenhar_grade()
        self._desenhar_borda()

    def redraw(self):
        self.limpar()
        if callable(self.on_redraw):
            self.on_redraw()

    def resize(self, largura, altura):
        self.vp.set_size(largura, altura)
        self.cv.config(width=self.vp.largura, height=self.vp.altura)
        self.redraw()

    def put_pixel(self, x, y, cor="#000000", s=1):
        sx, sy = self.mundo_para_canvas(x, y)
        tamanho = max(1, s * self.vp.escala)
        self.cv.create_rectangle(sx, sy, sx + tamanho, sy + tamanho, outline=cor, fill=cor)

    def _desenhar_borda(self):
        self.cv.create_rectangle(1, 1, self.vp.largura - 1, self.vp.altura - 1, outline="#d6d6d6", width=2)

    def _desenhar_grade(self, cor_eixo="#888888"):
        sx0, sy0 = self.mundo_para_canvas(0, 0)
        self.cv.create_line(0, sy0, self.vp.largura, sy0, fill=cor_eixo, width=2, tags="GRADE")
        self.cv.create_line(sx0, 0, sx0, self.vp.altura, fill=cor_eixo, width=2, tags="GRADE")


_quadro = None
_app = None
_coletor = None

INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8
Point = tuple[float, float]
Polygon = list[Point]


def registrar_quadro(quadro: QuadroDesenho, app):
    """Registra o quadro global usado pelas rotinas de desenho deste módulo."""
    global _quadro, _app
    _quadro, _app = quadro, app


def ligar_coleta(lista_destino):
    """Ativa a coleta de pixels para inspeção auxiliar."""
    global _coletor
    _coletor = lista_destino


def desligar_coleta():
    """Desativa a coleta auxiliar de pixels."""
    global _coletor
    _coletor = None


def set_pixel(x, y, cor="#000000"):
    """Plota um pixel e, se necessário, o registra na lista de coleta."""
    if _coletor is not None:
        _coletor.append((x, y))
    if _quadro is not None and _app is not None:
        _quadro.put_pixel(x, y, cor, _app.tamanho_pixel.get())


def reta_dda(x0, y0, x1, y1, cor="#000000"):
    """Rasteriza um segmento 2D com DDA."""
    dx, dy = x1 - x0, y1 - y0
    passos = int(max(abs(dx), abs(dy)))
    if passos == 0:
        set_pixel(round(x0), round(y0), cor)
        return
    inc_x = dx / passos
    inc_y = dy / passos
    x, y = x0, y0
    for _ in range(passos + 1):
        set_pixel(round(x), round(y), cor)
        x += inc_x
        y += inc_y


def desenhar_poligono(vertices: Iterable[Point], cor="#000000"):
    """Desenha um polígono fechado a partir de seus vértices."""
    pontos = list(vertices)
    if not pontos:
        return
    if len(pontos) == 1:
        set_pixel(round(pontos[0][0]), round(pontos[0][1]), cor)
        return
    if len(pontos) == 2:
        reta_dda(pontos[0][0], pontos[0][1], pontos[1][0], pontos[1][1], cor)
        return

    for indice, atual in enumerate(pontos):
        proximo = pontos[(indice + 1) % len(pontos)]
        reta_dda(atual[0], atual[1], proximo[0], proximo[1], cor)


def desenhar_janela(xmin, ymin, xmax, ymax, cor="#1f4e79"):
    """Desenha o retângulo da janela de recorte atual."""
    xmin, xmax = sorted((xmin, xmax))
    ymin, ymax = sorted((ymin, ymax))
    reta_dda(xmin, ymin, xmax, ymin, cor)
    reta_dda(xmax, ymin, xmax, ymax, cor)
    reta_dda(xmax, ymax, xmin, ymax, cor)
    reta_dda(xmin, ymax, xmin, ymin, cor)


def normalizar_janela(xmin, ymin, xmax, ymax):
    """Reordena os quatro limites para garantir min antes de max."""
    xmin, xmax = sorted((xmin, xmax))
    ymin, ymax = sorted((ymin, ymax))
    return xmin, ymin, xmax, ymax


def _same_point(first: Point, second: Point, tolerance: float = 1e-9) -> bool:
    """Compara pontos com tolerância para evitar duplicatas numéricas."""
    return abs(first[0] - second[0]) <= tolerance and abs(first[1] - second[1]) <= tolerance


def _append_unique(points: list[Point], point: Point) -> None:
    """Acrescenta um ponto somente se ele ainda não estiver na lista."""
    for existing in points:
        if _same_point(existing, point):
            return
    points.append(point)


def _point_within_window(
    point: Point,
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    tolerance: float = 1e-9,
) -> bool:
    """Verifica se um ponto pertence ao interior da janela, com tolerância numérica."""
    x, y = point
    return xmin - tolerance <= x <= xmax + tolerance and ymin - tolerance <= y <= ymax + tolerance


def _remove_redundant_vertices(vertices: Polygon) -> Polygon:
    """Remove vértices repetidos criados pelas etapas intermediárias de clipping."""
    if not vertices:
        return []

    cleaned = [vertices[0]]
    for point in vertices[1:]:
        if not _same_point(point, cleaned[-1]):
            cleaned.append(point)

    if len(cleaned) > 1 and _same_point(cleaned[0], cleaned[-1]):
        cleaned.pop()

    return cleaned


def _intersect_with_vertical(start: Point, end: Point, boundary_x: float) -> Point:
    """Calcula a interseção entre um segmento e uma borda vertical."""
    x1, y1 = start
    x2, y2 = end
    if x2 == x1:
        return boundary_x, y1

    # Parametriza o segmento e fixa x = boundary_x para achar a intersecao.
    t = (boundary_x - x1) / (x2 - x1)
    y = y1 + t * (y2 - y1)
    return boundary_x, y


def _intersect_with_horizontal(start: Point, end: Point, boundary_y: float) -> Point:
    """Calcula a interseção entre um segmento e uma borda horizontal."""
    x1, y1 = start
    x2, y2 = end
    if y2 == y1:
        return x1, boundary_y

    # Parametriza o segmento e fixa y = boundary_y para achar a intersecao.
    t = (boundary_y - y1) / (y2 - y1)
    x = x1 + t * (x2 - x1)
    return x, boundary_y


def _clip_vertical(vertices: Iterable[Point], boundary_x: float, keep_greater: bool) -> tuple[Polygon, list[Point]]:
    """Recorta um polígono contra uma única borda vertical do retângulo."""
    polygon = list(vertices)
    if not polygon:
        return [], []

    def inside(point: Point) -> bool:
        # Nesta etapa, "dentro" depende apenas da borda vertical atual.
        return point[0] >= boundary_x if keep_greater else point[0] <= boundary_x

    clipped: Polygon = []
    intersections: list[Point] = []
    previous = polygon[-1]
    previous_inside = inside(previous)

    for current in polygon:
        current_inside = inside(current)

        # Implementa os quatro casos do Sutherland-Hodgman:
        # dentro->dentro, fora->dentro, dentro->fora e fora->fora.
        if current_inside:
            if not previous_inside:
                point = _intersect_with_vertical(previous, current, boundary_x)
                clipped.append(point)
                _append_unique(intersections, point)
            clipped.append(current)
        elif previous_inside:
            point = _intersect_with_vertical(previous, current, boundary_x)
            clipped.append(point)
            _append_unique(intersections, point)

        previous = current
        previous_inside = current_inside

    return _remove_redundant_vertices(clipped), intersections


def _clip_horizontal(vertices: Iterable[Point], boundary_y: float, keep_greater: bool) -> tuple[Polygon, list[Point]]:
    """Recorta um polígono contra uma única borda horizontal do retângulo."""
    polygon = list(vertices)
    if not polygon:
        return [], []

    def inside(point: Point) -> bool:
        # Nesta etapa, "dentro" depende apenas da borda horizontal atual.
        return point[1] >= boundary_y if keep_greater else point[1] <= boundary_y

    clipped: Polygon = []
    intersections: list[Point] = []
    previous = polygon[-1]
    previous_inside = inside(previous)

    for current in polygon:
        current_inside = inside(current)

        # Implementa os quatro casos do Sutherland-Hodgman:
        # dentro->dentro, fora->dentro, dentro->fora e fora->fora.
        if current_inside:
            if not previous_inside:
                point = _intersect_with_horizontal(previous, current, boundary_y)
                clipped.append(point)
                _append_unique(intersections, point)
            clipped.append(current)
        elif previous_inside:
            point = _intersect_with_horizontal(previous, current, boundary_y)
            clipped.append(point)
            _append_unique(intersections, point)

        previous = current
        previous_inside = current_inside

    return _remove_redundant_vertices(clipped), intersections


def clip_against_vertical_boundary(vertices: Iterable[Point], boundary_x: float, keep_greater: bool) -> Polygon:
    """Wrapper enxuto para recorte vertical sem devolver interseções."""
    clipped, _ = _clip_vertical(vertices, boundary_x, keep_greater)
    return clipped


def clip_against_horizontal_boundary(vertices: Iterable[Point], boundary_y: float, keep_greater: bool) -> Polygon:
    """Wrapper enxuto para recorte horizontal sem devolver interseções."""
    clipped, _ = _clip_horizontal(vertices, boundary_y, keep_greater)
    return clipped


def sutherland_hodgman_clip(
    vertices: Iterable[Point],
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> Polygon:
    """Executa o Sutherland-Hodgman retornando apenas o polígono final."""
    polygon, _ = sutherland_hodgman_clip_details(vertices, xmin, ymin, xmax, ymax)
    return polygon


def sutherland_hodgman_clip_details(
    vertices: Iterable[Point],
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
) -> tuple[Polygon, list[Point]]:
    """Executa o recorte e também devolve as interseções relevantes."""
    polygon = list(vertices)
    intersections: list[Point] = []
    xmin, ymin, xmax, ymax = normalizar_janela(xmin, ymin, xmax, ymax)

    # O poligono de saida de uma borda vira a entrada da borda seguinte.
    polygon, points = _clip_vertical(polygon, xmin, keep_greater=True)
    for point in points:
        _append_unique(intersections, point)
    polygon, points = _clip_vertical(polygon, xmax, keep_greater=False)
    for point in points:
        _append_unique(intersections, point)
    polygon, points = _clip_horizontal(polygon, ymin, keep_greater=True)
    for point in points:
        _append_unique(intersections, point)
    polygon, points = _clip_horizontal(polygon, ymax, keep_greater=False)
    for point in points:
        _append_unique(intersections, point)

    filtered_intersections = [
        point for point in intersections if _point_within_window(point, xmin, ymin, xmax, ymax)
    ]
    return _remove_redundant_vertices(polygon), filtered_intersections


def _trace_intersection_calculation(start: Point, end: Point, boundary_value: float, is_vertical: bool) -> tuple[Point, list[str]]:
    """Produz a interseção e o texto matemático usado pela interface explicativa."""
    x1, y1 = start
    x2, y2 = end
    lines: list[str] = []

    # Reconstroi as formulas da intersecao para a explicacao textual na UI.
    if is_vertical:
        if x2 == x1:
            point = (boundary_value, y1)
            lines.append(f"x = {boundary_value:g} (valor da borda vertical)")
            lines.append(f"Como x2 == x1 == {x1:g}, mantemos y = y1 = {y1:g}.")
            lines.append(f"Intersecao = ({point[0]:g}, {point[1]:g})")
            return point, lines

        t = (boundary_value - x1) / (x2 - x1)
        y = y1 + t * (y2 - y1)
        point = (boundary_value, y)
        lines.append(f"x = {boundary_value:g} (valor da borda vertical)")
        lines.append(
            f"t = (xborda - x1) / (x2 - x1) = ({boundary_value:g} - {x1:g}) / ({x2:g} - {x1:g}) = {t:.6f}"
        )
        lines.append(
            f"y = y1 + t * (y2 - y1) = {y1:g} + {t:.6f} * ({y2:g} - {y1:g}) = {y:.6f}"
        )
        lines.append(f"Intersecao = ({point[0]:g}, {point[1]:.6f})")
        return point, lines

    if y2 == y1:
        point = (x1, boundary_value)
        lines.append(f"y = {boundary_value:g} (valor da borda horizontal)")
        lines.append(f"Como y2 == y1 == {y1:g}, mantemos x = x1 = {x1:g}.")
        lines.append(f"Intersecao = ({point[0]:g}, {point[1]:g})")
        return point, lines

    t = (boundary_value - y1) / (y2 - y1)
    x = x1 + t * (x2 - x1)
    point = (x, boundary_value)
    lines.append(f"y = {boundary_value:g} (valor da borda horizontal)")
    lines.append(
        f"t = (yborda - y1) / (y2 - y1) = ({boundary_value:g} - {y1:g}) / ({y2:g} - {y1:g}) = {t:.6f}"
    )
    lines.append(
        f"x = x1 + t * (x2 - x1) = {x1:g} + {t:.6f} * ({x2:g} - {x1:g}) = {x:.6f}"
    )
    lines.append(f"Intersecao = ({point[0]:.6f}, {point[1]:g})")
    return point, lines


def _trace_clip_stage(
    vertices: Iterable[Point],
    boundary_name: str,
    boundary_value: float,
    keep_greater: bool,
    is_vertical: bool,
) -> tuple[Polygon, list[Point], list[dict]]:
    """Registra uma etapa completa do clipping de uma borda com as decisões tomadas."""
    polygon = list(vertices)
    if not polygon:
        return [], [], []

    def inside(point: Point) -> bool:
        # O teste de dentro/fora sempre e relativo a uma unica borda por vez.
        if is_vertical:
            return point[0] >= boundary_value if keep_greater else point[0] <= boundary_value
        return point[1] >= boundary_value if keep_greater else point[1] <= boundary_value

    clipped: Polygon = []
    intersections: list[Point] = []
    edge_steps: list[dict] = []
    previous = polygon[-1]
    previous_inside = inside(previous)

    for index, current in enumerate(polygon, start=1):
        current_inside = inside(current)
        added: list[Point] = []
        calculation: list[str] = []
        intersection = None

        if previous_inside and current_inside:
            rule = 'dentro -> dentro'
            result = 'Mantem apenas o vertice atual na saida.'
            clipped.append(current)
            added.append(current)
        elif (not previous_inside) and current_inside:
            rule = 'fora -> dentro'
            result = 'Adiciona a intersecao e depois o vertice atual.'
            intersection, calculation = _trace_intersection_calculation(previous, current, boundary_value, is_vertical)
            clipped.append(intersection)
            clipped.append(current)
            added.extend([intersection, current])
            _append_unique(intersections, intersection)
        elif previous_inside and (not current_inside):
            rule = 'dentro -> fora'
            result = 'Adiciona apenas a intersecao e descarta o vertice atual.'
            intersection, calculation = _trace_intersection_calculation(previous, current, boundary_value, is_vertical)
            clipped.append(intersection)
            added.append(intersection)
            _append_unique(intersections, intersection)
        else:
            rule = 'fora -> fora'
            result = 'Nenhum ponto e enviado para a saida.'

        # Guarda a decisao da aresta junto com a conta usada na intersecao.
        edge_steps.append(
            {
                'edge_index': index,
                'start': previous,
                'end': current,
                'start_inside': previous_inside,
                'end_inside': current_inside,
                'rule': rule,
                'result': result,
                'intersection': intersection,
                'calculation': calculation,
                'added': list(added),
            }
        )

        previous = current
        previous_inside = current_inside

    return _remove_redundant_vertices(clipped), intersections, edge_steps


def sutherland_hodgman_clip_trace(
    vertices: Iterable[Point],
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
):
    """Retorna um trace completo do algoritmo para desenho e log detalhado."""
    original = _remove_redundant_vertices(list(vertices))
    polygon = list(original)
    xmin, ymin, xmax, ymax = normalizar_janela(xmin, ymin, xmax, ymax)
    intersections: list[Point] = []
    stages = []
    boundaries = [
        ("ESQUERDA", xmin, True, True),
        ("DIREITA", xmax, False, True),
        ("FUNDO", ymin, True, False),
        ("TOPO", ymax, False, False),
    ]

    for name, boundary_value, keep_greater, is_vertical in boundaries:
        before = list(polygon)
        polygon, points, edge_steps = _trace_clip_stage(before, name, boundary_value, keep_greater, is_vertical)
        for point in points:
            _append_unique(intersections, point)
        stages.append(
            {
                "boundary": name,
                "boundary_value": boundary_value,
                "before": before,
                "after": list(polygon),
                "intersections": list(points),
                "edge_steps": edge_steps,
            }
        )

    filtered_intersections = [
        point for point in intersections if _point_within_window(point, xmin, ymin, xmax, ymax)
    ]
    return {
        "window": (xmin, ymin, xmax, ymax),
        "original": original,
        "clipped": _remove_redundant_vertices(polygon),
        "intersections": filtered_intersections,
        "stages": stages,
    }
def compute_outcode(x, y, xmin, ymin, xmax, ymax):
    """Calcula o código regional de Cohen-Sutherland para um ponto."""
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code


def format_outcode(code):
    """Converte o outcode para a representação binária usada na UI."""
    return f"{1 if code & TOP else 0}{1 if code & BOTTOM else 0}{1 if code & RIGHT else 0}{1 if code & LEFT else 0}"


def nomes_outcode(code):
    """Traduz os bits ativos do outcode para nomes legíveis."""
    nomes = []
    if code & TOP:
        nomes.append("TOPO")
    if code & BOTTOM:
        nomes.append("FUNDO")
    if code & RIGHT:
        nomes.append("DIREITA")
    if code & LEFT:
        nomes.append("ESQUERDA")
    return "INSIDE" if not nomes else " + ".join(nomes)


def cohen_sutherland_clip(x0, y0, x1, y1, xmin, ymin, xmax, ymax):
    """Recorta uma reta e devolve o resultado junto com as etapas do processo."""
    xmin, ymin, xmax, ymax = normalizar_janela(xmin, ymin, xmax, ymax)

    code0 = compute_outcode(x0, y0, xmin, ymin, xmax, ymax)
    code1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
    steps = [
        f"P0=({x0:.3f}, {y0:.3f}) code={format_outcode(code0)} [{nomes_outcode(code0)}]",
        f"P1=({x1:.3f}, {y1:.3f}) code={format_outcode(code1)} [{nomes_outcode(code1)}]",
    ]
    intersections = []
    aceito = False

    while True:
        if not (code0 | code1):
            aceito = True
            steps.append("Aceitacao trivial: ambos os pontos estao dentro da janela.")
            break
        if code0 & code1:
            steps.append("Rejeicao trivial: ha um bit comum diferente de zero nos dois outcodes.")
            break

        code_out = code0 if code0 else code1
        if code_out & TOP:
            x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
            y = ymax
            borda = "TOPO"
        elif code_out & BOTTOM:
            x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
            y = ymin
            borda = "FUNDO"
        elif code_out & RIGHT:
            y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
            x = xmax
            borda = "DIREITA"
        else:
            y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
            x = xmin
            borda = "ESQUERDA"

        steps.append(
            f"Intersecao com a borda {borda}: ({x:.3f}, {y:.3f}) a partir do ponto com code {format_outcode(code_out)}."
        )
        intersections.append((x, y, borda))

        if code_out == code0:
            x0, y0 = x, y
            code0 = compute_outcode(x0, y0, xmin, ymin, xmax, ymax)
            steps.append(
                f"Atualiza P0 -> ({x0:.3f}, {y0:.3f}) code={format_outcode(code0)} [{nomes_outcode(code0)}]"
            )
        else:
            x1, y1 = x, y
            code1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
            steps.append(
                f"Atualiza P1 -> ({x1:.3f}, {y1:.3f}) code={format_outcode(code1)} [{nomes_outcode(code1)}]"
            )

    return {
        "accepted": aceito,
        "window": (xmin, ymin, xmax, ymax),
        "original": (x0, y0, x1, y1),
        "clipped": (x0, y0, x1, y1) if aceito else None,
        "initial_codes": (steps[0], steps[1]),
        "steps": steps,
        "intersections": intersections,
    }
