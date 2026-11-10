"""A forma-assinatura da interface: placa de cantos chanfrados com filete interno."""
import pygame

from .tela import Tela
from .tema import Layout


def _poligono(rect: pygame.Rect, chanfro: float) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = rect.left, rect.top, rect.right, rect.bottom
    c = min(chanfro, rect.w / 2, rect.h / 2)
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def placa(tela: Tela, rect, fundo, borda=None, espessura: int = 0, filete=None,
          chanfro: int = Layout.CHANFRO, recuo_filete: int = 5) -> None:
    """Desenha uma placa.

    ``borda``: contorno externo com ``espessura`` (unidades lógicas).
    ``filete``: linha fina interna, a uns px da borda, como nas placas de trânsito.
    """
    rect = pygame.Rect(rect)
    if borda is not None and espessura:
        tela.poligono_suave(borda, _poligono(rect, chanfro))
        interno = rect.inflate(-2 * espessura, -2 * espessura)
        chanfro_int = max(1, chanfro - espessura // 2)
    else:
        interno, chanfro_int = rect, chanfro
    tela.poligono_suave(fundo, _poligono(interno, chanfro_int))
    if filete is not None:
        r = interno.inflate(-2 * recuo_filete, -2 * recuo_filete)
        tela.polygon(filete, _poligono(r, max(1, chanfro_int - recuo_filete // 2)), 2)


def sombra(tela: Tela, rect, deslocamento=(8, 10), alfa: int = 70, chanfro: int = 14) -> None:
    """Sombra dura e translúcida de uma placa, desenhada numa camada do tamanho dela."""
    rect = pygame.Rect(rect)
    camada = Tela.nova((rect.w + 2, rect.h + 2), transparente=True)
    placa(camada, pygame.Rect(0, 0, rect.w, rect.h), (0, 0, 0, alfa), chanfro=chanfro)
    tela.blit(camada, (rect.x + deslocamento[0], rect.y + deslocamento[1]))
