from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from laboratorio_imagens.core.utilidades_matriz import (
    aplicar_correlacao,
    aplicar_mediana,
    limitar_uint8,
)


@dataclass(frozen=True)
class EspecificacaoFiltro:
    nome: str
    descricao: str


FILTROS_DISPONIVEIS = [
    EspecificacaoFiltro("Filtro da media", "Mascara 3x3 uniforme."),
    EspecificacaoFiltro("Filtro da mediana", "Substitui cada pixel pela mediana local."),
    EspecificacaoFiltro("Passa-altas basico", "Realce simples para pontos e detalhes finos."),
    EspecificacaoFiltro("Roberts", "Gradiente por diferencas simples."),
    EspecificacaoFiltro("Roberts X", "Resposta do operador de Roberts apenas no eixo X."),
    EspecificacaoFiltro("Roberts Y", "Resposta do operador de Roberts apenas no eixo Y."),
    EspecificacaoFiltro("Roberts cruzado", "Gradiente cruzado de Roberts."),
    EspecificacaoFiltro("Roberts cruzado X", "Resposta do operador de Roberts cruzado apenas no eixo X."),
    EspecificacaoFiltro("Roberts cruzado Y", "Resposta do operador de Roberts cruzado apenas no eixo Y."),
    EspecificacaoFiltro("Prewitt", "Operador de bordas por gradiente."),
    EspecificacaoFiltro("Prewitt X", "Resposta do operador de Prewitt apenas no eixo X."),
    EspecificacaoFiltro("Prewitt Y", "Resposta do operador de Prewitt apenas no eixo Y."),
    EspecificacaoFiltro("Sobel", "Operador de bordas com suavizacao."),
    EspecificacaoFiltro("Sobel X", "Resposta do operador de Sobel apenas no eixo X."),
    EspecificacaoFiltro("Sobel Y", "Resposta do operador de Sobel apenas no eixo Y."),
    EspecificacaoFiltro("High-boost", "Realce por alto reforco."),
    EspecificacaoFiltro("Filtro livre", "Mascara 3x3 definida pelo usuario."),
]


# mascaras base: ficam centralizadas em 3x3 para combinar com a visualizacao da interface
MASCARA_MEDIA = np.ones((3, 3), dtype=np.float64) / 9.0
MASCARA_MEDIANA_REFERENCIA = np.ones((3, 3), dtype=np.float64)
MASCARA_PASSA_ALTAS_BASICO = np.array(
    [
        [-1, -1, -1],
        [-1, 8, -1],
        [-1, -1, -1],
    ],
    dtype=np.float64,
)

MASCARA_ROBERTS_X = np.array(
    [
        [0, 0, 0],
        [0, 1, 0],
        [0, -1, 0],
    ],
    dtype=np.float64,
)

MASCARA_ROBERTS_Y = np.array(
    [
        [0, 0, 0],
        [0, 1, -1],
        [0, 0, 0],
    ],
    dtype=np.float64,
)

MASCARA_ROBERTS_CRUZADO_X = np.array(
    [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, -1],
    ],
    dtype=np.float64,
)

MASCARA_ROBERTS_CRUZADO_Y = np.array(
    [
        [0, 0, 0],
        [0, 0, 1],
        [0, -1, 0],
    ],
    dtype=np.float64,
)

MASCARA_PREWITT_X = np.array(
    [
        [-1, -1, -1],
        [0, 0, 0],
        [1, 1, 1],
    ],
    dtype=np.float64,
)

MASCARA_PREWITT_Y = np.array(
    [
        [-1, 0, 1],
        [-1, 0, 1],
        [-1, 0, 1],
    ],
    dtype=np.float64,
)

MASCARA_SOBEL_X = np.array(
    [
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1],
    ],
    dtype=np.float64,
)

MASCARA_SOBEL_Y = np.array(
    [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1],
    ],
    dtype=np.float64,
)

MASCARA_FILTRO_LIVRE_INICIAL = np.array(
    [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ],
    dtype=np.float64,
)

MASCARAS_VISUAIS_PADRAO = {
    "Filtro da media": MASCARA_MEDIA,
    "Filtro da mediana": MASCARA_MEDIANA_REFERENCIA,
    "Passa-altas basico": MASCARA_PASSA_ALTAS_BASICO,
    "Roberts": MASCARA_ROBERTS_X,
    "Roberts X": MASCARA_ROBERTS_X,
    "Roberts Y": MASCARA_ROBERTS_Y,
    "Roberts cruzado": MASCARA_ROBERTS_CRUZADO_X,
    "Roberts cruzado X": MASCARA_ROBERTS_CRUZADO_X,
    "Roberts cruzado Y": MASCARA_ROBERTS_CRUZADO_Y,
    "Prewitt": MASCARA_PREWITT_X,
    "Prewitt X": MASCARA_PREWITT_X,
    "Prewitt Y": MASCARA_PREWITT_Y,
    "Sobel": MASCARA_SOBEL_X,
    "Sobel X": MASCARA_SOBEL_X,
    "Sobel Y": MASCARA_SOBEL_Y,
    "Filtro livre": MASCARA_FILTRO_LIVRE_INICIAL,
}


def _combinar_gradientes(resposta_x: np.ndarray, resposta_y: np.ndarray) -> np.ndarray:
    magnitude = np.abs(resposta_x) + np.abs(resposta_y)
    return limitar_uint8(magnitude)


def _aplicar_gradiente_unico(matriz: np.ndarray, mascara: np.ndarray) -> np.ndarray:
    # bordas: usa o valor absoluto para preservar a resposta do eixo escolhido
    resposta = aplicar_correlacao(matriz, mascara)
    return limitar_uint8(np.abs(resposta))


def filtro_media(matriz: np.ndarray) -> np.ndarray:
    return limitar_uint8(aplicar_correlacao(matriz, MASCARA_MEDIA))


def filtro_mediana(matriz: np.ndarray) -> np.ndarray:
    return limitar_uint8(aplicar_mediana(matriz, tamanho=3))


def filtro_passa_altas_basico(matriz: np.ndarray) -> np.ndarray:
    resposta = aplicar_correlacao(matriz, MASCARA_PASSA_ALTAS_BASICO)
    return limitar_uint8(resposta)


def operador_roberts(matriz: np.ndarray) -> np.ndarray:
    # combinacao: soma as respostas absolutas dos dois eixos classicos do Roberts
    resposta_x = aplicar_correlacao(matriz, MASCARA_ROBERTS_X)
    resposta_y = aplicar_correlacao(matriz, MASCARA_ROBERTS_Y)
    return _combinar_gradientes(resposta_x, resposta_y)


def operador_roberts_x(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_ROBERTS_X)


def operador_roberts_y(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_ROBERTS_Y)


def operador_roberts_cruzado(matriz: np.ndarray) -> np.ndarray:
    resposta_x = aplicar_correlacao(matriz, MASCARA_ROBERTS_CRUZADO_X)
    resposta_y = aplicar_correlacao(matriz, MASCARA_ROBERTS_CRUZADO_Y)
    return _combinar_gradientes(resposta_x, resposta_y)


def operador_roberts_cruzado_x(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_ROBERTS_CRUZADO_X)


def operador_roberts_cruzado_y(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_ROBERTS_CRUZADO_Y)


def operador_prewitt(matriz: np.ndarray) -> np.ndarray:
    resposta_x = aplicar_correlacao(matriz, MASCARA_PREWITT_X)
    resposta_y = aplicar_correlacao(matriz, MASCARA_PREWITT_Y)
    return _combinar_gradientes(resposta_x, resposta_y)


def operador_prewitt_x(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_PREWITT_X)


def operador_prewitt_y(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_PREWITT_Y)


def operador_sobel(matriz: np.ndarray) -> np.ndarray:
    resposta_x = aplicar_correlacao(matriz, MASCARA_SOBEL_X)
    resposta_y = aplicar_correlacao(matriz, MASCARA_SOBEL_Y)
    return _combinar_gradientes(resposta_x, resposta_y)


def operador_sobel_x(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_SOBEL_X)


def operador_sobel_y(matriz: np.ndarray) -> np.ndarray:
    return _aplicar_gradiente_unico(matriz, MASCARA_SOBEL_Y)


def filtragem_high_boost(matriz: np.ndarray, fator_realce: float = 1.2) -> np.ndarray:
    matriz_float = np.asarray(matriz, dtype=np.float64)
    suavizada = filtro_media(matriz_float).astype(np.float64)
    # formula do livro: A * original - passa-baixas
    reforcada = fator_realce * matriz_float - suavizada
    return limitar_uint8(reforcada)


def obter_mascara_high_boost_visual(fator_realce: float = 1.2) -> np.ndarray:
    centro = fator_realce - (1.0 / 9.0)
    return np.array(
        [
            [-1 / 9, -1 / 9, -1 / 9],
            [-1 / 9, centro, -1 / 9],
            [-1 / 9, -1 / 9, -1 / 9],
        ],
        dtype=np.float64,
    )


def obter_mascara_visual_filtro(nome_filtro: str, fator_realce: float = 1.2) -> np.ndarray:
    if nome_filtro == "High-boost":
        return obter_mascara_high_boost_visual(fator_realce)
    if nome_filtro not in MASCARAS_VISUAIS_PADRAO:
        raise ValueError(f"Filtro '{nome_filtro}' nao reconhecido para visualizacao.")
    return np.asarray(MASCARAS_VISUAIS_PADRAO[nome_filtro], dtype=np.float64).copy()


def aplicar_filtro_livre(matriz: np.ndarray, mascara_personalizada: np.ndarray) -> np.ndarray:
    return limitar_uint8(aplicar_correlacao(matriz, mascara_personalizada))


def aplicar_filtro_por_nome(
    nome_filtro: str,
    matriz: np.ndarray,
    *,
    fator_realce: float = 1.2,
    mascara_personalizada: np.ndarray | None = None,
) -> np.ndarray:
    if nome_filtro == "Filtro da media":
        return filtro_media(matriz)
    if nome_filtro == "Filtro da mediana":
        return filtro_mediana(matriz)
    if nome_filtro == "Passa-altas basico":
        return filtro_passa_altas_basico(matriz)
    if nome_filtro == "Roberts":
        return operador_roberts(matriz)
    if nome_filtro == "Roberts X":
        return operador_roberts_x(matriz)
    if nome_filtro == "Roberts Y":
        return operador_roberts_y(matriz)
    if nome_filtro == "Roberts cruzado":
        return operador_roberts_cruzado(matriz)
    if nome_filtro == "Roberts cruzado X":
        return operador_roberts_cruzado_x(matriz)
    if nome_filtro == "Roberts cruzado Y":
        return operador_roberts_cruzado_y(matriz)
    if nome_filtro == "Prewitt":
        return operador_prewitt(matriz)
    if nome_filtro == "Prewitt X":
        return operador_prewitt_x(matriz)
    if nome_filtro == "Prewitt Y":
        return operador_prewitt_y(matriz)
    if nome_filtro == "Sobel":
        return operador_sobel(matriz)
    if nome_filtro == "Sobel X":
        return operador_sobel_x(matriz)
    if nome_filtro == "Sobel Y":
        return operador_sobel_y(matriz)
    if nome_filtro == "High-boost":
        return filtragem_high_boost(matriz, fator_realce=fator_realce)
    if nome_filtro == "Filtro livre":
        if mascara_personalizada is None:
            raise ValueError("Informe uma mascara 3x3 para o filtro livre.")
        return aplicar_filtro_livre(matriz, mascara_personalizada)
    raise ValueError(f"Filtro '{nome_filtro}' nao reconhecido.")
