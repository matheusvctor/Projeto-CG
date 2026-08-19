"""
core.cg_utils – motor compartilhado (viewport/canvas, raster e transformações 2D).
"""

import math
import tkinter as tk

class Viewport:
    def __init__(self, largura=900, altura=900, escala=1):
        """Guarda o tamanho visível e a escala usada na conversão mundo/canvas."""
        self.largura = int(largura)
        self.altura  = int(altura)
        self.escala  = max(1, int(escala))

    def set_escala(self, escala_px_un):
        """Atualiza o zoom em pixels por unidade."""
        self.escala = max(1, int(escala_px_un))

    def set_size(self, largura, altura):
        """Atualiza o tamanho do retângulo de desenho quando a janela muda."""
        self.largura = int(max(1, largura))
        self.altura  = int(max(1, altura))

class QuadroDesenho:
    def __init__(self, canvas: tk.Canvas, vp: Viewport, usar_grade=True):
        """Encapsula o canvas, o pan/zoom e o mapeamento entre mundo e tela."""
        self.cv = canvas
        self.vp = vp
        self.usar_grade = usar_grade
        self.cxw = 0.0
        self.cyw = 0.0
        self._drag_last = None
        self.on_redraw = None
        self.limpar()
        self._bind_interactions()

    def set_redraw_callback(self, fn): self.on_redraw = fn
    def _bind_interactions(self):
        self.cv.bind("<ButtonPress-1>", self._on_pan_start)
        self.cv.bind("<B1-Motion>", self._on_pan_drag)
        self.cv.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag_last", None))
        self.cv.bind("<MouseWheel>", self._on_wheel)  # Win/Mac
        self.cv.bind("<Button-4>", lambda e: self._on_wheel_like(e, +120))  # X11
        self.cv.bind("<Button-5>", lambda e: self._on_wheel_like(e, -120))

    def _on_pan_start(self, e): self._drag_last = (e.x, e.y)
    def _on_pan_drag(self, e):
        if not self._drag_last: return
        sx0, sy0 = self._drag_last
        dx, dy = e.x - sx0, e.y - sy0
        if dx or dy:
            self.cxw -= dx / self.vp.escala
            self.cyw += dy / self.vp.escala
            self._drag_last = (e.x, e.y)
            self.redraw()

    def _on_wheel_like(self, e, delta):
        class E: pass
        ev = E(); ev.x, ev.y, ev.delta = e.x, e.y, delta
        self._on_wheel(ev)

    def _on_wheel(self, e):
        old = self.vp.escala
        new = max(1, int(round(old * (1.15 if e.delta > 0 else 1/1.15))))
        if new == old:
            new = old + (1 if e.delta > 0 else -1)
            if new < 1: new = 1

        wx, wy = self.canvas_para_mundo(e.x, e.y)
        self.vp.set_escala(new)
        cx, cy = self.vp.largura//2, self.vp.altura//2
        self.cxw = wx - (e.x - cx)/self.vp.escala
        self.cyw = wy - (cy - e.y)/self.vp.escala
        self.redraw()

    def mundo_para_canvas(self, x, y):
        cx, cy = self.vp.largura//2, self.vp.altura//2
        sx = int(round(cx + (x - self.cxw)*self.vp.escala))
        sy = int(round(cy - (y - self.cyw)*self.vp.escala))
        return sx, sy
    def canvas_para_mundo(self, sx, sy):
        cx, cy = self.vp.largura//2, self.vp.altura//2
        x = self.cxw + (sx - cx)/self.vp.escala
        y = self.cyw + (cy - sy)/self.vp.escala
        return x, y

    def _world_bounds(self):
        half_w = self.vp.largura/(2*self.vp.escala)
        half_h = self.vp.altura /(2*self.vp.escala)
        return self.cxw - half_w, self.cxw + half_w, self.cyw - half_h, self.cyw + half_h

    def _desenhar_borda(self):
        self.cv.create_rectangle(1,1,self.vp.largura-1,self.vp.altura-1, outline="#d6d6d6", width=2, tags="BORDA")

    def _desenhar_grade(self, alvo_px=24, cor_eixo="#888"):
        sx0, _ = self.mundo_para_canvas(0, 0)
        _ , sy0 = self.mundo_para_canvas(0, 0)
        self.cv.create_line(0, sy0, self.vp.largura, sy0, fill=cor_eixo, width=2, tags="GRADE") # Eixo X
        self.cv.create_line(sx0, 0, sx0, self.vp.altura, fill=cor_eixo, width=2, tags="GRADE")  # Eixo Y

    def limpar(self):
        self.cv.delete("all")
        if self.usar_grade: self._desenhar_grade(alvo_px=24)
        self._desenhar_borda()

    def redraw(self):
        self.limpar()
        if callable(self.on_redraw): self.on_redraw()

    def resize(self, largura, altura):
        self.vp.set_size(largura, altura)
        self.cv.config(width=self.vp.largura, height=self.vp.altura)
        self.redraw()

    def put_pixel(self, x, y, cor="#000", s=1):
        sx, sy = self.mundo_para_canvas(x, y)
        tamanho = max(1, s * self.vp.escala) 
        if tamanho <= 1:
            self.cv.create_line(sx, sy, sx + 1, sy, fill=cor, width=1)
        else:
            self.cv.create_rectangle(sx, sy, sx + tamanho, sy + tamanho, outline="", fill=cor)

_quadro = None
_app    = None
_coletor = None
_EPS = 1e-9

def registrar_quadro(quadro: QuadroDesenho, app):
    """Registra o quadro atual para as rotinas globais de rasterização."""
    global _quadro, _app
    _quadro, _app = quadro, app

def ligar_coleta(lista_destino):
    """Passa a coletar os pixels desenhados em uma lista externa."""
    global _coletor; _coletor = lista_destino
def desligar_coleta():
    """Encerra a coleta auxiliar de pixels."""
    global _coletor; _coletor = None

def set_pixel(x, y, cor="#000000"):
    """Plota um pixel no canvas ativo e o registra na coleta, quando habilitada."""
    if _coletor is not None: _coletor.append((x, y))
    if _quadro is not None and _app is not None:
        _quadro.put_pixel(x, y, cor, _app.tamanho_pixel.get())

def _quase_zero(valor, eps=_EPS):
    """Evita tratar erros numéricos de ponto flutuante como valores significativos."""
    return abs(valor) <= eps

def _limites_inteiros_visiveis(margem=2):
    """Obtém os limites inteiros visíveis do mundo para restringir varreduras."""
    if _quadro is None:
        return -100, 100, -100, 100
    xmin, xmax, ymin, ymax = _quadro._world_bounds()
    return (
        math.floor(xmin) - margem,
        math.ceil(xmax) + margem,
        math.floor(ymin) - margem,
        math.ceil(ymax) + margem,
    )

def _resolver_quadratica(a, b, c):
    """Resolve uma equação quadrática retornando apenas raízes reais."""
    if _quase_zero(a):
        if _quase_zero(b):
            return []
        return [-c / b]
    delta = b * b - 4 * a * c
    if delta < -_EPS:
        return []
    if _quase_zero(delta):
        return [-b / (2 * a)]
    raiz_delta = math.sqrt(max(0.0, delta))
    x1 = (-b - raiz_delta) / (2 * a)
    x2 = (-b + raiz_delta) / (2 * a)
    return sorted([x1, x2])

def _conectar_amostras(anteriores, atuais, max_gap, cor):
    """Liga amostras próximas para evitar descontinuidades em curvas por varredura."""
    usados = set()
    for px, py in anteriores:
        melhor = None
        for i, (ax, ay) in enumerate(atuais):
            if i in usados:
                continue
            dist = max(abs(ax - px), abs(ay - py))
            if melhor is None or dist < melhor[0]:
                melhor = (dist, i, ax, ay)
        if melhor is None:
            continue
        dist, i, ax, ay = melhor
        if dist <= max_gap:
            reta_dda(px, py, ax, ay, cor)
            usados.add(i)

def reta_ponto_medio(x0, y0, x1, y1, cor="#000000"):
    """Rasteriza uma reta com o algoritmo do ponto médio/Bresenham."""
    dx, dy = x1 - x0, y1 - y0
    sx = 1 if dx >= 0 else -1; sy = 1 if dy >= 0 else -1
    dx, dy = abs(dx), abs(dy)
    if dx >= dy:
        d = 2*dy - dx; x, y = x0, y0
        for _ in range(dx+1):
            set_pixel(x, y, cor); x += sx
            if d <= 0: d += 2*dy
            else: d += 2*(dy-dx); y += sy
    else:
        d = 2*dx - dy; x, y = x0, y0
        for _ in range(dy+1):
            set_pixel(x, y, cor); y += sy
            if d <= 0: d += 2*dx
            else: d += 2*(dx-dy); x += sx

def reta_dda(x0, y0, x1, y1, cor="#000"):
    """Rasteriza uma reta com o algoritmo DDA."""
    dx, dy = x1-x0, y1-y0
    passos = int(max(abs(dx), abs(dy)))
    if passos == 0: set_pixel(x0, y0, cor); return
    inc_x, inc_y = dx/passos, dy/passos
    x, y = x0, y0
    for _ in range(passos+1):
        set_pixel(round(x), round(y), cor)
        x += inc_x; y += inc_y

def _sim8(xc, yc, x, y, cor="#000"):
    """Explora a simetria octogonal da circunferência."""
    set_pixel(xc+x, yc+y, cor); set_pixel(xc+y, yc+x, cor)
    set_pixel(xc+y, yc-x, cor); set_pixel(xc+x, yc-y, cor)
    set_pixel(xc-x, yc-y, cor); set_pixel(xc-y, yc-x, cor)
    set_pixel(xc-y, yc+x, cor); set_pixel(xc-x, yc+y, cor)

def circunferencia_ponto_medio(xc, yc, r, cor="#000"):
    """Desenha uma circunferência por ponto médio."""
    if r < 0: return
    x, y, d = 0, r, 1-r; _sim8(xc, yc, x, y, cor)
    while x < y:
        if d < 0: d += 2*x + 3; x += 1
        else: d += 2*(x - y) + 5; x += 1; y -= 1
        _sim8(xc, yc, x, y, cor)

def circunferencia_equacao(xc, yc, r, cor="#000"):
    """Desenha uma circunferência diretamente pela equação x² + y² = r²."""
    if r < 0: return
    for x in range(0, r + 1):
        y = int(round(math.sqrt(max(0, r*r - x*x))))
        set_pixel(xc + x, yc + y, cor)
        set_pixel(xc - x, yc + y, cor)
        set_pixel(xc + x, yc - y, cor)
        set_pixel(xc - x, yc - y, cor)

def circunferencia_trigonometrica(xc, yc, r, cor="#000"):
    """Desenha uma circunferência por parametrização trigonométrica."""
    if r <= 0: return
    passo = 1.0 / r
    t = 0.0
    fim = 2 * math.pi
    while t <= fim + 0.001:
        x = int(round(xc + r * math.cos(t)))
        y = int(round(yc + r * math.sin(t)))
        set_pixel(x, y, cor) 
        t += passo

def _sim4(xc, yc, x, y, cor="#000"):
    """Explora a simetria em quatro quadrantes da elipse."""
    set_pixel(xc + x, yc + y, cor)
    set_pixel(xc - x, yc + y, cor)
    set_pixel(xc + x, yc - y, cor)
    set_pixel(xc - x, yc - y, cor)

def elipse_ponto_medio(xc, yc, rx, ry, cor="#000"):
    """Desenha uma elipse por ponto médio, dividindo o cálculo em duas regiões."""
    x, y = 0, ry
    rx2 = rx * rx
    ry2 = ry * ry
    px, py = 0, 2 * rx2 * y

    d1 = round(ry2 - (rx2 * ry) + (0.25 * rx2))
    _sim4(xc, yc, x, y, cor)
    
    while px < py:
        x += 1
        px += 2 * ry2
        if d1 < 0:
            d1 += ry2 + px
        else:
            y -= 1
            py -= 2 * rx2
            d1 += ry2 + px - py
        _sim4(xc, yc, x, y, cor)

    d2 = round(ry2 * (x + 0.5)**2 + rx2 * (y - 1)**2 - rx2 * ry2)
    while y > 0:
        y -= 1
        py -= 2 * rx2
        if d2 > 0:
            d2 += rx2 - py
        else:
            x += 1
            px += 2 * ry2
            d2 += rx2 - py + px
        _sim4(xc, yc, x, y, cor)

def curva_bezier_cubica(p0, p1, p2, p3, passos=100, cor="#000"):
    """Amostra e liga os pontos de uma curva de Bézier cúbica."""
    pts = []
    for i in range(passos + 1):
        t = i / passos
        u = 1 - t
        x = (u**3)*p0[0] + 3*(u**2)*t*p1[0] + 3*u*(t**2)*p2[0] + (t**3)*p3[0]
        y = (u**3)*p0[1] + 3*(u**2)*t*p1[1] + 3*u*(t**2)*p2[1] + (t**3)*p3[1]
        pts.append((round(x), round(y)))

    for i in range(len(pts) - 1):
        reta_dda(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], cor)

def classificar_secao_conica(a, b, c, d, e, f):
    """Classifica a cônica a partir do discriminante da forma geral."""
    if _quase_zero(a) and _quase_zero(b) and _quase_zero(c):
        if _quase_zero(d) and _quase_zero(e):
            return ("Degenerada/sem curva", 0.0)
        return ("Degenerada (reta)", 0.0)

    discriminante = c * c - 4 * a * b
    if _quase_zero(discriminante):
        return ("Parábola", discriminante)
    if discriminante < 0:
        if _quase_zero(c) and _quase_zero(a - b) and not _quase_zero(a):
            return ("Circunferência", discriminante)
        return ("Elipse", discriminante)
    return ("Hipérbole", discriminante)

def secao_conica_varredura(a, b, c, d, e, f, limites=None, cor="#000000", margem=2, max_gap=5):
    """Desenha uma cônica geral varrendo X e Y e conectando amostras vizinhas."""
    vis_xmin, vis_xmax, vis_ymin, vis_ymax = _limites_inteiros_visiveis(margem)
    if limites is None:
        xmin, xmax, ymin, ymax = vis_xmin, vis_xmax, vis_ymin, vis_ymax
    else:
        lxmin, lxmax, lymin, lymax = limites
        xmin = max(vis_xmin, math.floor(lxmin))
        xmax = min(vis_xmax, math.ceil(lxmax))
        ymin = max(vis_ymin, math.floor(lymin))
        ymax = min(vis_ymax, math.ceil(lymax))

    if xmin > xmax or ymin > ymax:
        return

    anteriores = []
    for x in range(xmin, xmax + 1):
        raizes = _resolver_quadratica(
            b,
            c * x + e,
            a * x * x + d * x + f,
        )
        atuais = []
        for y in raizes:
            if ymin - max_gap <= y <= ymax + max_gap:
                py = int(round(y))
                set_pixel(x, py, cor)
                atuais.append((x, py))
        _conectar_amostras(anteriores, atuais, max_gap, cor)
        anteriores = atuais

    anteriores = []
    for y in range(ymin, ymax + 1):
        raizes = _resolver_quadratica(
            a,
            c * y + d,
            b * y * y + e * y + f,
        )
        atuais = []
        for x in raizes:
            if xmin - max_gap <= x <= xmax + max_gap:
                px = int(round(x))
                set_pixel(px, y, cor)
                atuais.append((px, y))
        _conectar_amostras(anteriores, atuais, max_gap, cor)
        anteriores = atuais

def multiplicar_matrizes(a, b):
    """Multiplica matrizes usadas nas transformações homogêneas 2D."""
    m, n = len(a), len(a[0]); n2, p = len(b), len(b[0]); assert n == n2
    r = [[0.0]*p for _ in range(m)]
    for i in range(m):
        for j in range(p):
            r[i][j] = sum(a[i][k]*b[k][j] for k in range(n))
    return r

def para_homogeneas(pts):
    """Converte pontos 2D para colunas homogêneas [x, y, 1]."""
    return [[p[0] for p in pts],[p[1] for p in pts],[1.0]*len(pts)]

def de_homogeneas(m):
    """Converte coordenadas homogêneas de volta para pares (x, y)."""
    xs,ys,ws=m
    return [(x/w if w else x, y/w if w else y) for x,y,w in zip(xs,ys,ws)]

def aplicar_transformacao(pts, M):
    """Aplica uma matriz homogênea 2D a todos os pontos do objeto."""
    return de_homogeneas(multiplicar_matrizes(M, para_homogeneas(pts)))

def T(tx,ty):
    """Matriz de translação 2D."""
    return [[1,0,tx],[0,1,ty],[0,0,1]]

def S(sx,sy):
    """Matriz de escala 2D."""
    return [[sx,0,0],[0,sy,0],[0,0,1]]

def R(theta):
    """Matriz de rotação 2D em graus."""
    t=math.radians(theta); c,s=math.cos(t),math.sin(t)
    return [[c,-s,0],[s,c,0],[0,0,1]]
def Sh(shx=0.0, shy=0.0):
    """Matriz de cisalhamento 2D."""
    return [[1,   shx, 0],
            [shy, 1,   0],
            [0,   0,   1]]

def seg_origem(L):
    """Segmento horizontal base com origem em (0,0)."""
    return [(0,0),(L,0)]

def quadrado_origem(Sz):
    """Quadrado alinhado aos eixos usado como objeto base."""
    return [(0,0),(Sz,0),(Sz,Sz),(0,Sz)]

def triangulo_origem(Sz):
    """Triângulo retângulo simples usado como objeto base."""
    return [(0,0),(Sz,0),(0,Sz)]
