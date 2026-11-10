"""Aba 1: tempos de cada participante, botões para jogar e ranking do dia."""
import pygame

from ...jogo import ControladorJogo, ModoRodada
from ..formas import placa
from ..tema import Escala, Fontes, Layout, Paleta, texto_sobre
from ..texto import desenhar_texto
from ..widgets import Botao, EstiloBotao
from .base import Painel


class PainelJogar(Painel):
    ORDEM = (ModoRodada.FIXO, ModoRodada.VOCE, ModoRodada.IA)
    NOMES = {ModoRodada.FIXO: "Semáforo comum", ModoRodada.VOCE: "Você", ModoRodada.IA: "IA"}

    def __init__(self, controlador: ControladorJogo):
        super().__init__(controlador)
        area = Layout.conteudo(0)
        self.area = area
        terco = (area.w - 16) // 3
        self.placas = [pygame.Rect(area.x + i * (terco + 8), area.y, terco, 124) for i in range(3)]

        y = area.y + 146

        def botao(i, texto, modo):
            return Botao((area.x + i * (terco + 8), y, terco, 70), texto,
                         lambda: controlador.iniciar_rodada(modo),
                         EstiloBotao(Paleta.IDENTIDADE[modo]), Escala.MEDIO + 1)
        self.botoes = [
            botao(0, "Jogar", ModoRodada.VOCE),
            botao(1, "IA joga", ModoRodada.IA),
            botao(2, "Semáforo", ModoRodada.FIXO),
        ]
        self.y_ranking = y + 100
        self.widgets = list(self.botoes)

    def atualizar(self) -> None:
        for b in self.botoes:
            b.habilitado = not self.controlador.ocupado

    def desenhar(self, tela: pygame.Surface) -> None:
        self._desenhar_tempos(tela)
        super().desenhar(tela)
        self._desenhar_ranking(tela)

    def _desenhar_tempos(self, tela) -> None:
        placar = self.controlador.placar
        nome_f = Fontes.obter(Escala.BASE, "texto_extra")
        numero_f = Fontes.obter(Escala.NUMERO, "letreiro")
        unidade_f = Fontes.obter(Escala.MEDIO, "texto_extra")
        for rect, modo in zip(self.placas, self.ORDEM):
            cor = Paleta.IDENTIDADE[modo]
            res = placar.obter(modo)
            placa(tela, rect, Paleta.PAPEL, cor, 5)     # sempre placa branca com a borda da cor
            tinta = Paleta.TINTA
            nome = res.nome if res else self.NOMES[modo]
            desenhar_texto(tela, nome, nome_f, tinta, (rect.centerx, rect.y + 18), "midtop")
            if res is None:
                desenhar_texto(tela, "—", numero_f, Paleta.CONCRETO_ESCURO, (rect.centerx, rect.y + 80), "center")
                continue
            numero = numero_f.render(str(res.tempo_perdido), True, tinta)
            unidade = unidade_f.render("s", True, tinta)
            total = numero.get_width() + 4 + unidade.get_width()
            x = rect.centerx - total // 2
            tela.blit(numero, numero.get_rect(midleft=(x, rect.y + 82)))
            tela.blit(unidade, unidade.get_rect(bottomleft=(x + numero.get_width() + 4, rect.y + 96)))

    def _desenhar_ranking(self, tela) -> None:
        ctrl = self.controlador
        x, w, y = self.area.x, self.area.w, self.y_ranking
        titulo = Fontes.obter(Escala.SUBTITULO, "letreiro")
        r = desenhar_texto(tela, "RANKING DO DIA", titulo, Paleta.TEXTO, (x + w // 2, y), "midtop")
        meio = r.centery - 1
        tela.line(Paleta.AMARELO, (x, meio), (r.left - 16, meio), 3)
        tela.line(Paleta.AMARELO, (r.right + 16, meio), (x + w, meio), 3)

        itens = [(e.nome, e.tempo_perdido, None) for e in ctrl.ranking.do_dia(10)]
        ia = ctrl.placar.ia_de_referencia()
        if ia:
            itens.append(("IA treinada", ia.tempo_perdido, Paleta.VERDE))
        fixo = ctrl.placar.obter(ModoRodada.FIXO)
        if fixo:
            itens.append(("Semáforo comum", fixo.tempo_perdido, Paleta.VERMELHO))
        itens.sort(key=lambda item: item[1])

        y = r.bottom + 16
        altura, vao = 38, 6
        vagas = (self.area.bottom - y + vao) // (altura + vao)
        nome_f = Fontes.obter(Escala.MEDIO, "texto_forte")
        pos_f = Fontes.obter(Escala.BASE, "letreiro")
        tempo_f = Fontes.obter(Escala.BASE + 2, "letreiro")
        unidade_f = Fontes.obter(Escala.BASE + 1, "texto_extra")
        medalhas = (Paleta.AMARELO, Paleta.CONCRETO_ESCURO, (232, 150, 80))
        posicao = 0
        for k in range(vagas):
            linha = pygame.Rect(x, y + k * (altura + vao), w, altura)
            if k >= len(itens):
                placa(tela, linha, Paleta.SUPERFICIE, chanfro=7)
                continue
            nome, valor, referencia = itens[k]
            selo = pygame.Rect(linha.x, linha.y, 46, altura)
            if referencia:
                placa(tela, linha, Paleta.FUNDO, referencia, 3, chanfro=7)
                placa(tela, selo, referencia, chanfro=7)
                cor = Paleta.TEXTO_SUAVE
            else:
                posicao += 1
                placa(tela, linha, Paleta.SUPERFICIE, chanfro=7)
                cor_selo = medalhas[posicao - 1] if posicao <= 3 else Paleta.ESCURO
                placa(tela, selo, cor_selo, chanfro=7)
                desenhar_texto(tela, str(posicao), pos_f, texto_sobre(cor_selo),
                               (selo.centerx, selo.centery + 2), "center")
                cor = Paleta.TEXTO
            desenhar_texto(tela, nome, nome_f, cor, (selo.right + 14, linha.centery + 1), "midleft")
            u = desenhar_texto(tela, "s", unidade_f, cor, (linha.right - 14, linha.centery + 1), "midright")
            desenhar_texto(tela, str(valor), tempo_f, cor, (u.left - 4, linha.centery + 2), "midright")
