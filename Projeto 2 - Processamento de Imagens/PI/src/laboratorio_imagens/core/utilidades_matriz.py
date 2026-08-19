from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def limitar_uint8(matriz: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(matriz), 0, 255).astype(np.uint8)


def normalizar_uint8(matriz: np.ndarray) -> np.ndarray:
    matriz_float = np.asarray(matriz, dtype=np.float64)
    minimo = float(matriz_float.min())
    maximo = float(matriz_float.max())
    if maximo - minimo < 1e-9:
        return np.zeros_like(matriz_float, dtype=np.uint8)
    normalizada = (matriz_float - minimo) * 255.0 / (maximo - minimo)
    return np.clip(np.rint(normalizada), 0, 255).astype(np.uint8)


def ajustar_para_mesmo_tamanho(
    matriz_a: np.ndarray,
    matriz_b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    altura = min(matriz_a.shape[0], matriz_b.shape[0])
    largura = min(matriz_a.shape[1], matriz_b.shape[1])
    return matriz_a[:altura, :largura], matriz_b[:altura, :largura]


def padronizar_binaria(matriz: np.ndarray) -> np.ndarray:
    return np.where(np.asarray(matriz) > 0, 255, 0).astype(np.uint8)


def limiarizar_por_valor(matriz: np.ndarray, limiar: int) -> np.ndarray:
    return np.where(np.asarray(matriz) >= limiar, 255, 0).astype(np.uint8)


def limiarizar_pela_media(matriz: np.ndarray) -> np.ndarray:
    limiar = int(np.mean(matriz))
    return limiarizar_por_valor(matriz, limiar)


def _extrair_janelas(matriz: np.ndarray, formato_janela: tuple[int, int], modo_borda: str) -> np.ndarray:
    margem_y = formato_janela[0] // 2
    margem_x = formato_janela[1] // 2
    expandida = np.pad(matriz, ((margem_y, margem_y), (margem_x, margem_x)), mode=modo_borda)
    return sliding_window_view(expandida, formato_janela)


def aplicar_correlacao(
    matriz: np.ndarray,
    mascara: np.ndarray,
    *,
    modo_borda: str = "edge",
) -> np.ndarray:
    mascara_array = np.asarray(mascara, dtype=np.float64)
    janelas = _extrair_janelas(np.asarray(matriz, dtype=np.float64), mascara_array.shape, modo_borda)
    return np.einsum("ijkl,kl->ij", janelas, mascara_array)


def aplicar_mediana(
    matriz: np.ndarray,
    *,
    tamanho: int = 3,
    modo_borda: str = "edge",
) -> np.ndarray:
    janelas = _extrair_janelas(np.asarray(matriz, dtype=np.float64), (tamanho, tamanho), modo_borda)
    return np.median(janelas, axis=(-2, -1))


def calcular_maximo_local(
    matriz: np.ndarray,
    elemento_estruturante: np.ndarray,
    *,
    modo_borda: str = "edge",
) -> np.ndarray:
    janelas = _extrair_janelas(np.asarray(matriz, dtype=np.float64), elemento_estruturante.shape, modo_borda)
    mascara = np.asarray(elemento_estruturante, dtype=bool)
    valores = janelas[..., mascara]
    return np.max(valores, axis=-1)


def calcular_minimo_local(
    matriz: np.ndarray,
    elemento_estruturante: np.ndarray,
    *,
    modo_borda: str = "edge",
) -> np.ndarray:
    janelas = _extrair_janelas(np.asarray(matriz, dtype=np.float64), elemento_estruturante.shape, modo_borda)
    mascara = np.asarray(elemento_estruturante, dtype=bool)
    valores = janelas[..., mascara]
    return np.min(valores, axis=-1)


def janelas_binarias(
    matriz_binaria: np.ndarray,
    elemento_estruturante: np.ndarray,
    *,
    modo_borda: str = "constant",
) -> np.ndarray:
    matriz_bool = np.asarray(matriz_binaria > 0, dtype=bool)
    margem_y = elemento_estruturante.shape[0] // 2
    margem_x = elemento_estruturante.shape[1] // 2
    expandida = np.pad(
        matriz_bool,
        ((margem_y, margem_y), (margem_x, margem_x)),
        mode=modo_borda,
        constant_values=False,
    )
    return sliding_window_view(expandida, elemento_estruturante.shape)
