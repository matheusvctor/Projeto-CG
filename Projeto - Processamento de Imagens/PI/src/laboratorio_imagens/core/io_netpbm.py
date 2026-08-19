from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


FORMATOS_SUPORTADOS = {"P1", "P2", "P5"}


@dataclass(slots=True)
class ImagemNetpbm:
    matriz: np.ndarray
    caminho_origem: Path | None = None
    formato_origem: str = "P5"
    binaria: bool = False
    nome: str = "imagem"

    @property
    def altura(self) -> int:
        return int(self.matriz.shape[0])

    @property
    def largura(self) -> int:
        return int(self.matriz.shape[1])

    def copiar(
        self,
        nova_matriz: np.ndarray,
        *,
        nome: str | None = None,
        binaria: bool | None = None,
    ) -> "ImagemNetpbm":
        return ImagemNetpbm(
            matriz=nova_matriz.astype(np.uint8),
            caminho_origem=self.caminho_origem,
            formato_origem=self.formato_origem,
            binaria=self.binaria if binaria is None else binaria,
            nome=self.nome if nome is None else nome,
        )


def _ler_token(arquivo) -> bytes:
    # parser: le o proximo token ignorando espacos e comentarios do formato NetPBM
    while True:
        caractere = arquivo.read(1)
        if not caractere:
            return b""
        if caractere in b" \t\r\n":
            continue
        if caractere == b"#":
            arquivo.readline()
            continue
        break

    token = bytearray(caractere)
    while True:
        caractere = arquivo.read(1)
        if not caractere or caractere in b" \t\r\n":
            break
        token.extend(caractere)
    return bytes(token)


def _posicionar_em_dados_binarios(arquivo) -> None:
    while True:
        posicao = arquivo.tell()
        caractere = arquivo.read(1)
        if not caractere:
            return
        if caractere in b" \t\r\n":
            continue
        if caractere == b"#":
            arquivo.readline()
            continue
        arquivo.seek(posicao)
        return


def _normalizar_para_uint8(matriz: np.ndarray, valor_maximo: int) -> np.ndarray:
    if valor_maximo == 255:
        return matriz.astype(np.uint8)
    escala = 255.0 / max(valor_maximo, 1)
    return np.clip(np.rint(matriz.astype(np.float64) * escala), 0, 255).astype(np.uint8)


def carregar_imagem(caminho: str | Path) -> ImagemNetpbm:
    # leitura: suporta nativamente NetPBM (P1, P2, P5) e imagens comuns (PNG, JPG, JPEG, BMP, WEBP)
    caminho_imagem = Path(caminho)
    extensao = caminho_imagem.suffix.lower()

    # 1. Tenta carregar como NetPBM se a extensão for .pgm ou .pbm
    if extensao in {".pgm", ".pbm"}:
        try:
            with caminho_imagem.open("rb") as arquivo:
                identificador = _ler_token(arquivo).decode("ascii", errors="ignore")
                if identificador in FORMATOS_SUPORTADOS:
                    largura = int(_ler_token(arquivo))
                    altura = int(_ler_token(arquivo))

                    if identificador == "P1":
                        valores = []
                        while True:
                            token = _ler_token(arquivo)
                            if not token:
                                break
                            valores.append(int(token))
                        matriz = np.array(valores, dtype=np.uint8).reshape((altura, largura))
                        matriz = np.where(matriz > 0, 255, 0).astype(np.uint8)
                        return ImagemNetpbm(
                            matriz=matriz,
                            caminho_origem=caminho_imagem,
                            formato_origem=identificador,
                            binaria=True,
                            nome=caminho_imagem.stem,
                        )

                    valor_maximo = int(_ler_token(arquivo))

                    if identificador == "P2":
                        valores = []
                        while True:
                            token = _ler_token(arquivo)
                            if not token:
                                break
                            valores.append(int(token))
                        matriz = np.array(valores, dtype=np.uint16).reshape((altura, largura))
                        matriz = _normalizar_para_uint8(matriz, valor_maximo)
                        return ImagemNetpbm(
                            matriz=matriz,
                            caminho_origem=caminho_imagem,
                            formato_origem=identificador,
                            binaria=False,
                            nome=caminho_imagem.stem,
                        )

                    _posicionar_em_dados_binarios(arquivo)
                    bruto = arquivo.read()
                    if valor_maximo <= 255:
                        matriz = np.frombuffer(bruto, dtype=np.uint8).reshape((altura, largura))
                    else:
                        matriz = np.frombuffer(bruto, dtype=">u2").reshape((altura, largura))
                    matriz = _normalizar_para_uint8(matriz, valor_maximo)
                    return ImagemNetpbm(
                        matriz=matriz,
                        caminho_origem=caminho_imagem,
                        formato_origem=identificador,
                        binaria=False,
                        nome=caminho_imagem.stem,
                    )
        except Exception:
            pass  # Se falhar o parser NetPBM, cai para o leitor de imagem universal (PIL)

    # 2. Carregamento universal via PIL (PNG, JPG, JPEG, BMP, WEBP, etc.)
    try:
        from PIL import Image
        with Image.open(caminho_imagem) as img:
            eh_binaria = img.mode == "1"
            if eh_binaria:
                matriz = (np.array(img, dtype=np.uint8) * 255).astype(np.uint8)
            else:
                img_cinza = img.convert("L")
                matriz = np.array(img_cinza, dtype=np.uint8)

            return ImagemNetpbm(
                matriz=matriz,
                caminho_origem=caminho_imagem,
                formato_origem=extensao.lstrip(".").upper() or "IMG",
                binaria=eh_binaria,
                nome=caminho_imagem.stem,
            )
    except Exception as erro:
        raise ValueError(
            f"Não foi possível abrir o arquivo '{caminho_imagem.name}': formato não reconhecido ou corrompido ({erro})."
        )


def salvar_imagem(
    imagem: ImagemNetpbm,
    caminho: str | Path,
    *,
    formato: str | None = None,
) -> Path:
    # saida: salva a matriz no formato escolhido (NetPBM ou PNG/JPG/BMP)
    caminho_saida = Path(caminho)
    matriz = np.asarray(imagem.matriz, dtype=np.uint8)
    extensao = caminho_saida.suffix.lower()

    # Salvamento de formatos comuns via PIL (PNG, JPG, etc.)
    if extensao in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
        from PIL import Image
        if imagem.binaria:
            modo = "1"
            img_pil = Image.fromarray(matriz > 127).convert(modo)
        else:
            modo = "L"
            img_pil = Image.fromarray(matriz, mode=modo)
        img_pil.save(caminho_saida)
        return caminho_saida

    if formato is None:
        if extensao == ".pbm":
            formato = "P1"
        else:
            formato = "P5"

    if formato == "P1":
        binaria = np.where(matriz > 0, 1, 0).astype(np.uint8)
        linhas = ["P1", f"{imagem.largura} {imagem.altura}"]
        linhas.extend(" ".join(str(valor) for valor in linha) for linha in binaria)
        caminho_saida.write_text("\n".join(linhas) + "\n", encoding="ascii")
        return caminho_saida

    if formato == "P2":
        linhas = ["P2", f"{imagem.largura} {imagem.altura}", "255"]
        linhas.extend(" ".join(str(int(valor)) for valor in linha) for linha in matriz)
        caminho_saida.write_text("\n".join(linhas) + "\n", encoding="ascii")
        return caminho_saida

    if formato != "P5":
        raise ValueError(f"Formato de saida '{formato}' nao suportado.")

    with caminho_saida.open("wb") as arquivo:
        cabecalho = f"P5\n{imagem.largura} {imagem.altura}\n255\n".encode("ascii")
        arquivo.write(cabecalho)
        arquivo.write(matriz.tobytes())
    return caminho_saida


def criar_imagem(
    matriz: np.ndarray,
    *,
    nome: str = "resultado",
    binaria: bool = False,
    caminho_origem: Path | None = None,
) -> ImagemNetpbm:
    return ImagemNetpbm(
        matriz=np.asarray(matriz, dtype=np.uint8),
        caminho_origem=caminho_origem,
        formato_origem="P5" if not binaria else "P1",
        binaria=binaria,
        nome=nome,
    )
