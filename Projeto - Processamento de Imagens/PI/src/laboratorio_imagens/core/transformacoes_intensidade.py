from __future__ import annotations

import numpy as np

from laboratorio_imagens.core.utilidades_matriz import limitar_uint8


def negativo(matriz: np.ndarray) -> np.ndarray:
    """Aplica a transformação de negativo na imagem em níveis de cinza.

    Fórmula Matemática:
        s = (L - 1) - r = 255 - r
    Onde:
        - r: intensidade do pixel original [0, 255]
        - s: intensidade resultante invertida
    """
    return 255 - np.asarray(matriz, dtype=np.uint8)


def transformacao_gamma(matriz: np.ndarray, gamma: float, c: float = 1.0) -> np.ndarray:
    """Aplica a transformação de potência (Correção Gamma).

    Fórmula Matemática:
        s = c * (r / 255.0)^gamma * 255.0
    Propriedades:
        - gamma < 1.0: Expande tons escuros (clareia regiões de sombras).
        - gamma > 1.0: Comprime tons escuros (escurece e aumenta contraste em realces).
        - gamma == 1.0: Mapeamento linear identidade.
    """
    matriz_float = np.asarray(matriz, dtype=np.float64) / 255.0
    resultado = 255.0 * c * np.power(matriz_float, gamma)
    return limitar_uint8(resultado)


def transformacao_logaritmica(matriz: np.ndarray, constante: float | None = None) -> np.ndarray:
    """Aplica a transformação logarítmica para expansão de valores baixos de intensidade.

    Fórmula Matemática:
        s = c * ln(1 + r)
    Onde:
        - c = 255 / ln(1 + 255) para garantir que a saída ocupe a faixa completa [0, 255].
    Utilidade:
        - Realça detalhes em áreas escuras comprimindo valores dinâmicos muito altos (ex: espectro de Fourier).
    """
    matriz_float = np.asarray(matriz, dtype=np.float64)
    if constante is None:
        constante = 255.0 / np.log1p(255.0)
    resultado = constante * np.log1p(matriz_float)
    return limitar_uint8(resultado)


def transformacao_linear(matriz: np.ndarray, a: float, b: float) -> np.ndarray:
    """Aplica uma função de transferência linear afim aos níveis de cinza.

    Fórmula Matemática:
        s = a * r + b
    Onde:
        - a: Ganho / Contraste (inclinação da reta)
        - b: Offset / Brilho (deslocamento vertical)
    """
    matriz_float = np.asarray(matriz, dtype=np.float64)
    return limitar_uint8(a * matriz_float + b)


def faixa_dinamica(matriz: np.ndarray, faixa_saida: int = 255) -> np.ndarray:
    """Aplica o alargamento de contraste (estiramento de faixa dinâmica / Min-Max Scaling).

    Fórmula Matemática:
        s = ((r - r_min) / (r_max - r_min)) * faixa_saida
    Onde:
        - r_min: menor intensidade presente na imagem original
        - r_max: maior intensidade presente na imagem original
        - faixa_saida: valor máximo da escala de destino (padrão 255)
    """
    matriz_float = np.asarray(matriz, dtype=np.float64)
    minimo = float(matriz_float.min())
    maximo = float(matriz_float.max())
    if maximo - minimo < 1e-9:
        return np.zeros_like(matriz_float, dtype=np.uint8)
    resultado = ((matriz_float - minimo) / (maximo - minimo)) * faixa_saida
    return limitar_uint8(resultado)


def funcao_sigmoide(matriz: np.ndarray, centro: float = 127.0, largura: float = 25.0) -> np.ndarray:
    """Aplica a função de transferência sigmoidal (curva S) para aumento suave de contraste.

    Fórmula Matemática:
        s = 255.0 / (1.0 + exp(-(r - centro) / largura))
    Onde:
        - centro: Ponto de inflexão onde o contraste é máximo (geralmente 127.0)
        - largura: Controla a suavidade da transição da curva
    """
    matriz_float = np.asarray(matriz, dtype=np.float64)
    largura_segura = largura if abs(largura) > 1e-9 else 1.0
    resultado = 255.0 / (1.0 + np.exp(-(matriz_float - centro) / largura_segura))
    return limitar_uint8(resultado)
