# Projeto 1 - Computacao Grafica

Projeto em Python para a disciplina de Computacao Grafica, com interface em `tkinter`, organizado em quatro questoes principais.

## Modulos

- `Questao 1 - Primitivas e Transformacoes 2D`:
  - desenho de formas simples e conicas;
  - transformacoes 2D (translacao, rotacao, escala e cisalhamento).
- `Questao 2 - Recortes`:
  - recorte de retas com Cohen-Sutherland;
  - recorte de poligonos com Sutherland-Hodgman.
- `Questao 3 - Transformacoes 3D`:
  - transformacoes no objeto 3D (translacao, rotacao, escala, reflexoes e cisalhamento);
  - projecao e exibicao em viewport com historico de transformacoes.
- `Questao 4 - Operacoes com Imagens PGM`:
  - transformacoes afins em imagens (escala, rotacao, translacao, cisalhamento e reflexao);
  - carregamento e visualizacao de imagens `PGM`.

## Estrutura

- `Projeto_CG_Final/main_menu.py`: menu principal para acesso aos modulos.
- `Projeto_CG_Final/theme.py`: tema visual compartilhado da interface.
- `Projeto_CG_Final/mod_primitivas/Questao1`: primitivas e transformacoes 2D.
- `Projeto_CG_Final/mod_recortes/Questao2`: interfaces e algoritmos de recorte.
- `Projeto_CG_Final/mod_3d/Questao3`: ambiente de transformacoes 3D.
- `Projeto_CG_Final/mod_imagens/Questao4`: transformacoes geometricas aplicadas em imagens `PGM`.

## Como executar

1. Entre na pasta `Projeto_CG_Final`.
2. Garanta que o Python 3 esteja disponivel no ambiente.
3. Execute o menu principal:

```powershell
python .\main_menu.py
```

## Observacoes

- O projeto utiliza a biblioteca padrao do Python com `tkinter` para a interface grafica.
- Alguns modulos podem ser executados de forma independente a partir de seus scripts internos.
- O modulo de imagens da Questao 4 trabalha com arquivos no formato `PGM`.

## Erros Cometidos

- Na parte de transformações 2D, não contém composição de transformações, e também quando ele rotaciona, o objeto sai da sua posição atual.
- O pixels não estão sendo ativados a nível de pixel(o desenho fica fino quando isso está correto), parecendo que está sendo ativado 4 pixels para ser um pixel só.