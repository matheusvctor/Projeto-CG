#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core.cg_utils – utilitários de desenho, transformações 3D e recorte de janela.
"""

import math
import tkinter as tk

class Viewport:
    def __init__(self, largura=900, altura=700, escala=1):
        self.largura = int(largura)
        self.altura = int(altura)
        self.escala = max(1, int(escala))

    def set_escala(self, escala_px_un):
        self.escala = max(1, int(escala_px_un))

    def set_size(self, largura, altura):
        self.largura = int(max(1, largura))
        self.altura = int(max(1, altura))

_coletor = None
INSIDE = 0
LEFT = 1
RIGHT = 2
BOTTOM = 4
TOP = 8

def set_pixel(cv, x, y, cor="#000000"):
    ix, iy = int(round(x)), int(round(y))
    cv.create_line(ix, iy, ix + 1, iy, fill=cor, width=1)

def reta_dda(cv, x0, y0, x1, y1, cor="#000000"):
    """Desenha uma reta 2D com DDA, usada após a projeção do modelo 3D."""
    dx, dy = x1 - x0, y1 - y0
    passos = int(max(abs(dx), abs(dy)))
    if passos == 0:
        set_pixel(cv, round(x0), round(y0), cor)
        return
    inc_x = dx / passos
    inc_y = dy / passos
    x, y = x0, y0
    for _ in range(passos + 1):
        set_pixel(cv, round(x), round(y), cor)
        x += inc_x
        y += inc_y

# ==========================================
# MOTOR 3D E MATRIZES
# ==========================================

def mat_mult(A, B):
    """Multiplica duas matrizes 4x4 para compor transformações 3D homogêneas."""
    result = [[0.0]*4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                result[i][j] += A[i][k] * B[k][j]
    return result

def vec_mult(M, v):
    """Aplica uma matriz 4x4 a um vetor homogêneo [x, y, z, w]."""
    res = [0.0]*4
    for i in range(4):
        for j in range(4):
            res[i] += M[i][j] * v[j]
    if res[3] != 0 and res[3] != 1.0:
        res = [r / res[3] for r in res]
    return res

def identity():
    return [[1.0,0,0,0], [0,1.0,0,0], [0,0,1.0,0], [0,0,0,1.0]]

def translate3d(tx, ty, tz):
    return [[1.0, 0, 0, tx], [0, 1.0, 0, ty], [0, 0, 1.0, tz], [0, 0, 0, 1.0]]

def scale3d(sx, sy, sz):
    return [[sx, 0, 0, 0], [0, sy, 0, 0], [0, 0, sz, 0], [0, 0, 0, 1.0]]

def rotate_x(angle_deg):
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    return [[1.0, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]]

def rotate_y(angle_deg):
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    return [[c, 0, s, 0], [0, 1.0, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]]

def rotate_z(angle_deg):
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]

def reflect_x3d():
    return scale3d(-1.0, 1.0, 1.0)

def reflect_y3d():
    return scale3d(1.0, -1.0, 1.0)

def reflect_z3d():
    return scale3d(1.0, 1.0, -1.0)

def shear3d(shxy=0.0, shxz=0.0, shyx=0.0, shyz=0.0, shzx=0.0, shzy=0.0):
    """Gera a matriz de cisalhamento 3D."""
    return [
        [1.0,  shxy, shxz, 0.0],
        [shyx, 1.0,  shyz, 0.0],
        [shzx, shzy, 1.0,  0.0],
        [0.0,  0.0,  0.0,  1.0]
    ]

def projection_isometric():
    m_ry = rotate_y(45)
    m_rx = rotate_x(-35.264389682754654) # arcosseno(1/sqrt(3))
    return mat_mult(m_rx, m_ry)

# ==========================================
# RECORTE SUTHERLAND-HODGMAN (Polígonos 2D)
# ==========================================

def inside_poly(p, edge, rect):
    """Testa se um ponto está dentro de uma borda do retângulo de clipping."""
    xmin, xmax, ymin, ymax = rect
    x, y = p[0], p[1]
    if edge == 0: return x >= xmin
    if edge == 1: return x <= xmax
    if edge == 2: return y >= ymin
    if edge == 3: return y <= ymax

def intersect_poly(p1, p2, edge, rect):
    """Calcula a interseção entre uma aresta do polígono e uma borda do retângulo."""
    xmin, xmax, ymin, ymax = rect
    x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
    if edge == 0: return [xmin, y1 + (xmin - x1) * (y2 - y1) / (x2 - x1) if x2 != x1 else y1]
    if edge == 1: return [xmax, y1 + (xmax - x1) * (y2 - y1) / (x2 - x1) if x2 != x1 else y1]
    if edge == 2: return [x1 + (ymin - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else x1, ymin]
    if edge == 3: return [x1 + (ymax - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else x1, ymax]

def sutherland_hodgman_clip(polygon, rect):
    """Recorta o polígono já projetado contra o retângulo da viewport."""
    out_poly = polygon
    for edge in range(4):
        in_poly = out_poly
        out_poly = []
        if len(in_poly) == 0: break
        for i in range(len(in_poly)):
            p1 = in_poly[i - 1]
            p2 = in_poly[i]
            p1_in = inside_poly(p1, edge, rect)
            p2_in = inside_poly(p2, edge, rect)
            if p1_in and p2_in: 
                out_poly.append(p2)
            elif p1_in and not p2_in: 
                out_poly.append(intersect_poly(p1, p2, edge, rect))
            elif not p1_in and p2_in:
                out_poly.append(intersect_poly(p1, p2, edge, rect))
                out_poly.append(p2)
    return out_poly