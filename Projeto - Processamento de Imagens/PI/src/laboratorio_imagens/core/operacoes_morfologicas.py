from __future__ import annotations

import numpy as np

from laboratorio_imagens.core.utilidades_matriz import (
    calcular_maximo_local,
    calcular_minimo_local,
    janelas_binarias,
    limitar_uint8,
    padronizar_binaria,
)


ELEMENTOS_ESTRUTURANTES = {
    "Quadrado 3x3": np.ones((3, 3), dtype=np.uint8),
    "Cruz 3x3": np.array(
        [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ],
        dtype=np.uint8,
    ),
    "Quadrado 5x5": np.ones((5, 5), dtype=np.uint8),
}


MASCARAS_HIT_OR_MISS = {
    "Ponto isolado": np.array(
        [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ],
        dtype=np.int8,
    ),
    "Canto superior esquerdo": np.array(
        [
            [1, 1, -1],
            [1, 0, -1],
            [-1, -1, -1],
        ],
        dtype=np.int8,
    ),
    "Cruz": np.array(
        [
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ],
        dtype=np.int8,
    ),
}


def dilatacao_binaria(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    """Dilatação binária: (A ⊕ B).

    Pergunta do professor: "Como funciona a dilatação binária?"
    Resposta: Expande os objetos brancos (1/255). Se PELO MENOS UM pixel sob o elemento
    estruturante for 1 (operador lógico OR / np.any), o pixel central de saída torna-se 255.
    Efeito: Preenche pequenos buracos e une descontinuidades.
    """
    janelas = janelas_binarias(matriz, elemento_estruturante)
    mascara = np.asarray(elemento_estruturante, dtype=bool)
    resultado = np.any(janelas[..., mascara], axis=-1)
    return padronizar_binaria(resultado)


def erosao_binaria(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    """Erosão binária: (A ⊖ B).

    Pergunta do professor: "Como funciona a erosão binária?"
    Resposta: Encolhe os objetos brancos. Somente se TODOS os pixels sob o elemento
    estruturante forem 1 (operador lógico AND / np.all), o pixel central de saída torna-se 255.
    Efeito: Elimina ruídos isolados e afina estruturas.
    """
    janelas = janelas_binarias(matriz, elemento_estruturante)
    mascara = np.asarray(elemento_estruturante, dtype=bool)
    resultado = np.all(janelas[..., mascara], axis=-1)
    return padronizar_binaria(resultado)


def abertura_binaria(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    return dilatacao_binaria(erosao_binaria(matriz, elemento_estruturante), elemento_estruturante)


def fechamento_binaria(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    return erosao_binaria(dilatacao_binaria(matriz, elemento_estruturante), elemento_estruturante)


def hit_or_miss(matriz: np.ndarray, mascara: np.ndarray) -> np.ndarray:
    janelas = janelas_binarias(matriz, np.ones(mascara.shape, dtype=np.uint8))
    foreground = mascara == 1
    background = mascara == 0

    atende_frente = np.all(janelas[..., foreground], axis=-1) if np.any(foreground) else np.ones(
        matriz.shape, dtype=bool
    )
    atende_fundo = (
        np.all(~janelas[..., background], axis=-1)
        if np.any(background)
        else np.ones(matriz.shape, dtype=bool)
    )
    return padronizar_binaria(atende_frente & atende_fundo)


def contorno_interno_binario(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = padronizar_binaria(matriz).astype(np.int16)
    erodida = erosao_binaria(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(base - erodida)


def contorno_externo_binario(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = padronizar_binaria(matriz).astype(np.int16)
    dilatada = dilatacao_binaria(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(dilatada - base)


def gradiente_morfologico_binario(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    dilatada = dilatacao_binaria(matriz, elemento_estruturante).astype(np.int16)
    erodida = erosao_binaria(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(dilatada - erodida)


def top_hat_binario(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = padronizar_binaria(matriz).astype(np.int16)
    aberta = abertura_binaria(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(base - aberta)


def bottom_hat_binario(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = padronizar_binaria(matriz).astype(np.int16)
    fechada = fechamento_binaria(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(fechada - base)


def dilatacao_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    return limitar_uint8(calcular_maximo_local(matriz, elemento_estruturante))


def erosao_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    return limitar_uint8(calcular_minimo_local(matriz, elemento_estruturante))


def abertura_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    return dilatacao_cinza(erosao_cinza(matriz, elemento_estruturante), elemento_estruturante)


def fechamento_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    return erosao_cinza(dilatacao_cinza(matriz, elemento_estruturante), elemento_estruturante)


def gradiente_morfologico_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    dilatada = dilatacao_cinza(matriz, elemento_estruturante).astype(np.int16)
    erodida = erosao_cinza(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(dilatada - erodida)


def contorno_interno_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = np.asarray(matriz, dtype=np.int16)
    erodida = erosao_cinza(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(base - erodida)


def contorno_externo_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = np.asarray(matriz, dtype=np.int16)
    dilatada = dilatacao_cinza(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(dilatada - base)


def top_hat_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = np.asarray(matriz, dtype=np.int16)
    aberta = abertura_cinza(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(base - aberta)


def bottom_hat_cinza(matriz: np.ndarray, elemento_estruturante: np.ndarray) -> np.ndarray:
    base = np.asarray(matriz, dtype=np.int16)
    fechada = fechamento_cinza(matriz, elemento_estruturante).astype(np.int16)
    return limitar_uint8(fechada - base)
