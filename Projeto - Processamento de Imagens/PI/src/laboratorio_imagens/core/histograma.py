from __future__ import annotations

import numpy as np


def calcular_histograma(matriz: np.ndarray) -> np.ndarray:
    valores = np.asarray(matriz, dtype=np.uint8).ravel()
    return np.bincount(valores, minlength=256)


def equalizar_histograma(matriz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    imagem = np.asarray(matriz, dtype=np.uint8)
    histograma_original = calcular_histograma(imagem)
    total_pixels = imagem.size
    probabilidades = histograma_original / max(total_pixels, 1)
    distribuicao_acumulada = np.cumsum(probabilidades)
    tabela = np.floor(255 * distribuicao_acumulada).astype(np.uint8)
    imagem_equalizada = tabela[imagem]
    histograma_equalizado = calcular_histograma(imagem_equalizada)
    return imagem_equalizada, histograma_original, histograma_equalizado
