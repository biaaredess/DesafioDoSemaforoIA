"""Aba 3: como a IA pensa — os três passos, o código do Q-learning e o "cérebro" aprendido."""
import keyword
import re

import pygame

from ...ia import Acao
from ...jogo import ControladorJogo
from ..formas import placa
from ..tema import Escala, Fontes, Layout, Paleta, texto_sobre
from ..texto import desenhar_paragrafo, desenhar_texto
from ..widgets import Alternancia, Widget
from .base import Painel

CODIGO_IA = '''# Ninguém escreveu quando trocar o sinal.
# A IA guarda uma "nota" para cada situação e cada escolha.
def escolher(situacao):
    if random() < curiosidade:  # às vezes testa algo novo
        return sortear(["manter", "trocar"])
    return maior_nota(Q[situacao])  # senão, usa o que sabe

def aprender(situacao, escolha, pontos, depois):
    futuro = max(Q[depois])
    Q[situacao][escolha] += taxa * (
        pontos + 0.9 * futuro - Q[situacao][escolha])

# pontos = −1 por segundo para cada carro parado'''

PASSOS = (
    ("Ela olha", "Quantos carros esperam no verde e no vermelho, e há quanto tempo o sinal abriu.",
     Paleta.VERMELHO),
    ("Ela escolhe", "Só duas opções: manter o sinal como está ou trocar.", Paleta.AMARELO),
    ("Ela ganha pontos", "Perde 1 ponto por segundo para cada carro parado. Quer perder o mínimo.",
     Paleta.VERDE),
)


class BlocoCodigo(Widget):
    """Código Python com realce de sintaxe simples, em tons que funcionam no claro."""

    TOKEN = re.compile(r'(#.*$)|("[^"]*")|(\b\d+(?:\.\d+)?\b)|([A-Za-z_]\w*)|(\s+)|(.)', re.M)
    TAMANHO = 16

    def __init__(self, rect, codigo: str):
        super().__init__(rect)
        self.codigo = codigo
        self.fonte = Fontes.obter(self.TAMANHO, "mono")
        self.fonte_forte = Fontes.obter(self.TAMANHO, "mono_forte")

    @classmethod
    def altura_para(cls, codigo: str) -> int:
        return (codigo.count("\n") + 1) * (Fontes.obter(cls.TAMANHO, "mono").get_height() + 3) + 36

    def desenhar(self, tela) -> None:
        placa(tela, self.rect, Paleta.ESCURO, Paleta.SUPERFICIE_BORDA, 3)
        y = self.rect.y + 18
        altura = self.fonte.get_height() + 3
        for linha in self.codigo.split("\n"):
            x = self.rect.x + 22
            for m in self.TOKEN.finditer(linha):
                texto, fonte = m.group(0), self.fonte
                if m.group(1):
                    cor = (140, 148, 160)
                elif m.group(2):
                    cor = Paleta.VERDE
                elif m.group(3):
                    cor = Paleta.LARANJA
                elif m.group(4) and keyword.iskeyword(texto):
                    cor, fonte = Paleta.AMARELO, self.fonte_forte
                elif m.group(4) and texto in ("max", "random"):
                    cor = (110, 190, 255)
                else:
                    cor = Paleta.TEXTO
                superficie = fonte.render(texto, True, cor)
                tela.blit(superficie, (x, y))
                x += superficie.get_width()
            y += altura


class TelaPensa:
    """Ocupa o lugar do cruzamento na aba 3: os três passos e o código."""

    def __init__(self):
        m = 32
        self.rect = pygame.Rect(0, 0, Layout.LARGURA_PALCO, Layout.ALTURA)
        self.x, self.w = m, self.rect.w - 2 * m
        self.y_codigo = 252
        altura = BlocoCodigo.altura_para(CODIGO_IA)
        self.codigo = BlocoCodigo((self.x, self.y_codigo + 44, self.w, altura), CODIGO_IA)

    def tratar_evento(self, evento) -> bool:
        return False

    sob_mouse = False

    def desenhar(self, tela: pygame.Surface) -> None:
        tela.rect(Paleta.FUNDO, self.rect)
        x, w = self.x, self.w
        largura = (w - 24) // 3
        titulo_f = Fontes.obter(Escala.BASE + 1, "texto_extra")
        corpo_f = Fontes.obter(Escala.BASE, "texto")
        numero_f = Fontes.obter(22, "letreiro")
        for i, (titulo, texto, cor) in enumerate(PASSOS):
            card = pygame.Rect(x + i * (largura + 12), 36, largura, 184)
            placa(tela, card, Paleta.SUPERFICIE, cor, 4)
            selo = pygame.Rect(card.x + 16, card.y + 16, 36, 36)
            placa(tela, selo, cor, chanfro=7)
            desenhar_texto(tela, str(i + 1), numero_f, texto_sobre(cor), (selo.centerx, selo.centery + 2), "center")
            desenhar_texto(tela, titulo, titulo_f, Paleta.TEXTO, (selo.right + 10, selo.centery + 1), "midleft")
            desenhar_paragrafo(tela, texto, pygame.Rect(card.x + 16, card.y + 66, card.w - 32, 0),
                               corpo_f, corpo_f, Paleta.TEXTO, entrelinha=1.25)

        desenhar_texto(tela, "O código da IA que aprende", Fontes.obter(Escala.SUBTITULO, "texto_extra"),
                       Paleta.TEXTO, (x, self.y_codigo))
        self.codigo.desenhar(tela)


class PainelPensa(Painel):
    """O "cérebro": para cada situação, a ação que a IA aprendeu."""

    def __init__(self, controlador: ControladorJogo):
        super().__init__(controlador)
        self.area = Layout.conteudo(0)
        self.verde_antigo = True
        self.alternancia = Alternancia((self.area.x, self.area.y + 44),
                                       [("Verde aberto há 5 s ou mais", True), ("Verde acabou de abrir", False)],
                                       True, self._mudar)
        self.widgets = [self.alternancia]

    def _mudar(self, valor: bool) -> None:
        self.verde_antigo = valor

    def desenhar(self, tela: pygame.Surface) -> None:
        ctrl = self.controlador
        x, y, w = self.area.x, self.area.y, self.area.w
        desenhar_texto(tela, "O CÉREBRO DA IA", Fontes.obter(Escala.SUBTITULO, "letreiro"), Paleta.TEXTO, (x, y))
        super().desenhar(tela)

        obs = ctrl.observador
        rotulos = obs.ROTULOS_FILA
        n = len(rotulos)
        eixo_y, cab_col, vao = 30, 58, 4
        topo = y + 104
        cel_w = (w - eixo_y - cab_col - vao * n) // n
        cel_h = 50
        rotulo_f = Fontes.obter(Escala.BASE, "texto_extra")
        celula_f = Fontes.obter(Escala.BASE - 1, "texto_extra")
        eixo_f = Fontes.obter(Escala.BASE - 1, "texto_extra")

        grade_altura = 30 + n * (cel_h + vao)
        texto_y = eixo_f.render("Carros esperando no verde", True, Paleta.VERDE).rotacionar(90)
        tela.blit(texto_y, texto_y.get_rect(center=(x + eixo_y // 2 - 4, topo + 30 + (grade_altura - 30) / 2)))

        gx = x + eixo_y + cab_col
        for j, r in enumerate(rotulos):
            desenhar_texto(tela, r, rotulo_f, Paleta.TEXTO, (gx + j * (cel_w + vao) + cel_w / 2, topo + 12), "center")
        for i, rv in enumerate(rotulos):
            cy = topo + 30 + i * (cel_h + vao)
            desenhar_texto(tela, rv, rotulo_f, Paleta.TEXTO, (gx - 12, cy + cel_h / 2), "midright")
            for j in range(n):
                estado = obs.codificar(i, j, self.verde_antigo)
                acao = ctrl.agente.preferencia(estado) if ctrl.treinada else None
                cel = pygame.Rect(gx + j * (cel_w + vao), cy, cel_w, cel_h)
                if acao is None:
                    placa(tela, cel, Paleta.SUPERFICIE, chanfro=6)
                elif acao is Acao.TROCAR:
                    placa(tela, cel, Paleta.AMARELO, chanfro=6)
                    desenhar_texto(tela, "trocar", celula_f, Paleta.TINTA, cel.center, "center")
                else:
                    placa(tela, cel, Paleta.VERDE, chanfro=6)
                    desenhar_texto(tela, "manter", celula_f, Paleta.BRANCO, cel.center, "center")
        base = topo + grade_altura + 6
        desenhar_texto(tela, "Carros esperando no vermelho", eixo_f, Paleta.VERMELHO,
                       (gx + (n * (cel_w + vao)) / 2, base), "midtop")

        nota = ("Ninguém pintou esta tabela: a IA a preencheu sozinha durante o treino."
                if ctrl.treinada else "Treine a IA na aba 2 para preencher a tabela.")
        desenhar_paragrafo(tela, nota, pygame.Rect(x, base + 40, w, 0), Fontes.obter(Escala.BASE, "texto"),
                           Fontes.obter(Escala.BASE, "texto_extra"), Paleta.TEXTO, entrelinha=1.3)
