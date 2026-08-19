import math
from matrix_utils import multiply_vec, invert_3x3

def read_pgm(filename):
    """Lê imagens PGM P2/P5 manualmente para manter o projeto sem dependências externas."""
    with open(filename, 'rb') as f:
        header = f.readline().decode('ascii').strip()
        while True:
            pos = f.tell()
            line = f.readline()
            if not line.startswith(b'#'):
                f.seek(pos)
                break
        dim_data = f.readline().decode('ascii').split()
        width, height = int(dim_data[0]), int(dim_data[1])
        maxval = int(f.readline().decode('ascii').strip())
        
        if header == 'P5':
            pixels = list(f.read(width * height))
        elif header == 'P2':
            data = f.read().decode('ascii').split()
            pixels = [int(p) for p in data]
        else:
            raise ValueError("Formato PGM não suportado")
    return width, height, maxval, pixels

def write_pgm_p5(filename, width, height, pixels):
    """Serializa a imagem temporária no formato P5 para o Tkinter conseguir exibi-la."""
    with open(filename, 'wb') as f:
        f.write(f"P5\n{width} {height}\n255\n".encode('ascii'))
        f.write(bytes(pixels))

def apply_image_transformation(pixels, width, height, transform_matrix):
    """Aplica a transformação afim por mapeamento inverso usando vizinho mais próximo."""
    corners = [
        multiply_vec(transform_matrix, [0, 0, 1]),
        multiply_vec(transform_matrix, [width-1, 0, 1]),
        multiply_vec(transform_matrix, [0, height-1, 1]),
        multiply_vec(transform_matrix, [width-1, height-1, 1])
    ]
    xs = [c[0]/c[2] for c in corners]
    ys = [c[1]/c[2] for c in corners]
    
    min_x, max_x = int(math.floor(min(xs))), int(math.ceil(max(xs)))
    min_y, max_y = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    
    new_width = max_x - min_x + 1
    new_height = max_y - min_y + 1

    inv_m = invert_3x3(transform_matrix)
    new_pixels = [255] * (new_width * new_height)
    
    for ny in range(new_height):
        for nx in range(new_width):
            wx = nx + min_x
            wy = ny + min_y
            orig_p = multiply_vec(inv_m, [wx, wy, 1])
            ox = int(round(orig_p[0] / orig_p[2]))
            oy = int(round(orig_p[1] / orig_p[2]))
            
            if 0 <= ox < width and 0 <= oy < height:
                val = pixels[oy * width + ox]
                new_pixels[ny * new_width + nx] = val
                
    return new_pixels, new_width, new_height
