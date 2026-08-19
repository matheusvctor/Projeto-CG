from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laboratorio_imagens.core.filtros_espaciais import (
    filtro_media,
    filtro_mediana,
    filtragem_high_boost,
    operador_prewitt,
    operador_sobel,
)
from laboratorio_imagens.core.histograma import equalizar_histograma
from laboratorio_imagens.core.io_netpbm import carregar_imagem, criar_imagem, salvar_imagem
from laboratorio_imagens.core.operacoes_morfologicas import (
    ELEMENTOS_ESTRUTURANTES,
    MASCARAS_HIT_OR_MISS,
    abertura_binaria,
    contorno_interno_binario,
    dilatacao_binaria,
    erosao_binaria,
    fechamento_binaria,
    hit_or_miss,
)
from laboratorio_imagens.core.operacoes_pixel import (
    divisao,
    multiplicacao,
    operacao_and,
    operacao_not,
    operacao_or,
    operacao_xor,
    soma,
    subtracao,
)
from laboratorio_imagens.core.transformacoes_geometricas import (
    cisalhar,
    escalar,
    refletir,
    rotacionar,
    transladar,
)
from laboratorio_imagens.core.transformacoes_intensidade import transformacao_linear
from laboratorio_imagens.core.utilidades_matriz import limiarizar_pela_media


PASTA_EXEMPLOS = ROOT / "assets" / "exemplos"
PASTA_SAIDA = ROOT / "resultados_livro"


def _carregar(nome_arquivo: str) -> np.ndarray:
    return carregar_imagem(PASTA_EXEMPLOS / nome_arquivo).matriz


def _salvar(nome_arquivo: str, matriz: np.ndarray, *, binaria: bool = False) -> Path:
    # saida: salva em NetPBM para manter compatibilidade com o restante do projeto
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    extensao = ".pbm" if binaria else ".pgm"
    formato = "P1" if binaria else "P5"
    caminho = PASTA_SAIDA / f"{nome_arquivo}{extensao}"
    imagem = criar_imagem(matriz, nome=nome_arquivo, binaria=binaria)
    salvar_imagem(imagem, caminho, formato=formato)
    return caminho


def _adicionar_ruido_sal_pimenta(matriz: np.ndarray, proporcao: float = 0.08, *, semente: int = 7) -> np.ndarray:
    # ruido: usa semente fixa para deixar o relatorio reproduzivel
    rng = np.random.default_rng(semente)
    resultado = np.asarray(matriz, dtype=np.uint8).copy()
    quantidade = int(resultado.size * proporcao)
    indices = rng.choice(resultado.size, size=quantidade, replace=False)
    metade = quantidade // 2
    plano = resultado.reshape(-1)
    plano[indices[:metade]] = 0
    plano[indices[metade:]] = 255
    return resultado


def _adicionar_ruido_gaussiano(matriz: np.ndarray, sigma: float = 18.0, *, semente: int = 11) -> np.ndarray:
    rng = np.random.default_rng(semente)
    ruido = rng.normal(loc=0.0, scale=sigma, size=matriz.shape)
    return np.clip(np.rint(np.asarray(matriz, dtype=np.float64) + ruido), 0, 255).astype(np.uint8)


def _ampliar_binaria(matriz: np.ndarray, fator: int = 16) -> np.ndarray:
    bloco = np.ones((fator, fator), dtype=np.uint8)
    return np.kron(np.where(np.asarray(matriz) > 0, 255, 0).astype(np.uint8), bloco)


def gerar_operacoes() -> list[Path]:
    caminhos: list[Path] = []
    imagem_a = _carregar("lena.pgm")
    imagem_b = _carregar("airplane.pgm")

    caminhos.append(_salvar("operacoes_entrada_a_lena", imagem_a))
    caminhos.append(_salvar("operacoes_entrada_b_airplane", imagem_b))
    caminhos.append(_salvar("operacoes_soma_normalizada", soma(imagem_a, imagem_b, pos_processamento="Normalizacao")))
    caminhos.append(_salvar("operacoes_subtracao_normalizada", subtracao(imagem_a, imagem_b, pos_processamento="Normalizacao")))
    caminhos.append(_salvar("operacoes_multiplicacao_normalizada", multiplicacao(imagem_a, imagem_b, pos_processamento="Normalizacao")))
    caminhos.append(_salvar("operacoes_divisao_normalizada", divisao(imagem_a, imagem_b, pos_processamento="Normalizacao")))

    binaria_a = limiarizar_pela_media(imagem_a)
    binaria_b = limiarizar_pela_media(imagem_b)
    caminhos.append(_salvar("operacoes_binaria_a", binaria_a, binaria=True))
    caminhos.append(_salvar("operacoes_binaria_b", binaria_b, binaria=True))
    caminhos.append(_salvar("operacoes_and", operacao_and(binaria_a, binaria_b), binaria=True))
    caminhos.append(_salvar("operacoes_or", operacao_or(binaria_a, binaria_b), binaria=True))
    caminhos.append(_salvar("operacoes_xor", operacao_xor(binaria_a, binaria_b), binaria=True))
    caminhos.append(_salvar("operacoes_not_a", operacao_not(binaria_a), binaria=True))
    return caminhos


def gerar_histograma() -> list[Path]:
    caminhos: list[Path] = []
    imagem = _carregar("airplane.pgm")
    baixo_contraste = transformacao_linear(imagem, 0.35, 75.0)
    equalizada, _, _ = equalizar_histograma(baixo_contraste)

    caminhos.append(_salvar("histograma_original_airplane", imagem))
    caminhos.append(_salvar("histograma_baixo_contraste", baixo_contraste))
    caminhos.append(_salvar("histograma_equalizada", equalizada))
    return caminhos


def gerar_filtros() -> list[Path]:
    caminhos: list[Path] = []
    imagem = _carregar("lena.pgm")
    ruido_sal_pimenta = _adicionar_ruido_sal_pimenta(imagem)
    ruido_gaussiano = _adicionar_ruido_gaussiano(imagem)

    caminhos.append(_salvar("filtros_original_lena", imagem))
    caminhos.append(_salvar("filtros_ruido_sal_pimenta", ruido_sal_pimenta))
    caminhos.append(_salvar("filtros_mediana_sal_pimenta", filtro_mediana(ruido_sal_pimenta)))
    caminhos.append(_salvar("filtros_media_sal_pimenta", filtro_media(ruido_sal_pimenta)))
    caminhos.append(_salvar("filtros_ruido_gaussiano", ruido_gaussiano))
    caminhos.append(_salvar("filtros_mediana_gaussiano", filtro_mediana(ruido_gaussiano)))
    caminhos.append(_salvar("filtros_media_gaussiano", filtro_media(ruido_gaussiano)))
    caminhos.append(_salvar("filtros_prewitt", operador_prewitt(imagem)))
    caminhos.append(_salvar("filtros_sobel", operador_sobel(imagem)))
    caminhos.append(_salvar("filtros_high_boost_a_1_10", filtragem_high_boost(imagem, fator_realce=1.10)))
    caminhos.append(_salvar("filtros_high_boost_a_1_15", filtragem_high_boost(imagem, fator_realce=1.15)))
    caminhos.append(_salvar("filtros_high_boost_a_1_20", filtragem_high_boost(imagem, fator_realce=1.20)))
    return caminhos


def gerar_morfologia() -> list[Path]:
    caminhos: list[Path] = []
    letra_j = _carregar("letra_j.pbm")
    letra_j_ampliada = _ampliar_binaria(letra_j)
    elemento = ELEMENTOS_ESTRUTURANTES["Quadrado 3x3"]

    caminhos.append(_salvar("morfologia_entrada_letra_j", letra_j_ampliada, binaria=True))
    caminhos.append(_salvar("morfologia_dilatacao", dilatacao_binaria(letra_j_ampliada, elemento), binaria=True))
    caminhos.append(_salvar("morfologia_erosao", erosao_binaria(letra_j_ampliada, elemento), binaria=True))
    caminhos.append(_salvar("morfologia_abertura", abertura_binaria(letra_j_ampliada, elemento), binaria=True))
    caminhos.append(_salvar("morfologia_fechamento", fechamento_binaria(letra_j_ampliada, elemento), binaria=True))
    caminhos.append(
        _salvar(
            "morfologia_hit_or_miss",
            hit_or_miss(letra_j_ampliada, MASCARAS_HIT_OR_MISS["Ponto isolado"]),
            binaria=True,
        )
    )
    caminhos.append(_salvar("morfologia_contorno_interno", contorno_interno_binario(letra_j_ampliada, elemento), binaria=True))
    return caminhos


def gerar_geometria() -> list[Path]:
    caminhos: list[Path] = []
    imagem = _carregar("airplane.pgm")

    caminhos.append(_salvar("geometria_original_airplane", imagem))
    caminhos.append(_salvar("geometria_escala", escalar(imagem, 1.4, 1.2)))
    caminhos.append(_salvar("geometria_translacao", transladar(imagem, 40.0, 20.0)))
    caminhos.append(_salvar("geometria_rotacao_30_graus", rotacionar(imagem, 30.0)))
    caminhos.append(_salvar("geometria_reflexao_horizontal", refletir(imagem, "Horizontal")))
    caminhos.append(_salvar("geometria_cisalhamento_arnold", cisalhar(imagem, 1.0, 1.0)))
    return caminhos


def main() -> None:
    caminhos_gerados: list[Path] = []
    caminhos_gerados.extend(gerar_operacoes())
    caminhos_gerados.extend(gerar_histograma())
    caminhos_gerados.extend(gerar_filtros())
    caminhos_gerados.extend(gerar_morfologia())
    caminhos_gerados.extend(gerar_geometria())

    print(f"{len(caminhos_gerados)} arquivos gerados em {PASTA_SAIDA}")
    for caminho in caminhos_gerados:
        print(caminho.relative_to(ROOT))


if __name__ == "__main__":
    main()
