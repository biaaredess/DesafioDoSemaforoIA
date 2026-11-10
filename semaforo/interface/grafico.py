"""Gráfico de linha do treino: tempo perdido pela IA × semáforo comum."""
import math

import pygame

from .formas import placa
from .tema import Fontes, Paleta
from .texto import desenhar_texto


class GraficoTreino:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    @staticmethod
    def _teto(valor: float) -> tuple[float, float]:
        """Topo do eixo Y e intervalo das linhas de grade, em números redondos."""
        bruto = max(valor, 1) / 3
        magnitude = 10 ** math.floor(math.log10(bruto))
        passo = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= bruto)
        return passo * math.ceil(valor / passo), passo

    def desenhar(self, tela: pygame.Surface, curva: list[float], base_fixo: float,
                 episodios: int, intervalo: int) -> None:
        r = self.rect
        placa(tela, r, Paleta.ESCURO, Paleta.SUPERFICIE_BORDA, 3)
        esq, dir_, topo, baixo = r.x + 74, r.right - 24, r.y + 22, r.bottom - 38
        fonte = Fontes.obter(16, "texto_medio")
        topo_y, passo = self._teto(max([base_fixo * 1.15, *curva]))

        def py(v):
            return baixo - (baixo - topo) * min(v, topo_y) / topo_y

        def px(e):
            return esq + (dir_ - esq) * e / episodios

        v = 0.0
        while v <= topo_y + 1e-6:
            y = py(v)
            tela.line(Paleta.SUPERFICIE, (esq, y), (dir_, y), 2)
            rotulo = "0" if v == 0 else (f"{v / 1000:g} mil s" if v >= 1000 else f"{v:g} s")
            desenhar_texto(tela, rotulo, fonte, Paleta.TEXTO_SUAVE, (esq - 10, y), "midright")
            v += passo
        for e in (0, episodios // 3, 2 * episodios // 3, episodios):
            ancora = "midtop" if 0 < e < episodios else ("topleft" if e == 0 else "topright")
            texto = f"{e:,}".replace(",", ".") + (" partidas" if e == episodios else "")
            desenhar_texto(tela, texto, fonte, Paleta.TEXTO_SUAVE, (px(e), baixo + 10), ancora)

        y = py(base_fixo)
        for x in range(int(esq), int(dir_), 14):
            tela.line(Paleta.VERMELHO, (x, y), (min(x + 8, dir_), y), 4)

        if curva:
            pontos = [(px(i * intervalo), py(valor)) for i, valor in enumerate(curva)]
            if len(pontos) > 1:
                tela.lines(Paleta.VERDE, False, pontos, 5)
            x, y = pontos[-1]
            placa(tela, pygame.Rect(x - 8, y - 8, 16, 16), Paleta.VERDE, Paleta.TEXTO, 2, chanfro=4)
