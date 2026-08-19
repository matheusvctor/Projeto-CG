# Guia Rapido do Projeto

Este guia resume a estrutura atual do projeto, os arquivos mais importantes e as funcoes ou variaveis que mais aparecem no codigo.

## Entrada do projeto

- [executar_projeto.py](./executar_projeto.py)
  Inicia a aplicacao.
  Ajusta o caminho da pasta `src` e chama a funcao principal da interface.

- [src/laboratorio_imagens/aplicacao.py](./src/laboratorio_imagens/aplicacao.py)
  Tem a funcao `executar()`.
  Ela cria a janela principal e inicia o loop do `tkinter`.

## Interface

- [src/laboratorio_imagens/ui/janela_principal.py](./src/laboratorio_imagens/ui/janela_principal.py)
  Classe principal: `JanelaPrincipal`.
  Monta o cabecalho, aplica o tema visual e organiza as abas do sistema.

- [src/laboratorio_imagens/ui/widgets.py](./src/laboratorio_imagens/ui/widgets.py)
  Componentes reutilizaveis da interface.
  Classes principais:
  `FrameRolavel`: envolve uma aba inteira com barra de rolagem vertical.
  `PainelImagem`: mostra a imagem, a tabela sincronizada de pixels e a selecao com o mouse.
  `SincronizadorPaineisImagem`: espelha a leitura dos pixels entre paineis quando o usuario habilita essa opcao.
  `GraficoHistograma`: desenha histogramas com grade, eixos e tambem serve para a janela ampliada de apresentacao.
  Funcoes importantes:
  `criar_photoimage_ajustada()`: encaixa a imagem na area da aba.
  `criar_photoimage_original()`: preserva a exibicao em pixels reais.

- [src/laboratorio_imagens/ui/abas_processamento.py](./src/laboratorio_imagens/ui/abas_processamento.py)
  Abas mais diretas do sistema.
  Classes:
  `AbaFiltros`: filtros espaciais com mascara `3x3` visivel e sincronizada com o modulo `filtros_espaciais`.
  `AbaOperacoes`: operacoes aritmeticas e logicas entre imagens, com opcao de sincronizar tabelas.
  `AbaIntensidadeHistograma`: `Negativo de uma imagem`, `Transformacao Gamma`, `Transformacao logaritmo`, `Funcao de transferencia de intensidade geral`, `Funcao de transferencia faixa dinamica`, `Funcao de transferencia linear`, `Equalize o histograma`, histogramas melhorados e zoom dos histogramas.

- [src/laboratorio_imagens/ui/abas_avancadas.py](./src/laboratorio_imagens/ui/abas_avancadas.py)
  Abas com operacoes mais elaboradas.
  Classes:
  `AbaMorfologia`: morfologia binaria e em tons de cinza, com sincronizacao opcional das tabelas.
  `AbaGeometria`: escala, translacao, reflexao, cisalhamento e rotacao com exibicao em pixels reais.
  `AbaMorfismo`: marca pontos correspondentes, atualiza a previa pelo valor de `t`, carrega um exemplo experimental e exporta a animacao final.

## Nucleo de imagens

- [src/laboratorio_imagens/core/io_netpbm.py](./src/laboratorio_imagens/core/io_netpbm.py)
  Faz leitura e escrita de `PGM` e `PBM`.
  Classe principal:
  `ImagemNetpbm`: guarda a matriz da imagem e metadados simples.
  Funcoes principais:
  `carregar_imagem()`, `salvar_imagem()` e `criar_imagem()`.

- [src/laboratorio_imagens/core/utilidades_matriz.py](./src/laboratorio_imagens/core/utilidades_matriz.py)
  Reune funcoes auxiliares usadas pelos outros modulos.
  Exemplos:
  `limitar_uint8()`: limita valores para `0..255`.
  `normalizar_uint8()`: reescala um resultado para a faixa de cinza.
  `aplicar_correlacao()`: aplica uma mascara sobre a imagem.
  `aplicar_mediana()`: calcula a mediana em janelas locais.

## Algoritmos principais

- [src/laboratorio_imagens/core/filtros_espaciais.py](./src/laboratorio_imagens/core/filtros_espaciais.py)
  Filtros da aula 9.
  Funcoes principais:
  `filtro_media()`, `filtro_mediana()`, `operador_roberts()`, `operador_roberts_x()`, `operador_roberts_y()`, `operador_roberts_cruzado()`, `operador_roberts_cruzado_x()`, `operador_roberts_cruzado_y()`, `operador_prewitt()`, `operador_prewitt_x()`, `operador_prewitt_y()`, `operador_sobel()`, `operador_sobel_x()`, `operador_sobel_y()` e `filtragem_high_boost()`.
  Variaveis importantes:
  `FILTROS_DISPONIVEIS`, `MASCARA_ROBERTS_X`, `MASCARA_ROBERTS_Y`, `MASCARA_ROBERTS_CRUZADO_X`, `MASCARA_ROBERTS_CRUZADO_Y`, `MASCARA_PREWITT_X`, `MASCARA_PREWITT_Y`, `MASCARA_SOBEL_X`, `MASCARA_SOBEL_Y`.

- [src/laboratorio_imagens/core/operacoes_pixel.py](./src/laboratorio_imagens/core/operacoes_pixel.py)
  Operacoes entre duas imagens.
  Funcoes principais:
  `soma()`, `subtracao()`, `multiplicacao()`, `divisao()`, `operacao_and()`, `operacao_or()`, `operacao_xor()` e `operacao_not()`.

- [src/laboratorio_imagens/core/transformacoes_intensidade.py](./src/laboratorio_imagens/core/transformacoes_intensidade.py)
  Transformacoes ponto a ponto.
  Funcoes principais:
  `negativo()`, `transformacao_gamma()`, `transformacao_logaritmica()`, `transformacao_linear()`, `faixa_dinamica()` e `funcao_sigmoide()`.

- [src/laboratorio_imagens/core/histograma.py](./src/laboratorio_imagens/core/histograma.py)
  Trabalha com a distribuicao dos niveis de cinza.
  Funcoes principais:
  `calcular_histograma()` e `equalizar_histograma()`.

- [src/laboratorio_imagens/core/operacoes_morfologicas.py](./src/laboratorio_imagens/core/operacoes_morfologicas.py)
  Reune morfologia binaria e em tons de cinza.
  Variaveis importantes:
  `ELEMENTOS_ESTRUTURANTES` e `MASCARAS_HIT_OR_MISS`.

- [src/laboratorio_imagens/core/transformacoes_geometricas.py](./src/laboratorio_imagens/core/transformacoes_geometricas.py)
  Faz transformacoes afins.
  Funcoes principais:
  `escalar()`, `transladar()`, `rotacionar()`, `refletir()` e `cisalhar()`.

- [src/laboratorio_imagens/core/morfismo.py](./src/laboratorio_imagens/core/morfismo.py)
  Implementa o morfismo com triangulacao.
  Funcoes principais:
  `preparar_morfismo()`, `gerar_frame_preparado()`, `gerar_sequencia_preparada()` e `salvar_gif_animado()`.
  Classes:
  `ResultadoMorfismo` e `PreparacaoMorfismo`.

- [src/laboratorio_imagens/core/exemplos_morfismo.py](./src/laboratorio_imagens/core/exemplos_morfismo.py)
  Guarda o exemplo experimental do morfismo.
  Funcoes principais:
  `carregar_exemplo_luiz()` e `exemplo_luiz_disponivel()`.

## Variaveis que aparecem bastante nas abas

- `imagem_origem`, `imagem_a`, `imagem_b`, `imagem_inicial`, `imagem_final`
  Guardam as imagens carregadas pelo usuario.

- `imagem_resultado`
  Guarda o resultado mais recente da aba.

- `status`
  Texto de retorno mostrado ao usuario.

- `filtro_atual`, `operacao_atual`, `transformacao`, `modo_operacao`
  Guardam a opcao selecionada na interface.

- `parametro_1`, `parametro_2`, `fator_realce`
  Guardam valores digitados pelo usuario.

- `pontos_iniciais`, `pontos_finais`
  Listas usadas no morfismo para marcar pontos correspondentes.

## Recursos importantes da interface

- Tabela sincronizada de pixels com janelas `10x10`, `12x12` e `20x20`.
- Clique esquerdo fixa a leitura dos pixels e clique direito libera novamente.
- Varias abas tem um botao para sincronizar as tabelas de pixels entre os paineis mostrados.
- A aba de filtros sempre mostra a mascara `3x3` do operador selecionado usando a mesma referencia do modulo `core`.
- O `High-boost` mostra o valor de `A` apenas quando necessario.
- A aba de intensidade tem histogramas com visual mais forte e uma janela de zoom para apresentacao.
- A aba geometrica usa exibicao em pixels reais para o tamanho visual acompanhar a matriz transformada.
- Na aba geometrica, os parametros seguem a convencao cartesiana: `+dy` sobe, `+angulo` gira em sentido anti-horario e o cisalhamento usa a mesma orientacao.
- A aba de morfismo atualiza o frame ao mover a barra `t`, mostra os campos de quadros e atraso e salva a animacao final.
- As abas principais usam rolagem vertical para que o conteudo inferior nao fique cortado.

## Documentos auxiliares

- [README.md](./README.md)
  Resumo geral do projeto e como executar.

- [RELATORIO_EXEMPLOS_LIVRO.md](./RELATORIO_EXEMPLOS_LIVRO.md)
  Relaciona exemplos da bibliografia com as abas do sistema.

- [scripts/gerar_exemplos_livro.py](./scripts/gerar_exemplos_livro.py)
  Gera os exemplos usados no relatorio.

## Fluxo geral

1. O usuario carrega uma ou duas imagens.
2. A aba chama uma funcao do modulo `core`.
3. O resultado volta como matriz `numpy`.
4. A matriz vira um objeto `ImagemNetpbm`.
5. A interface atualiza a imagem, a tabela de pixels e, quando fizer sentido, o histograma.
