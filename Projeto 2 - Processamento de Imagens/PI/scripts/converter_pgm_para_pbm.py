from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from laboratorio_imagens.core.io_netpbm import carregar_imagem, criar_imagem, salvar_imagem
from laboratorio_imagens.core.utilidades_matriz import limiarizar_por_valor


def converter_pgm_para_pbm(
    caminho_entrada: str | Path,
    *,
    caminho_saida: str | Path | None = None,
    limiar: int | None = None,
) -> tuple[Path, int]:
    caminho_origem = Path(caminho_entrada)
    imagem = carregar_imagem(caminho_origem)

    # limiar: usa o valor informado; se nao vier, usa a media da imagem como corte.
    limiar_usado = int(np.mean(imagem.matriz)) if limiar is None else int(limiar)
    matriz_binaria = limiarizar_por_valor(imagem.matriz, limiar_usado)

    if caminho_saida is None:
        caminho_destino = caminho_origem.with_name(f"{caminho_origem.stem}_binaria.pbm")
    else:
        caminho_destino = Path(caminho_saida)

    caminho_destino.parent.mkdir(parents=True, exist_ok=True)

    # pbm: mantemos a imagem binaria no padrao do projeto e gravamos em P1 com 0 e 1 no arquivo.
    imagem_binaria = criar_imagem(
        matriz_binaria,
        nome=caminho_destino.stem,
        binaria=True,
        caminho_origem=caminho_origem,
    )
    salvar_imagem(imagem_binaria, caminho_destino, formato="P1")
    return caminho_destino, limiar_usado


def _caminhos_padrao() -> list[Path]:
    candidatos = [
        Path.cwd() / "lena.pgm",
        Path.cwd() / "airplane.pgm",
        ROOT / "lena.pgm",
        ROOT / "airplane.pgm",
        ROOT / "assets" / "exemplos" / "lena.pgm",
        ROOT / "assets" / "exemplos" / "airplane.pgm",
    ]
    encontrados: list[Path] = []
    vistos: set[Path] = set()
    for candidato in candidatos:
        resolvido = candidato.resolve()
        if resolvido.exists() and resolvido not in vistos:
            encontrados.append(resolvido)
            vistos.add(resolvido)
    return encontrados


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Converte arquivos PGM para PBM com pixels 0 e 1 no arquivo de saida."
    )
    parser.add_argument(
        "imagens",
        nargs="*",
        help="Caminhos dos arquivos .pgm que serao convertidos. Se vazio, tenta lena.pgm e airplane.pgm.",
    )
    parser.add_argument(
        "--limiar",
        type=int,
        default=None,
        help="Valor de corte da binarizacao. Se omitido, usa a media da imagem.",
    )
    parser.add_argument(
        "--saida-dir",
        type=Path,
        default=None,
        help="Pasta onde os arquivos .pbm serao salvos. Se omitido, salva ao lado do .pgm.",
    )
    return parser


def main() -> int:
    parser = _construir_parser()
    args = parser.parse_args()

    caminhos = [Path(item) for item in args.imagens] if args.imagens else _caminhos_padrao()
    if not caminhos:
        parser.error(
            "Nenhuma imagem foi informada e nao encontrei lena.pgm/airplane.pgm automaticamente. "
            "Passe os caminhos dos .pgm na linha de comando."
        )

    for caminho in caminhos:
        if caminho.suffix.lower() != ".pgm":
            parser.error(f"O arquivo '{caminho}' nao eh .pgm.")

    for caminho in caminhos:
        destino = None
        if args.saida_dir is not None:
            destino = args.saida_dir / f"{caminho.stem}_binaria.pbm"
        caminho_saida, limiar_usado = converter_pgm_para_pbm(
            caminho,
            caminho_saida=destino,
            limiar=args.limiar,
        )
        print(f"{caminho.name} -> {caminho_saida} | limiar = {limiar_usado}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
