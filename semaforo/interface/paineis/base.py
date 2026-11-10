"""Classe base dos painéis: lista de widgets + desenho próprio, em coordenadas locais.

O painel é desenhado numa superfície própria (``Layout.LARGURA - Layout.PAINEL_X``
de largura), assim ele pode deslizar para fora da tela sem recalcular posições.
"""
import pygame

from ...jogo import ControladorJogo
from ..widgets import Widget


class Painel:
    def __init__(self, controlador: ControladorJogo):
        self.controlador = controlador
        self.widgets: list[Widget] = []

    def tratar_evento(self, evento: pygame.event.Event) -> bool:
        consumiu = False
        for w in self.widgets:
            # todos recebem MOUSEMOTION (para o hover); o resto para no primeiro que consumir
            if w.tratar_evento(evento) and evento.type != pygame.MOUSEMOTION:
                consumiu = True
                break
        return consumiu

    def atualizar(self) -> None:
        """Sincroniza botões habilitados com o estado do controlador."""

    def desenhar(self, tela: pygame.Surface) -> None:
        for w in self.widgets:
            w.desenhar(tela)

    @property
    def sob_mouse(self) -> bool:
        return any(w.sob_mouse for w in self.widgets)
