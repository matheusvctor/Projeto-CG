from __future__ import annotations

import numpy as np

from laboratorio_imagens.core.utilidades_matriz import limitar_uint8


def negativo(matriz: np.ndarray) -> np.ndarray:
    return 255 - np.asarray(matriz, dtype=np.uint8)


def transformacao_gamma(matriz: np.ndarray, gamma: float, c: float = 1.0) -> np.ndarray:
    matriz_float = np.asarray(matriz, dtype=np.float64) / 255.0
    resultado = 255.0 * c * np.power(matriz_float, gamma)
    return limitar_uint8(resultado)


def transformacao_logaritmica(matriz: np.ndarray, constante: float | None = None) -> np.ndarray:
    matriz_float = np.asarray(matriz, dtype=np.float64)
    if constante is None:
        constante = 255.0 / np.log1p(255.0)
    resultado = constante * np.log1p(matriz_float)
    return limitar_uint8(resultado)


def transformacao_linear(matriz: np.ndarray, a: float, b: float) -> np.ndarray:
    matriz_float = np.asarray(matriz, dtype=np.float64)
    return limitar_uint8(a * matriz_float + b)


def faixa_dinamica(matriz: np.ndarray, faixa_saida: int = 255) -> np.ndarray:
    matriz_float = np.asarray(matriz, dtype=np.float64)
    minimo = float(matriz_float.min())
    maximo = float(matriz_float.max())
    if maximo - minimo < 1e-9:
        return np.zeros_like(matriz_float, dtype=np.uint8)
    resultado = ((matriz_float - minimo) / (maximo - minimo)) * faixa_saida
    return limitar_uint8(resultado)


def funcao_sigmoide(matriz: np.ndarray, centro: float = 127.0, largura: float = 25.0) -> np.ndarray:
    matriz_float = np.asarray(matriz, dtype=np.float64)
    largura_segura = largura if abs(largura) > 1e-9 else 1.0
    resultado = 255.0 / (1.0 + np.exp(-(matriz_float - centro) / largura_segura))
    return limitar_uint8(resultado)
