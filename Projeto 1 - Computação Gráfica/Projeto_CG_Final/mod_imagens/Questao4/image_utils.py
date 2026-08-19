import math
from matrix_utils import multiply_vec, invert_3x3


def _ler_tokens_pgm(f):
    """Gerador de tokens (palavras) ignorando comentários que começam com '#'."""
    while True:
        linha = f.readline()
        if not linha:
            break
        # Remove comentários do NetPBM iniciados com '#'
        if b'#' in linha:
            linha = linha[:linha.index(b'#')]
        partes = linha.split()
        for p in partes:
            yield p


def read_pgm(filename):
    """Lê imagens PGM P2 (ASCII) e P5 (Binário) de forma robusta e sem bibliotecas externas."""
    with open(filename, 'rb') as f:
        # Lê o formato P2 ou P5
        token_gen = _ler_tokens_pgm(f)
        header = next(token_gen).decode('ascii').strip()
        
        if header not in ('P2', 'P5'):
            raise ValueError(f"Formato NetPBM '{header}' não suportado. Esperado P2 ou P5.")
        
        width = int(next(token_gen).decode('ascii'))
        height = int(next(token_gen).decode('ascii'))
        maxval = int(next(token_gen).decode('ascii'))
        
        if header == 'P2':
            pixels = []
            for _ in range(width * height):
                pixels.append(int(next(token_gen).decode('ascii')))
        elif header == 'P5':
            # Para P5, os bytes de pixel começam imediatamente após o cabeçalho
            # Posiciona o cursor no fim do cabeçalho binário
            # Reabre para buscar bytes brutos a partir do offset
            f.seek(0)
            cabecalho_lido = 0
            tokens_cabecalho = 0
            while tokens_cabecalho < 4:
                b = f.read(1)
                if not b:
                    break
                cabecalho_lido += 1
                if b == b'#':
                    # Pula até o fim da linha
                    while True:
                        c = f.read(1)
                        cabecalho_lido += 1
                        if not c or c in (b'\r', b'\n'):
                            break
                elif b in (b' ', b'\t', b'\r', b'\n'):
                    pass
                else:
                    # Início de um token
                    tokens_cabecalho += 1
                    while True:
                        prox = f.read(1)
                        cabecalho_lido += 1
                        if not prox or prox in (b' ', b'\t', b'\r', b'\n', b'#'):
                            if prox == b'#':
                                # Se terminou em comentário, volta 1 byte para o handler tratar
                                f.seek(f.tell() - 1)
                                cabecalho_lido -= 1
                            break
            
            dados = f.read(width * height)
            pixels = list(dados)

        # Normaliza valores para escala 0..255 se maxval != 255
        if maxval != 255 and maxval > 0:
            escala = 255.0 / maxval
            pixels = [int(round(p * escala)) for p in pixels]

    return width, height, maxval, pixels


def write_pgm_p5(filename, width, height, pixels):
    """Serializa a imagem no formato P5 (binário) para exibição direta no Tkinter."""
    # Garante que todos os valores sejam inteiros no intervalo [0, 255]
    dados_bytes = bytes(max(0, min(255, int(round(p)))) for p in pixels)
    with open(filename, 'wb') as f:
        f.write(f"P5\n{width} {height}\n255\n".encode('ascii'))
        f.write(dados_bytes)


def apply_image_transformation(pixels, width, height, transform_matrix, bg_color=0, expand_canvas=True):
    """Aplica a transformação afim por Mapeamento Inverso (Inverse Mapping).
    
    Parâmetros:
    - pixels: Lista linear de intensidades de pixel [0..255]
    - width, height: Dimensões originais da imagem
    - transform_matrix: Matriz homogênea 3x3
    - bg_color: Intensidade de fundo para posições fora da imagem original (ex: 0 para preto, 255 para branco)
    - expand_canvas:
        * False (Quadro Fixo): Mantém o enquadramento original (width × height). A imagem se desloca
          visivelmente dentro do quadro, com as margens expostas preenchidas por bg_color.
        * True (Bounding Box): Expande o quadro para conter toda a imagem transformada.
    """
    inv_m = invert_3x3(transform_matrix)
    
    if not expand_canvas:
        new_width = width
        new_height = height
        min_x = 0
        min_y = 0
    else:
        corners = [
            multiply_vec(transform_matrix, [0, 0, 1]),
            multiply_vec(transform_matrix, [width - 1, 0, 1]),
            multiply_vec(transform_matrix, [0, height - 1, 1]),
            multiply_vec(transform_matrix, [width - 1, height - 1, 1])
        ]
        xs = [c[0] / c[2] for c in corners if abs(c[2]) > 1e-9]
        ys = [c[1] / c[2] for c in corners if abs(c[2]) > 1e-9]
        
        if not xs or not ys:
            return pixels.copy(), width, height
        
        min_x = int(math.floor(min(xs)))
        max_x = int(math.ceil(max(xs)))
        min_y = int(math.floor(min(ys)))
        max_y = int(math.ceil(max(ys)))
        
        new_width = max(1, max_x - min_x + 1)
        new_height = max(1, max_y - min_y + 1)

    new_pixels = [bg_color] * (new_width * new_height)
    
    for ny in range(new_height):
        for nx in range(new_width):
            wx = nx + min_x
            wy = ny + min_y
            orig_p = multiply_vec(inv_m, [wx, wy, 1])
            if abs(orig_p[2]) < 1e-9:
                continue
            ox = int(round(orig_p[0] / orig_p[2]))
            oy = int(round(orig_p[1] / orig_p[2]))
            
            if 0 <= ox < width and 0 <= oy < height:
                val = pixels[oy * width + ox]
                new_pixels[ny * new_width + nx] = val
                
    return new_pixels, new_width, new_height


