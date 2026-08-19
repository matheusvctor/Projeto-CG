from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from laboratorio_imagens.core.io_netpbm import ImagemNetpbm, carregar_imagem, criar_imagem
from laboratorio_imagens.core.morfismo import redimensionar_para_limite


def _obter_pasta_assets_morfismo() -> Path:
    # Procura na pasta MEIPASS se compilado com PyInstaller
    if hasattr(sys, "_MEIPASS"):
        candidato = Path(sys._MEIPASS) / "assets" / "morfismo"
        if candidato.exists():
            return candidato

    # Procura relativo ao arquivo de código
    candidato = Path(__file__).resolve().parents[3] / "assets" / "morfismo"
    if candidato.exists():
        return candidato

    # Procura relativo ao diretório atual
    candidato = Path.cwd() / "assets" / "morfismo"
    if candidato.exists():
        return candidato

    # Procura dentro da subpasta PI
    candidato = Path.cwd() / "Projeto - Processamento de Imagens" / "PI" / "assets" / "morfismo"
    if candidato.exists():
        return candidato

    return Path(__file__).resolve().parents[3] / "assets" / "morfismo"


LIMITE_DIMENSAO_EXEMPLO = 320
TOTAL_QUADROS_GIF_EXEMPLO = 18
ATRASO_GIF_EXEMPLO_MS = 75

PONTOS_ADULTO_NORMALIZADOS = (
    (0.50, 0.18),  # Topo da cabeça
    (0.32, 0.28),  # Têmpora esquerda
    (0.68, 0.28),  # Têmpora direita
    (0.38, 0.37),  # Olho esquerdo
    (0.62, 0.37),  # Olho direito
    (0.50, 0.43),  # Ponte do nariz
    (0.50, 0.50),  # Ponta do nariz
    (0.35, 0.54),  # Bochecha esquerda
    (0.65, 0.54),  # Bochecha direita
    (0.42, 0.59),  # Canto esquerdo boca
    (0.58, 0.59),  # Canto direito boca
    (0.50, 0.64),  # Lábio inferior
    (0.50, 0.74),  # Queixo
)

PONTOS_CRIANCA_NORMALIZADOS = (
    (0.50, 0.17),  # Topo da cabeça
    (0.33, 0.26),  # Têmpora esquerda
    (0.67, 0.26),  # Têmpora direita
    (0.40, 0.35),  # Olho esquerdo
    (0.62, 0.35),  # Olho direito
    (0.51, 0.40),  # Ponte do nariz
    (0.51, 0.46),  # Ponta do nariz
    (0.36, 0.51),  # Bochecha esquerda
    (0.66, 0.51),  # Bochecha direita
    (0.43, 0.55),  # Canto esquerdo boca
    (0.58, 0.55),  # Canto direito boca
    (0.51, 0.60),  # Lábio inferior
    (0.51, 0.70),  # Queixo
)


@dataclass(slots=True, frozen=True)
class ExemploMorfismoCarregado:
    imagem_inicial: ImagemNetpbm
    imagem_final: ImagemNetpbm
    pontos_iniciais: list[tuple[float, float]]
    pontos_finais: list[tuple[float, float]]
    total_quadros_gif: int
    atraso_gif_ms: int


def _obter_caminhos_amostras() -> tuple[Path, Path]:
    pasta = _obter_pasta_assets_morfismo()
    caminho_inicial = pasta / "amostra_crianca.pgm"
    caminho_final = pasta / "amostra_adulto.pgm"
    return caminho_inicial, caminho_final


def exemplo_demonstrativo_disponivel() -> bool:
    inicial, final = _obter_caminhos_amostras()
    return inicial.exists() and final.exists()


# Alias de compatibilidade
exemplo_luiz_disponivel = exemplo_demonstrativo_disponivel


def _otimizar_imagem_exemplo(imagem: ImagemNetpbm, limite_dimensao: int) -> ImagemNetpbm:
    matriz_otimizada = redimensionar_para_limite(imagem.matriz, limite_dimensao)
    return criar_imagem(
        matriz_otimizada,
        nome=imagem.nome,
        caminho_origem=imagem.caminho_origem,
    )


def _converter_pontos_normalizados(
    largura: int,
    altura: int,
    pontos_normalizados: tuple[tuple[float, float], ...],
) -> list[tuple[float, float]]:
    return [(x * largura, y * altura) for x, y in pontos_normalizados]


def carregar_exemplo_demonstrativo(*, limite_dimensao: int = LIMITE_DIMENSAO_EXEMPLO) -> ExemploMorfismoCarregado:
    if not exemplo_demonstrativo_disponivel():
        raise FileNotFoundError("As imagens da amostra experimental não foram encontradas no diretório de assets.")

    caminho_inicial, caminho_final = _obter_caminhos_amostras()
    imagem_inicial = _otimizar_imagem_exemplo(carregar_imagem(caminho_inicial), limite_dimensao)
    imagem_final = _otimizar_imagem_exemplo(carregar_imagem(caminho_final), limite_dimensao)

    pontos_iniciais = _converter_pontos_normalizados(
        imagem_inicial.largura,
        imagem_inicial.altura,
        PONTOS_ADULTO_NORMALIZADOS,
    )
    pontos_finais = _converter_pontos_normalizados(
        imagem_final.largura,
        imagem_final.altura,
        PONTOS_CRIANCA_NORMALIZADOS,
    )

    return ExemploMorfismoCarregado(
        imagem_inicial=imagem_inicial,
        imagem_final=imagem_final,
        pontos_iniciais=pontos_iniciais,
        pontos_finais=pontos_finais,
        total_quadros_gif=TOTAL_QUADROS_GIF_EXEMPLO,
        atraso_gif_ms=ATRASO_GIF_EXEMPLO_MS,
    )


# Alias de compatibilidade
carregar_exemplo_luiz = carregar_exemplo_demonstrativo
