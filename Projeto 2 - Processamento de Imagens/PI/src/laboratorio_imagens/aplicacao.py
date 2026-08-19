from laboratorio_imagens.ui.janela_principal import JanelaPrincipal


def executar() -> None:
    # bootstrap: cria a janela e inicia o loop grafico do tkinter
    aplicacao = JanelaPrincipal()
    aplicacao.mainloop()
