from __future__ import annotations

import numpy as np


def calcular_histograma(matriz: np.ndarray) -> np.ndarray:
    """Calcula o histograma absoluto (contagem de ocorrência de cada intensidade [0, 255]).

    Pergunta do professor: "Como é calculado o histograma?"
    Resposta: É a distribuição de frequência absoluta dos níveis de cinza da imagem.
    np.bincount conta quantas vezes cada nível r_k (de 0 a 255) aparece na matriz.
    """
    valores = np.asarray(matriz, dtype=np.uint8).ravel()
    return np.bincount(valores, minlength=256)


def equalizar_histograma(matriz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Equaliza o histograma usando a Função de Distribuição Acumulada (CDF).

    Pergunta do professor: "Qual é a base matemática da equalização?"
    Resposta:
    1. Calcula a função densidade de probabilidade (PDF): p(r_k) = n_k / N (onde N é o total de pixels).
    2. Calcula a distribuição acumulada (CDF): s_k = T(r_k) = sum_{j=0}^{k} p(r_j).
    3. Multiplica pelo nível máximo (L - 1 = 255) e arredonda (np.floor / np.rint): s_k = floor(255 * CDF(r_k)).
    4. Usa essa tabela de mapeamento (Look-Up Table / LUT) para substituir os pixels originais: s_k = T[r_k].
    Isso 'espalha' o contraste da imagem de forma uniforme pelo espectro dinâmico.
    """
    imagem = np.asarray(matriz, dtype=np.uint8)
    histograma_original = calcular_histograma(imagem)
    total_pixels = imagem.size

    # 1. Probabilidade empírica (PDF)
    probabilidades = histograma_original / max(total_pixels, 1)

    # 2. Distribuição acumulada (CDF)
    distribuicao_acumulada = np.cumsum(probabilidades)

    # 3. Mapeamento para escala [0, 255]
    tabela = np.floor(255 * distribuicao_acumulada).astype(np.uint8)

    # 4. Aplicação direta na imagem através de indexação vetorial (Lookup Table)
    imagem_equalizada = tabela[imagem]
    histograma_equalizado = calcular_histograma(imagem_equalizada)

    return imagem_equalizada, histograma_original, histograma_equalizado
