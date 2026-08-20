from __future__ import annotations

import numpy as np

from laboratorio_imagens.core.utilidades_matriz import (
    ajustar_para_mesmo_tamanho,
    limitar_uint8,
    normalizar_uint8,
)


POS_PROCESSAMENTOS = ("Truncamento", "Normalizacao")


def _ajustar_duas_matrizes(matriz_a: np.ndarray, matriz_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    primeira, segunda = ajustar_para_mesmo_tamanho(matriz_a, matriz_b)
    return primeira.astype(np.float64), segunda.astype(np.float64)


def _finalizar_resultado(matriz: np.ndarray, pos_processamento: str) -> np.ndarray:
    if pos_processamento == "Normalizacao":
        return normalizar_uint8(matriz)
    return limitar_uint8(matriz)


def soma(matriz_a: np.ndarray, matriz_b: np.ndarray, *, pos_processamento: str = "Truncamento") -> np.ndarray:
    """Realiza a soma pontual entre duas imagens: C(x,y) = A(x,y) + B(x,y).
    
    Pós-processamentos:
        - Truncamento: limita valores superiores a 255 (clamp).
        - Normalização: mapeia [min, max] linearmente para [0, 255].
    """
    primeira, segunda = _ajustar_duas_matrizes(matriz_a, matriz_b)
    return _finalizar_resultado(primeira + segunda, pos_processamento)


def subtracao(
    matriz_a: np.ndarray,
    matriz_b: np.ndarray,
    *,
    pos_processamento: str = "Truncamento",
) -> np.ndarray:
    """Realiza a subtração pontual: C(x,y) = A(x,y) - B(x,y). Usado para detecção de mudanças e diferenças."""
    primeira, segunda = _ajustar_duas_matrizes(matriz_a, matriz_b)
    return _finalizar_resultado(primeira - segunda, pos_processamento)


def multiplicacao(
    matriz_a: np.ndarray,
    matriz_b: np.ndarray,
    *,
    pos_processamento: str = "Normalizacao",
) -> np.ndarray:
    """Realiza a multiplicação pontual: C(x,y) = A(x,y) * B(x,y). Usado para mascaramento e sombreamento."""
    primeira, segunda = _ajustar_duas_matrizes(matriz_a, matriz_b)
    return _finalizar_resultado(primeira * segunda, pos_processamento)


def divisao(
    matriz_a: np.ndarray,
    matriz_b: np.ndarray,
    *,
    pos_processamento: str = "Normalizacao",
) -> np.ndarray:
    """Realiza a divisão pontual com proteção contra divisão por zero: C(x,y) = A(x,y) / max(B(x,y), 1.0)."""
    primeira, segunda = _ajustar_duas_matrizes(matriz_a, matriz_b)
    divisor = np.where(segunda == 0, 1.0, segunda)
    resultado = primeira / divisor
    return _finalizar_resultado(resultado, pos_processamento)


def operacao_and(matriz_a: np.ndarray, matriz_b: np.ndarray) -> np.ndarray:
    """Executa a conjunção lógica bit a bit (AND bitwise) entre pixels correspondentes."""
    primeira, segunda = ajustar_para_mesmo_tamanho(matriz_a, matriz_b)
    return np.bitwise_and(primeira.astype(np.uint8), segunda.astype(np.uint8))


def operacao_or(matriz_a: np.ndarray, matriz_b: np.ndarray) -> np.ndarray:
    """Executa a disjunção lógica bit a bit (OR bitwise) entre pixels correspondentes."""
    primeira, segunda = ajustar_para_mesmo_tamanho(matriz_a, matriz_b)
    return np.bitwise_or(primeira.astype(np.uint8), segunda.astype(np.uint8))


def operacao_xor(matriz_a: np.ndarray, matriz_b: np.ndarray) -> np.ndarray:
    """Executa a disjunção exclusiva bit a bit (XOR bitwise) para realce de diferenças."""
    primeira, segunda = ajustar_para_mesmo_tamanho(matriz_a, matriz_b)
    return np.bitwise_xor(primeira.astype(np.uint8), segunda.astype(np.uint8))


def operacao_not(matriz: np.ndarray) -> np.ndarray:
    """Executa a negação lógica bit a bit (NOT bitwise / Complemento de 1): ~A."""
    return np.bitwise_not(np.asarray(matriz, dtype=np.uint8))


def aplicar_operacao_por_nome(
    nome_operacao: str,
    matriz_a: np.ndarray,
    matriz_b: np.ndarray | None = None,
    *,
    pos_processamento: str = "Truncamento",
) -> np.ndarray:
    if nome_operacao == "NOT":
        return operacao_not(matriz_a)

    if matriz_b is None:
        raise ValueError(f"Operacao '{nome_operacao}' exige duas imagens.")
    if nome_operacao == "Soma":
        return soma(matriz_a, matriz_b, pos_processamento=pos_processamento)
    if nome_operacao == "Subtracao":
        return subtracao(matriz_a, matriz_b, pos_processamento=pos_processamento)
    if nome_operacao == "Multiplicacao":
        return multiplicacao(matriz_a, matriz_b, pos_processamento=pos_processamento)
    if nome_operacao == "Divisao":
        return divisao(matriz_a, matriz_b, pos_processamento=pos_processamento)
    if nome_operacao == "AND":
        return operacao_and(matriz_a, matriz_b)
    if nome_operacao == "OR":
        return operacao_or(matriz_a, matriz_b)
    if nome_operacao == "XOR":
        return operacao_xor(matriz_a, matriz_b)
    raise ValueError(f"Operacao '{nome_operacao}' nao reconhecida.")
