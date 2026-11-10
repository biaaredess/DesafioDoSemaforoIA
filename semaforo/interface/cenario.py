"""Desenho fixo do cenário: grama, calçadas com meio-fio amarelo, asfalto, pintura e passarelas."""
import math
import random

import pygame

from .geometria import GeometriaCruzamento
from .tela import Resolucao, Tela
from .tema import Paleta, escurecer


class Cenario:
    """Pré-renderiza o cenário uma única vez (é a parte mais cara de desenhar).

    ``superficie`` fica embaixo dos carros; ``cobertura`` (passarelas) por cima.
    """

    def __init__(self, geometria: GeometriaCruzamento):
        self.g = geometria
        tamanho = (geometria.largura, geometria.altura)
        self.k = Resolucao.k             # resolução em que foi desenhado
        self.superficie = Tela.nova(tamanho)
        self.cobertura = Tela.nova(tamanho, transparente=True)
        self._rng = random.Random(7)
        self._desenhar()

    # ------------------------------------------------------------------
    def _desenhar(self) -> None:
        self.superficie.fill(Paleta.ASFALTO)
        self._textura_asfalto()
        for canto in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            self._esquina(*canto)
        self._faixas_pedestre()
        self._linhas_parada()
        self._faixa_central()
        for lado in (-1, 1):
            self._passarela(lado)

    def _textura_asfalto(self) -> None:
        r, s, g = self._rng, self.superficie, self.g
        for _ in range(16000):
            x, y = r.randrange(g.largura), r.randrange(g.altura)
            tom = r.choice((-14, -9, 8, 12))
            cor = tuple(max(0, min(255, c + tom)) for c in Paleta.ASFALTO)
            s.fill(cor, (x, y, r.choice((1, 1, 2)), 1))

    def _esquina(self, sx: int, sy: int) -> None:
        """Quarteirão de um canto: meio-fio amarelo, calçada cinza e grama no meio."""
        g, s = self.g, self.superficie
        cx, cy, R = g.cx, g.cy, g.meia_rua
        fora = 60  # passa da tela nos lados externos: só o canto interno fica arredondado
        wx, wy = cx - R + fora, cy - R + fora
        x = -fora if sx < 0 else cx + R
        y = -fora if sy < 0 else cy + R
        canto = {(-1, -1): "border_bottom_right_radius", (1, -1): "border_bottom_left_radius",
                 (-1, 1): "border_top_right_radius", (1, 1): "border_top_left_radius"}[(sx, sy)]

        def bloco(recuo: float, cor, raio: float) -> pygame.Rect:
            rx = x + (0 if sx < 0 else recuo)
            ry = y + (0 if sy < 0 else recuo)
            rect = pygame.Rect(rx, ry, wx - recuo, wy - recuo)
            s.rect(cor, rect, **{canto: max(4, int(raio))})
            return rect

        rc, mf, cal = g.raio_esquina, g.meio_fio, g.calcada
        bloco(0, Paleta.MEIO_FIO, rc)
        bloco(mf, Paleta.CALCADA, rc - mf)
        self._ladrilhos(sx, sy)
        bloco(mf + cal - 3, Paleta.CALCADA_BORDA, rc - mf - cal + 3)
        grama = bloco(mf + cal, Paleta.GRAMA, rc - mf - cal)
        self._textura_grama(grama, sx, sy)

        meio = R + mf + cal / 2
        for px, py in ((cx + sx * meio, cy + sy * (R + rc + 6)), (cx + sx * (R + rc + 6), cy + sy * meio)):
            s.circle(escurecer(Paleta.CALCADA, 0.55), (px, py), 4)
            s.circle(Paleta.PARAFUSO, (px, py), 3)
            s.circle(Paleta.CALCADA_CLARA, (px - 1, py - 1), 1)

    def _ladrilhos(self, sx: int, sy: int) -> None:
        """Juntas da calçada: riscos claros a intervalos regulares."""
        g, s = self.g, self.superficie
        cx, cy, R, mf, cal = g.cx, g.cy, g.meia_rua, g.meio_fio, g.calcada
        cor = Paleta.CALCADA_CLARA
        inicio = int(R + g.raio_esquina + 14)
        for d in range(inicio, int(cy) + 1, 26):       # calçada da rua vertical
            y = cy + sy * d
            s.line(cor, (cx + sx * (R + mf), y), (cx + sx * (R + mf + cal - 3), y), 2)
        for d in range(inicio, int(cx) + 1, 26):       # calçada da rua horizontal
            x = cx + sx * d
            s.line(cor, (x, cy + sy * (R + mf)), (x, cy + sy * (R + mf + cal - 3)), 2)

    def _textura_grama(self, rect: pygame.Rect, sx: int, sy: int) -> None:
        r, s = self._rng, self.superficie
        area = rect.clip(s.get_rect())
        anterior = s.get_clip()
        s.set_clip(area)
        for _ in range(int(area.w * area.h / 55)):
            x = r.uniform(area.left, area.right)
            y = r.uniform(area.top, area.bottom)
            cor = r.choice((Paleta.GRAMA_CLARA, Paleta.GRAMA_ESCURA, Paleta.GRAMA_ESCURA))
            s.line(cor, (x, y), (x + r.uniform(-2, 2), y - r.uniform(3, 6)), 1)
        self._jardim(sx, sy)
        s.set_clip(anterior)

    def _jardim(self, sx: int, sy: int) -> None:
        """Arbustos e canteiros: um grupo perto do cruzamento (visível com o painel
        aberto) e outro nas pontas, que só aparecem na tela cheia."""
        g, r, s = self.g, self._rng, self.superficie
        cx, cy = g.cx, g.cy
        grupos = [
            (cx + sx * 318, cy + sy * 318, 30), (cx + sx * 250, cy + sy * 322, 20),
            (cx + sx * 312, cy + sy * 246, 22),
            (cx + sx * 560, cy + sy * 120, 34), (cx + sx * 600, cy + sy * 190, 22),
            (cx + sx * 480, cy + sy * 300, 26),
        ]
        for x, y, raio in grupos:
            s.circle(escurecer(Paleta.GRAMA, 0.7), (x + 4, y + 5), raio)
            s.circle(Paleta.ARBUSTO, (x, y), raio)
            for _ in range(5):
                ox, oy = r.uniform(-raio * 0.5, raio * 0.5), r.uniform(-raio * 0.5, raio * 0.5)
                s.circle(Paleta.ARBUSTO_CLARO, (x + ox - 3, y + oy - 3), raio * 0.35)
        for ax, ay, ar in grupos:
            for _ in range(4):
                angulo = r.uniform(0, 6.283)
                dist = ar + r.uniform(8, 18)
                x = ax + dist * math.cos(angulo)
                y = ay + dist * math.sin(angulo)
                cor = r.choice((Paleta.VERMELHO, Paleta.AMARELO, (255, 255, 255)))
                for dx, dy in ((-2.5, 0), (2.5, 0), (0, -2.5), (0, 2.5)):
                    s.circle(cor, (x + dx, y + dy), 2.2)
                s.circle(Paleta.LARANJA if cor == Paleta.AMARELO else Paleta.AMARELO, (x, y), 1.6)

    def _faixas_pedestre(self) -> None:
        g, s = self.g, self.superficie
        cx, cy, R = g.cx, g.cy, g.meia_rua
        a, b = g.pedestre_inicio, g.pedestre_fim
        listra, vao = 9, 8
        n = int((2 * R - 8 + vao) // (listra + vao))
        desloc = (n * listra + (n - 1) * vao) / 2
        for k in range(n):
            p = k * (listra + vao) - desloc
            for inicio in (a, -b):
                s.fill(Paleta.PINTURA, (cx + p, cy + inicio, listra, b - a))   # ruas norte e sul
                s.fill(Paleta.PINTURA, (cx + inicio, cy + p, b - a, listra))   # ruas leste e oeste

    def _linhas_parada(self) -> None:
        g, s = self.g, self.superficie
        cx, cy, R = g.cx, g.cy, g.meia_rua
        a, b = g.linha_parada
        e = b - a
        s.fill(Paleta.PINTURA, (cx - R, cy - b, R, e))      # quem vem do norte
        s.fill(Paleta.PINTURA, (cx, cy + a, R, e))          # quem vem do sul
        s.fill(Paleta.PINTURA, (cx + a, cy - R, e, R))      # quem vem do leste
        s.fill(Paleta.PINTURA, (cx - b, cy, e, R))          # quem vem do oeste

    def _faixa_central(self) -> None:
        """Faixa dupla amarela separando os sentidos, só fora do cruzamento."""
        g, s = self.g, self.superficie
        cx, cy, L, A = g.cx, g.cy, g.largura, g.altura
        ini = g.linha_parada[1] + 6
        for d in (-4, 2):
            s.fill(Paleta.AMARELO, (cx + d, 0, 2, cy - ini))
            s.fill(Paleta.AMARELO, (cx + d, cy + ini, 2, A - cy - ini))
            s.fill(Paleta.AMARELO, (0, cy + d, cx - ini, 2))
            s.fill(Paleta.AMARELO, (cx + ini, cy + d, L - cx - ini, 2))

    def _passarela(self, lado: int) -> None:
        """Passarela de pedestres sobre a rua horizontal, com escadas na grama."""
        g, c = self.g, self.cobertura
        a, b = g.passarela
        x0 = g.cx + lado * a if lado > 0 else g.cx - b
        largura = b - a
        meia = g.meia_rua + g.meio_fio + g.calcada + 46
        escada = 64
        deck = pygame.Rect(x0, g.cy - meia, largura, 2 * meia)
        # sombra projetada no asfalto e na grama
        c.rect((0, 0, 0, 70), deck.move(9, 10).inflate(0, 2 * escada))
        for sinal in (-1, 1):
            topo = deck.top - escada if sinal < 0 else deck.bottom
            degraus = pygame.Rect(x0 + 4, topo, largura - 8, escada)
            c.rect(Paleta.PASSARELA_SOMBRA, degraus)
            for k in range(0, escada, 8):
                y = degraus.top + k if sinal < 0 else degraus.bottom - k - 3
                c.rect(Paleta.PASSARELA, (degraus.x + 2, y, degraus.w - 4, 5))
        c.rect(Paleta.PASSARELA, deck)
        for k in range(deck.top + 12, deck.bottom - 6, 24):          # juntas do piso
            c.line(Paleta.PASSARELA_SOMBRA, (deck.left + 6, k), (deck.right - 6, k), 1)
        for x in (deck.left, deck.right - 5):                        # guarda-corpos
            c.rect(Paleta.AMARELO, (x, deck.top - escada, 5, deck.h + 2 * escada))
            c.rect(Paleta.AMARELO_ESCURO, (x + 3, deck.top - escada, 2, deck.h + 2 * escada))
