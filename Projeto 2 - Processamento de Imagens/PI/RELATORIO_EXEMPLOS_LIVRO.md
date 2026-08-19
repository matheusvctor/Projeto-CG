# Relatorio de Exemplos do Livro

## Escopo

Este arquivo cruza o que foi implementado no sistema com exemplos e secoes dos livros usados na disciplina.

Observacao metodologica: o texto dos PDFs foi extraido localmente e as paginas puderam ser identificadas, mas as figuras do livro nao ficaram disponiveis em resolucao adequada dentro do ambiente. Por isso, os testes abaixo reproduzem o mesmo tipo de processamento usando as imagens do projeto, com saidas salvas em `resultados_livro/`.

## Conferencia rapida do codigo

- `Aba Operacoes` bate com o capitulo 2.3 do livro de processamento para soma, subtracao, multiplicacao, divisao, AND, OR e XOR. Foi adicionada a operacao `NOT` para cobrir tambem a figura 17.
- `Aba Intensidade e Histograma` bate com a equalizacao de histograma da secao 3.3, usando cdf acumulada e remapeamento para `0..255`.
- `Aba Filtros` bate conceitualmente com media, mediana, Prewitt, Sobel e high-boost. A formula de `high-boost` foi ajustada para `A * original - passa-baixas`, como aparece na equacao (4.18).
- `Aba Morfologia` cobre dilatacao, erosao, abertura, fechamento, hit-or-miss e extracao de contorno, em linha com o capitulo 5.
- `Aba Geometria` cobre escala, translacao, rotacao e reflexao. O `cisalhamento` foi refeito como composicao de cisalhamento em `x` seguido de cisalhamento em `y`, seguindo a ideia apresentada para a transformacao do gato de Arnold.

## Observacoes de aderencia

- Em `utilidades_matriz.py`, o processamento espacial usa correlacao com borda replicada. Para mascaras simetricas, isso coincide com o uso de convolucao do livro.
- Para `Prewitt`, `Sobel` e `Roberts`, a combinacao das respostas e feita por magnitude (`abs(x) + abs(y)`), enquanto o texto do livro menciona combinacao por `OR` em alguns exemplos de borda. O efeito visual e proximo, mas nao identico. A interface tambem oferece as respostas isoladas em `X` e `Y` para `Prewitt`, `Sobel`, `Roberts` e `Roberts cruzado`.
- O sistema atual nao cobre diretamente especificacao de histograma, compressao de histograma, preenchimento de regioes, afinamento, espessamento e esqueletizacao.

## Exemplos mapeados

### 1. Operacoes aritmeticas e logicas

- Livro: Ogê Marques Filho e Hugo Vieira Neto, capitulo 2.3, paginas 30 a 33, figuras 9 a 17.
- Nossa secao: `Aba Operacoes`.
- Entradas usadas: `lena.pgm`, `airplane.pgm` e versoes binarizadas por limiar medio.
- Arquivos gerados:
  - `resultados_livro/operacoes_soma_normalizada.pgm`
  - `resultados_livro/operacoes_subtracao_normalizada.pgm`
  - `resultados_livro/operacoes_multiplicacao_normalizada.pgm`
  - `resultados_livro/operacoes_divisao_normalizada.pgm`
  - `resultados_livro/operacoes_and.pbm`
  - `resultados_livro/operacoes_or.pbm`
  - `resultados_livro/operacoes_xor.pbm`
  - `resultados_livro/operacoes_not_a.pbm`
- Como estava: duas imagens em tons de cinza e duas versoes binarias derivadas delas.
- Como deve ficar: a soma clareia a cena, a subtracao destaca diferencas, multiplicacao reforca intersecoes de intensidade, divisao reescala contraste local, `AND` preserva interseccao, `OR` une regioes, `XOR` destaca diferencas e `NOT` inverte preto/branco.

### 2. Equalizacao de histograma

- Livro: capitulo 3.3, pagina 64, figura 10.
- Nossa secao: `Aba Intensidade e Histograma`.
- Entradas usadas: `airplane.pgm` e uma versao de baixo contraste gerada artificialmente.
- Arquivos gerados:
  - `resultados_livro/histograma_baixo_contraste.pgm`
  - `resultados_livro/histograma_equalizada.pgm`
- Como estava: a imagem de entrada foi comprimida para concentrar os niveis de cinza em uma faixa estreita.
- Como deve ficar: a equalizacao espalha os niveis pela faixa completa, aumentando o contraste perceptivel e abrindo detalhes em regioes antes apagadas.

### 3. Filtro da mediana versus filtro da media

- Livro: capitulo 4.2.3, paginas 91 a 93, figuras 8 e 9.
- Nossa secao: `Aba Filtros`.
- Entradas usadas: `lena.pgm` com ruido sal-e-pimenta sintetico e ruido gaussiano sintetico.
- Arquivos gerados:
  - `resultados_livro/filtros_ruido_sal_pimenta.pgm`
  - `resultados_livro/filtros_mediana_sal_pimenta.pgm`
  - `resultados_livro/filtros_media_sal_pimenta.pgm`
  - `resultados_livro/filtros_ruido_gaussiano.pgm`
  - `resultados_livro/filtros_mediana_gaussiano.pgm`
  - `resultados_livro/filtros_media_gaussiano.pgm`
- Como estava: a imagem foi degradada por ruido impulsivo ou gaussiano.
- Como deve ficar: na versao com sal-e-pimenta, a mediana remove melhor os pontos isolados e preserva mais as bordas; na versao gaussiana, media e mediana produzem resultados mais proximos.

### 4. Prewitt e Sobel

- Livro: capitulo 2.4.3, pagina 39, figura 19.
- Nossa secao: `Aba Filtros`.
- Entrada usada: `lena.pgm`.
- Arquivos gerados:
  - `resultados_livro/filtros_prewitt.pgm`
  - `resultados_livro/filtros_sobel.pgm`
- Como estava: imagem monocromatica sem realce de bordas.
- Como deve ficar: as bordas principais ficam evidenciadas; o Sobel tende a responder de forma um pouco mais estavel por incluir suavizacao na mascara.

### 5. High-boost

- Livro: capitulo 4.3.3, paginas 97 e 98, figuras 14 e 15.
- Nossa secao: `Aba Filtros`.
- Entrada usada: `lena.pgm`.
- Arquivos gerados:
  - `resultados_livro/filtros_high_boost_a_1_10.pgm`
  - `resultados_livro/filtros_high_boost_a_1_15.pgm`
  - `resultados_livro/filtros_high_boost_a_1_20.pgm`
- Como estava: imagem original sem reforco artificial de nitidez.
- Como deve ficar: os contornos e detalhes finos ficam mais destacados sem perder completamente a aparencia da imagem original; quanto maior o `A`, maior o realce.

### 6. Morfologia binaria

- Livro: capitulo 5.4 e 5.5, paginas 147 a 149, figuras 8 e 9.
- Nossa secao: `Aba Morfologia`.
- Entrada usada: `letra_j.pbm`, ampliada para facilitar visualizacao.
- Arquivos gerados:
  - `resultados_livro/morfologia_dilatacao.pbm`
  - `resultados_livro/morfologia_erosao.pbm`
  - `resultados_livro/morfologia_abertura.pbm`
  - `resultados_livro/morfologia_fechamento.pbm`
  - `resultados_livro/morfologia_hit_or_miss.pbm`
  - `resultados_livro/morfologia_contorno_interno.pbm`
- Como estava: uma forma binaria simples, com pixels de fundo e objeto bem separados.
- Como deve ficar: dilatacao engrossa a forma, erosao afina, abertura remove pequenos salientes, fechamento recompõe pequenas falhas, `hit-or-miss` procura um padrao local e o contorno interno deixa so a borda do objeto.

### 7. Transformacoes geometricas

- Livro: capitulo 2.5, paginas 42 a 46, figuras 24 a 27.
- Nossa secao: `Aba Geometria`.
- Entrada usada: `airplane.pgm`.
- Arquivos gerados:
  - `resultados_livro/geometria_escala.pgm`
  - `resultados_livro/geometria_translacao.pgm`
  - `resultados_livro/geometria_rotacao_30_graus.pgm`
  - `resultados_livro/geometria_reflexao_horizontal.pgm`
  - `resultados_livro/geometria_cisalhamento_arnold.pgm`
- Como estava: imagem original no referencial padrao.
- Como deve ficar: escala altera as dimensoes, translacao desloca a cena, rotacao muda a orientacao, reflexao espelha a imagem e o cisalhamento inclina a geometria conforme os fatores escolhidos.

### 8. Recomendacao do professor para cisalhamento

- Livro: Anton e Rorres, capitulo 10, secao 10.14 `Caos`, pagina 643 impressa; no PDF extraido, o trecho aparece na regiao da pagina 642 a 643.
- Nossa secao: `Aba Geometria`, transformacao `Cisalhamento`.
- Ideia usada: a transformacao do gato de Arnold e escrita como composicao de um cisalhamento em `x` seguido de um cisalhamento em `y`.
- Como estava no sistema: o cisalhamento era uma matriz afim unica, sem composicao explicita.
- Como deve ficar: o codigo primeiro modela o cisalhamento em `x`, depois o cisalhamento em `y`, aproximando melhor a interpretacao matricial sugerida pelo professor.
- Observacao: foi usada a parte linear da fatoracao do Arnold. O reagrupamento `mod 1` nao foi aplicado, porque a nossa aba trabalha com transformacao geometrica afim sobre imagem e nao com iteracoes de um mapa caotico.

## Como reproduzir

Execute na pasta `PI`:

```powershell
& "C:\Users\loy_l\anaconda3\python.exe" .\scripts\gerar_exemplos_livro.py
```
