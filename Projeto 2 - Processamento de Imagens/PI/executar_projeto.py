from pathlib import Path
import sys


RAIZ_PROJETO = Path(__file__).resolve().parent
PASTA_SRC = RAIZ_PROJETO / "src"

# chave: garante que a pasta `src` fique visivel para os imports do projeto
if str(PASTA_SRC) not in sys.path:
    sys.path.insert(0, str(PASTA_SRC))

from laboratorio_imagens.aplicacao import executar

if __name__ == "__main__":
    # entrada: inicia a interface principal do laboratorio
    executar()