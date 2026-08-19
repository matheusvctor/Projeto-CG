from __future__ import annotations

import math

import numpy as np


def _translacao(dx: float, dy: float) -> np.ndarray:
    return np.array([[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]], dtype=np.float64)


def _centro_imagem(largura: int, altura: int) -> tuple[float, float]:
    return (largura - 1) / 2.0, (altura - 1) / 2.0


def _em_torno_do_centro(matriz_base: np.ndarray, largura: int, altura: int) -> np.ndarray:
    centro_x, centro_y = _centro_imagem(largura, altura)
    return _translacao(centro_x, centro_y) @ matriz_base @ _translacao(-centro_x, -centro_y)


def aplicar_transformacao_afim(
    matriz: np.ndarray,
    matriz_afim: np.ndarray,
    *,
    expandir: bool = True,
    valor_fundo: int = 0,
) -> np.ndarray:
    """Aplica uma transformação geométrica afim 2D usando MAPEAMENTO INVERSO.

    Pergunta do professor: "Por que usamos Mapeamento Inverso (Inverse Mapping) em vez do Direto (Forward)?"
    Resposta:
    - Se usássemos Mapeamento Direto (varrer a imagem de entrada e calcular onde cada pixel cai na saída),
      haveria 'buracos' e 'descontinuidades' (aliasing/gaps) na imagem de saída porque as coordenadas
      transformadas caem em posições fracionárias não contíguas.
    - Com o MAPEAMENTO INVERSO, nós varremos CADA pixel (x', y') da imagem de SAÍDA, multiplicamos pela
      matriz INVERSA T^{-1} para encontrar as coordenadas originais (x, y), e interpolamos o valor.
      Isso garante que NENHUM pixel da saída fique vazio!
    """
    imagem = np.asarray(matriz, dtype=np.uint8)
    altura, largura = imagem.shape

    cantos = np.array(
        [
            [0, 0, 1],
            [largura - 1, 0, 1],
            [0, altura - 1, 1],
            [largura - 1, altura - 1, 1],
        ],
        dtype=np.float64,
    )
    transformados = (matriz_afim @ cantos.T).T[:, :2]

    if expandir:
        minimo_x = float(np.floor(transformados[:, 0].min()))
        minimo_y = float(np.floor(transformados[:, 1].min()))
        maximo_x = float(np.ceil(transformados[:, 0].max()))
        maximo_y = float(np.ceil(transformados[:, 1].max()))
        nova_largura = int(maximo_x - minimo_x + 1)
        nova_altura = int(maximo_y - minimo_y + 1)
        ajuste = _translacao(-minimo_x, -minimo_y)
        matriz_saida = ajuste @ matriz_afim
    else:
        nova_largura = largura
        nova_altura = altura
        matriz_saida = matriz_afim

    inversa = np.linalg.inv(matriz_saida)
    resultado = np.full((nova_altura, nova_largura), valor_fundo, dtype=np.uint8)

    coordenadas_y, coordenadas_x = np.indices((nova_altura, nova_largura))
    destino = np.stack(
        [coordenadas_x.ravel(), coordenadas_y.ravel(), np.ones(coordenadas_x.size)],
        axis=0,
    )
    origem = inversa @ destino
    origem_x = np.rint(origem[0]).astype(int)
    origem_y = np.rint(origem[1]).astype(int)

    validos = (
        (origem_x >= 0)
        & (origem_x < largura)
        & (origem_y >= 0)
        & (origem_y < altura)
    )

    plano = resultado.ravel()
    plano[validos] = imagem[origem_y[validos], origem_x[validos]]
    return resultado


def escalar(matriz: np.ndarray, fator_x: float, fator_y: float) -> np.ndarray:
    altura, largura = matriz.shape
    matriz_base = np.array(
        [
            [fator_x, 0.0, 0.0],
            [0.0, fator_y, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    return aplicar_transformacao_afim(matriz, _em_torno_do_centro(matriz_base, largura, altura))


def transladar(matriz: np.ndarray, deslocamento_x: float, deslocamento_y: float) -> np.ndarray:
    # translacao cartesiana: dy positivo sobe; no raster o eixo y cresce para baixo
    return aplicar_transformacao_afim(
        matriz,
        _translacao(deslocamento_x, -deslocamento_y),
        expandir=False,
        valor_fundo=0,
    )


def rotacionar(matriz: np.ndarray, angulo_graus: float) -> np.ndarray:
    altura, largura = matriz.shape
    # rotacao cartesiana: angulo positivo gira no sentido anti-horario
    angulo_radianos = math.radians(-angulo_graus)
    cosseno = math.cos(angulo_radianos)
    seno = math.sin(angulo_radianos)
    matriz_base = np.array(
        [
            [cosseno, -seno, 0.0],
            [seno, cosseno, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    return aplicar_transformacao_afim(matriz, _em_torno_do_centro(matriz_base, largura, altura))


def refletir(matriz: np.ndarray, eixo: str) -> np.ndarray:
    altura, largura = matriz.shape
    if eixo == "Horizontal":
        matriz_base = np.array([[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    elif eixo == "Vertical":
        matriz_base = np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]])
    elif eixo == "Ambos":
        matriz_base = np.array([[-1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]])
    else:
        raise ValueError(f"Eixo de reflexao '{eixo}' nao reconhecido.")
    return aplicar_transformacao_afim(matriz, _em_torno_do_centro(matriz_base, largura, altura))


def cisalhar(matriz: np.ndarray, fator_x: float, fator_y: float) -> np.ndarray:
    altura, largura = matriz.shape
    # cisalhamento cartesiano: compensa o eixo y invertido da imagem
    matriz_cisalhamento_x = np.array(
        [
            [1.0, -fator_x, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    matriz_cisalhamento_y = np.array(
        [
            [1.0, 0.0, 0.0],
            [-fator_y, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    # arnold: usa a fatoracao linear do gato; aqui mantemos a semantica afim sem mod 1
    matriz_base = matriz_cisalhamento_y @ matriz_cisalhamento_x
    return aplicar_transformacao_afim(matriz, _em_torno_do_centro(matriz_base, largura, altura))
