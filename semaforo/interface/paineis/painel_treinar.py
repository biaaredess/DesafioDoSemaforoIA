"""Aba 2: treinar a IA e acompanhar a curva de aprendizado."""
import pygame

from ...jogo import ControladorJogo
from ..formas import placa
from ..grafico import GraficoTreino
from ..tema import Escala, Fontes, Layout, Paleta
from ..texto import desenhar_paragrafo, desenhar_texto
from ..widgets import Botao, EstiloBotao
from .base import Painel

EXPLICACAO = ("A IA começa **sem saber nada**. Ela joga sozinha, em velocidade máxima, e ganha ou perde "
              "pontos conforme os carros andam ou ficam parados. Com o tempo, descobre sozinha quando "
              "vale a pena trocar o sinal.")


class PainelTreinar(Painel):
    def __init__(self, controlador: ControladorJogo):
        super().__init__(controlador)
        area = Layout.conteudo(0)
        self.area = area
        x, w = area.x, area.w
        self._fontes_texto = (Fontes.obter(Escala.BASE + 1, "texto"), Fontes.obter(Escala.BASE + 1, "texto_extra"))
        y = area.y + 116
        meio = (w - 10) // 2
        self.botao_treinar = Botao((x, y, meio, 64), "Começar o treino", controlador.iniciar_treino,
                                   EstiloBotao(Paleta.VERDE))
        self.botao_apagar = Botao((x + meio + 10, y, meio, 64), "Apagar o que ela aprendeu",
                                  controlador.apagar_aprendizado, EstiloBotao(Paleta.VERMELHO), Escala.BASE + 1)
        y += 82
        terco = (w - 16) // 3
        self.contadores = [
            ("Partidas", Paleta.VERDE, pygame.Rect(x, y, terco, 88)),
            ("Horas de trânsito", Paleta.AMARELO, pygame.Rect(x + terco + 8, y, terco, 88)),
            ("Curiosidade", Paleta.VERMELHO, pygame.Rect(x + 2 * (terco + 8), y, terco, 88)),
        ]
        self.valores = ["0", "0", "100%"]
        y += 104
        self.grafico = GraficoTreino((x, y, w, area.bottom - y - 34))
        self.y_legenda = self.grafico.rect.bottom + 10
        self.widgets = [self.botao_treinar, self.botao_apagar]

    def atualizar(self) -> None:
        ctrl = self.controlador
        self.botao_treinar.habilitado = not ctrl.ocupado
        self.botao_apagar.habilitado = not ctrl.ocupado and ctrl.treinada
        cfg = ctrl.config.treino
        t = ctrl.treinador
        if t is not None:
            episodios, horas, eps = t.episodio, t.passos_feitos // 3600, t.epsilon()
        elif ctrl.treinada:
            episodios, horas = cfg.episodios, cfg.episodios * cfg.passos_por_episodio // 3600
            eps = cfg.epsilon_minimo
        else:
            episodios, horas, eps = 0, 0, 1.0
        self.valores = [f"{episodios:,}".replace(",", "."), str(horas), f"{round(eps * 100)}%"]

    def desenhar(self, tela: pygame.Surface) -> None:
        f, fb = self._fontes_texto
        desenhar_paragrafo(tela, EXPLICACAO, pygame.Rect(self.area.x, self.area.y, self.area.w, 0),
                           f, fb, Paleta.TEXTO, Paleta.TEXTO, 1.3)
        super().desenhar(tela)
        rotulo_f = Fontes.obter(Escala.BASE - 1, "texto_forte")
        valor_f = Fontes.obter(32, "letreiro")
        for (rotulo, cor, r), valor in zip(self.contadores, self.valores):
            placa(tela, r, Paleta.PAPEL, cor, 4)
            desenhar_texto(tela, rotulo, rotulo_f, Paleta.CINZA, (r.centerx, r.y + 12), "midtop")
            desenhar_texto(tela, valor, valor_f, Paleta.TINTA, (r.centerx, r.bottom - 10), "midbottom")

        ctrl = self.controlador
        cfg = ctrl.config.treino
        self.grafico.desenhar(tela, ctrl.curva, ctrl.base_fixo, cfg.episodios, cfg.intervalo_curva)

        x, y = self.area.x, self.y_legenda
        fl = Fontes.obter(Escala.BASE, "texto_forte")
        tela.line(Paleta.VERDE, (x, y + 11), (x + 28, y + 11), 5)
        r = desenhar_texto(tela, "IA", fl, Paleta.TEXTO, (x + 38, y))
        for k in range(3):
            tela.line(Paleta.VERMELHO, (r.right + 30 + k * 12, y + 11), (r.right + 37 + k * 12, y + 11), 4)
        desenhar_texto(tela, "Semáforo comum", fl, Paleta.TEXTO, (r.right + 72, y))
        desenhar_texto(tela, "menos é melhor", fl, Paleta.TEXTO_SUAVE, (self.area.right, y), "topright")
