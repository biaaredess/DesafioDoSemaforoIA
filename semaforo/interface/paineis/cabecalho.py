"""Cabeçalho do painel: semáforo-logotipo, título e abas (coordenadas locais)."""
from typing import Callable

import pygame

from ..formas import placa
from ..tema import Escala, Fontes, Layout, Paleta
from ..texto import desenhar_texto
from ..widgets import Abas


class Cabecalho:
    ABAS = [("Jogar", "jogar"), ("Treinar a IA", "treinar"), ("Como a IA pensa", "pensa")]

    def __init__(self, ao_mudar_aba: Callable[[str], None]):
        largura = Layout.LARGURA - Layout.PAINEL_X - 2 * Layout.MARGEM
        self.abas = Abas((Layout.MARGEM, 84), largura, self.ABAS, "jogar", ao_mudar_aba)

    @property
    def sob_mouse(self) -> bool:
        return self.abas.sob_mouse

    def tratar_evento(self, evento) -> bool:
        return self.abas.tratar_evento(evento)

    def selecionar(self, aba: str) -> None:
        self.abas.valor = aba

    def desenhar(self, tela: pygame.Surface) -> None:
        x, y = Layout.MARGEM, 22
        caixa = pygame.Rect(x, y, 48, 46)
        placa(tela, caixa, Paleta.ESCURO, chanfro=8)
        for i, cor in enumerate((Paleta.VERMELHO, Paleta.AMARELO, Paleta.VERDE)):
            tela.circle(cor, (caixa.x + 11 + i * 13, caixa.centery), 5)
        desenhar_texto(tela, "DESAFIO DO SEMÁFORO", Fontes.obter(Escala.TITULO, "letreiro"), Paleta.TEXTO,
                       (caixa.right + 14, caixa.centery + 3), "midleft")
        self.abas.desenhar(tela)
