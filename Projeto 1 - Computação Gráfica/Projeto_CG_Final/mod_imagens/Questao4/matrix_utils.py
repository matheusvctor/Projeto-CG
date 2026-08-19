import math

def identity_3x3():
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

def multiply_3x3(A, B):
    """Compõe duas transformações homogêneas 2D na ordem matricial A * B."""
    result = [[0.0]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                result[i][j] += A[i][k] * B[k][j]
    return result

def multiply_vec(M, v):
    """Aplica uma matriz homogênea 3x3 a um vetor coluna [x, y, 1]."""
    res = [0.0]*3
    for i in range(3):
        for j in range(3):
            res[i] += M[i][j] * v[j]
    return res

def invert_3x3(m):
    """Inverte a matriz 3x3 para permitir o mapeamento inverso da imagem transformada."""
    det = (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
           m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
           m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))
    if det == 0: return identity_3x3()
    
    inv = [[0.0]*3 for _ in range(3)]
    inv[0][0] =  (m[1][1] * m[2][2] - m[1][2] * m[2][1]) / det
    inv[0][1] = -(m[0][1] * m[2][2] - m[0][2] * m[2][1]) / det
    inv[0][2] =  (m[0][1] * m[1][2] - m[0][2] * m[1][1]) / det
    inv[1][0] = -(m[1][0] * m[2][2] - m[1][2] * m[2][0]) / det
    inv[1][1] =  (m[0][0] * m[2][2] - m[0][2] * m[2][0]) / det
    inv[1][2] = -(m[0][0] * m[1][2] - m[0][2] * m[1][0]) / det
    inv[2][0] =  (m[1][0] * m[2][1] - m[1][1] * m[2][0]) / det
    inv[2][1] = -(m[0][0] * m[2][1] - m[0][1] * m[2][0]) / det
    inv[2][2] =  (m[0][0] * m[1][1] - m[0][1] * m[1][0]) / det
    return inv

def translate_2d(tx, ty):
    """Cria a matriz homogênea de translação 2D."""
    return [[1.0, 0.0, float(tx)], [0.0, 1.0, float(ty)], [0.0, 0.0, 1.0]]

def scale_2d(sx, sy):
    """Cria a matriz homogênea de escala 2D."""
    return [[float(sx), 0.0, 0.0], [0.0, float(sy), 0.0], [0.0, 0.0, 1.0]]

def rotate_2d(angle_deg):
    """Cria a matriz homogênea de rotação em torno da origem."""
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]

def shear_2d(shx, shy):
    """Cria a matriz homogênea de cisalhamento em X e/ou Y."""
    return [[1.0, float(shx), 0.0], [float(shy), 1.0, 0.0], [0.0, 0.0, 1.0]]

def reflect_y_2d():
    """Espelha a imagem em torno do eixo Y, invertendo o sinal de X."""
    return [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]