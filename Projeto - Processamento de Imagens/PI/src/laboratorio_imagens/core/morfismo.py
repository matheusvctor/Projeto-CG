from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from PIL import Image
from scipy.spatial import Delaunay


@dataclass(slots=True)
class ResultadoMorfismo:
    frame: np.ndarray
    triangulos: np.ndarray


@dataclass(slots=True)
class PreparacaoMorfismo:
    base_inicial: np.ndarray
    base_final: np.ndarray
    todos_iniciais: np.ndarray
    todos_finais: np.ndarray
    simplices: np.ndarray


def _redimensionar_vizinho_mais_proximo(matriz: np.ndarray, novo_formato: tuple[int, int]) -> np.ndarray:
    nova_altura, nova_largura = novo_formato
    altura, largura = matriz.shape
    coordenadas_y = np.linspace(0, altura - 1, nova_altura)
    coordenadas_x = np.linspace(0, largura - 1, nova_largura)
    indices_y = np.rint(coordenadas_y).astype(int)
    indices_x = np.rint(coordenadas_x).astype(int)
    return matriz[np.ix_(indices_y, indices_x)]


def redimensionar_para_limite(matriz: np.ndarray, limite_dimensao: int | None) -> np.ndarray:
    if limite_dimensao is None or limite_dimensao <= 0:
        return matriz.astype(np.uint8)

    altura, largura = matriz.shape
    escala = min(1.0, float(limite_dimensao) / max(altura, largura))
    if escala >= 1.0:
        return matriz.astype(np.uint8)

    nova_altura = max(1, int(round(altura * escala)))
    nova_largura = max(1, int(round(largura * escala)))
    return _redimensionar_vizinho_mais_proximo(matriz.astype(np.uint8), (nova_altura, nova_largura))


def ajustar_tamanho_para_morfismo(
    imagem_inicial: np.ndarray,
    imagem_final: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if imagem_inicial.shape == imagem_final.shape:
        return imagem_inicial.astype(np.uint8), imagem_final.astype(np.uint8)
    return imagem_inicial.astype(np.uint8), _redimensionar_vizinho_mais_proximo(
        imagem_final.astype(np.uint8),
        imagem_inicial.shape,
    )


def _pontos_de_contorno(largura: int, altura: int) -> np.ndarray:
    return np.array(
        [
            [0, 0],
            [largura - 1, 0],
            [largura - 1, altura - 1],
            [0, altura - 1],
            [largura // 2, 0],
            [largura - 1, altura // 2],
            [largura // 2, altura - 1],
            [0, altura // 2],
        ],
        dtype=np.float64,
    )


def _matriz_baricentrica(triangulo: np.ndarray) -> np.ndarray:
    return np.array(
        [
            [triangulo[0, 0], triangulo[1, 0], triangulo[2, 0]],
            [triangulo[0, 1], triangulo[1, 1], triangulo[2, 1]],
            [1.0, 1.0, 1.0],
        ],
        dtype=np.float64,
    )


def _amostrar_vizinho_mais_proximo_vetorizado(matriz: np.ndarray, pontos: np.ndarray) -> np.ndarray:
    indices_y = np.clip(np.rint(pontos[:, 1]).astype(int), 0, matriz.shape[0] - 1)
    indices_x = np.clip(np.rint(pontos[:, 0]).astype(int), 0, matriz.shape[1] - 1)
    return matriz[indices_y, indices_x]


def preparar_morfismo(
    imagem_inicial: np.ndarray,
    imagem_final: np.ndarray,
    pontos_iniciais: list[tuple[float, float]],
    pontos_finais: list[tuple[float, float]],
) -> PreparacaoMorfismo:
    if Delaunay is None:
        raise RuntimeError("O modulo scipy nao esta disponivel para executar o morfismo.")

    base_inicial, base_final = ajustar_tamanho_para_morfismo(imagem_inicial, imagem_final)
    altura, largura = base_inicial.shape

    if len(pontos_iniciais) != len(pontos_finais):
        raise ValueError("A quantidade de pontos correspondentes precisa ser igual nas duas imagens.")

    controle_inicial = np.array(pontos_iniciais, dtype=np.float64) if pontos_iniciais else np.empty((0, 2))
    controle_final = np.array(pontos_finais, dtype=np.float64) if pontos_finais else np.empty((0, 2))

    contorno = _pontos_de_contorno(largura, altura)
    todos_iniciais = np.vstack([controle_inicial, contorno])
    todos_finais = np.vstack([controle_final, contorno])

    # malha-base: usa a forma media para reaproveitar a triangulacao durante toda a animacao
    forma_media = 0.5 * (todos_iniciais + todos_finais)
    simplices = Delaunay(forma_media).simplices
    return PreparacaoMorfismo(
        base_inicial=base_inicial,
        base_final=base_final,
        todos_iniciais=todos_iniciais,
        todos_finais=todos_finais,
        simplices=simplices,
    )


def gerar_frame_preparado(preparacao: PreparacaoMorfismo, tempo: float) -> ResultadoMorfismo:
    tempo_limitado = float(np.clip(tempo, 0.0, 1.0))
    altura, largura = preparacao.base_inicial.shape
    todos_intermediarios = (
        (1.0 - tempo_limitado) * preparacao.todos_iniciais + tempo_limitado * preparacao.todos_finais
    )

    resultado = np.zeros((altura, largura), dtype=np.uint8)

    for indices_triangulo in preparacao.simplices:
        triangulo_intermediario = todos_intermediarios[indices_triangulo]
        triangulo_inicial = preparacao.todos_iniciais[indices_triangulo]
        triangulo_final = preparacao.todos_finais[indices_triangulo]

        minimo_x = max(int(np.floor(np.min(triangulo_intermediario[:, 0]))), 0)
        maximo_x = min(int(np.ceil(np.max(triangulo_intermediario[:, 0]))), largura - 1)
        minimo_y = max(int(np.floor(np.min(triangulo_intermediario[:, 1]))), 0)
        maximo_y = min(int(np.ceil(np.max(triangulo_intermediario[:, 1]))), altura - 1)
        if minimo_x > maximo_x or minimo_y > maximo_y:
            continue

        grade_y, grade_x = np.mgrid[minimo_y : maximo_y + 1, minimo_x : maximo_x + 1]
        pontos_grade = np.vstack(
            [
                grade_x.reshape(-1).astype(np.float64),
                grade_y.reshape(-1).astype(np.float64),
                np.ones(grade_x.size, dtype=np.float64),
            ]
        )

        try:
            inversa = np.linalg.inv(_matriz_baricentrica(triangulo_intermediario))
        except np.linalg.LinAlgError:
            continue

        pesos = inversa @ pontos_grade
        mascara = np.all((pesos >= -1e-5) & (pesos <= 1.0 + 1e-5), axis=0)
        if not np.any(mascara):
            continue

        pesos_validos = pesos[:, mascara].T
        pontos_destino_x = grade_x.reshape(-1)[mascara]
        pontos_destino_y = grade_y.reshape(-1)[mascara]

        pontos_iniciais = pesos_validos @ triangulo_inicial
        pontos_finais = pesos_validos @ triangulo_final

        valores_iniciais = _amostrar_vizinho_mais_proximo_vetorizado(preparacao.base_inicial, pontos_iniciais)
        valores_finais = _amostrar_vizinho_mais_proximo_vetorizado(preparacao.base_final, pontos_finais)
        mistura = np.clip(
            (1.0 - tempo_limitado) * valores_iniciais.astype(np.float64)
            + tempo_limitado * valores_finais.astype(np.float64),
            0,
            255,
        ).astype(np.uint8)
        resultado[pontos_destino_y, pontos_destino_x] = mistura

    return ResultadoMorfismo(frame=resultado, triangulos=preparacao.simplices)


def gerar_frame_morfado(
    imagem_inicial: np.ndarray,
    imagem_final: np.ndarray,
    pontos_iniciais: list[tuple[float, float]],
    pontos_finais: list[tuple[float, float]],
    tempo: float,
    *,
    preparacao: PreparacaoMorfismo | None = None,
) -> ResultadoMorfismo:
    if preparacao is None:
        preparacao = preparar_morfismo(imagem_inicial, imagem_final, pontos_iniciais, pontos_finais)
    return gerar_frame_preparado(preparacao, tempo)


def gerar_sequencia_preparada(preparacao: PreparacaoMorfismo, tempos: list[float]) -> list[np.ndarray]:
    return [gerar_frame_preparado(preparacao, tempo).frame for tempo in tempos]


def gerar_sequencia_morfismo(
    imagem_inicial: np.ndarray,
    imagem_final: np.ndarray,
    pontos_iniciais: list[tuple[float, float]],
    pontos_finais: list[tuple[float, float]],
    tempos: list[float],
    *,
    preparacao: PreparacaoMorfismo | None = None,
) -> list[np.ndarray]:
    if preparacao is None:
        preparacao = preparar_morfismo(imagem_inicial, imagem_final, pontos_iniciais, pontos_finais)
    return gerar_sequencia_preparada(preparacao, tempos)


def gerar_tempos_uniformes(total_quadros: int) -> list[float]:
    if total_quadros <= 1:
        return [0.0]
    return [indice / (total_quadros - 1) for indice in range(total_quadros)]


def salvar_gif_animado(
    frames: list[np.ndarray],
    caminho_saida: str | Path,
    *,
    duracao_ms: int = 70,
    repeticoes_extremos: int = 2,
) -> Path:
    if Image is None:
        raise RuntimeError("O modulo Pillow nao esta disponivel para exportar a animacao.")
    if not frames:
        raise ValueError("A lista de frames da animacao nao pode ser vazia.")

    imagens = [Image.fromarray(np.asarray(frame, dtype=np.uint8), mode="L") for frame in frames]

    if repeticoes_extremos > 1 and len(imagens) >= 2:
        sequencia = [imagens[0].copy() for _ in range(repeticoes_extremos)]
        sequencia.extend(imagem.copy() for imagem in imagens[1:-1])
        sequencia.extend([imagens[-1].copy() for _ in range(repeticoes_extremos)])
    else:
        sequencia = [imagem.copy() for imagem in imagens]

    caminho = Path(caminho_saida)
    primeira = sequencia[0]
    restantes = sequencia[1:]
    primeira.save(
        caminho,
        save_all=True,
        append_images=restantes,
        duration=max(20, int(duracao_ms)),
        loop=0,
        optimize=True,
        disposal=2,
    )
    return caminho


def contar_mudancas_entre_imagens(imagem_a: np.ndarray, imagem_b: np.ndarray) -> int:
    base_a, base_b = ajustar_tamanho_para_morfismo(imagem_a, imagem_b)
    return int(np.count_nonzero(base_a != base_b))
