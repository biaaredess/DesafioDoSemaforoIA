"""O palco: cenário animado, temporizador, botão de troca e cartões de resultado.

O cenário tem a largura da janela inteira. Com o painel aberto, a câmera
mostra só o quadrado do cruzamento; na rodada de quem joga, ela abre até as
bordas enquanto o painel sai pela direita (``abertura`` vai de 0 a 1).
"""
from typing import Callable

import pygame

from ..jogo import ControladorJogo
from ..simulacao import Direcao
from .animacao import AnimadorCarros
from .cenario import Cenario
from .formas import placa, sombra
from .geometria import GeometriaCruzamento
from .sprites import DesenhistaSemaforo, FabricaCarros
from .tela import Resolucao, Tela
from .tema import Escala, Fontes, Layout, Paleta, escurecer
from .texto import altura_paragrafo, desenhar_paragrafo, desenhar_texto
from .widgets import Botao, BotaoFechar, BotaoTrocar, CampoTexto, EstiloBotao


class Cartao:
    """Resultado de uma rodada, sobre o cruzamento. Pode trazer o campo do ranking."""

    LARGURA = 470
    PADDING = 34

    ESTILOS = {
        "rotulo": ("texto_forte", Escala.SUBTITULO, Paleta.TINTA),
        "grande": ("letreiro", 76, Paleta.TINTA),
        "texto": ("texto_medio", Escala.MEDIO, Paleta.CINZA),
        "destaque": ("texto_extra", Escala.SUBTITULO + 2, Paleta.VERDE_ESCURO),
        "alerta": ("texto_extra", Escala.SUBTITULO + 2, Paleta.VERMELHO),
    }

    def __init__(self, itens: list[tuple[str, str]], cor: tuple = Paleta.TINTA,
                 ao_salvar_nome: Callable[[str], None] | None = None,
                 ao_fechar: Callable[[], None] | None = None):
        self.itens, self.cor = itens, cor
        self.ao_salvar_nome, self.ao_fechar = ao_salvar_nome, ao_fechar
        self.widgets = []
        self.campo: CampoTexto | None = None
        self.rect = pygame.Rect(0, 0, self.LARGURA, 0)

    def _fonte(self, tipo: str):
        estilo, tamanho, cor = self.ESTILOS[tipo]
        return Fontes.obter(tamanho, estilo), cor

    def posicionar(self, centro) -> None:
        largura = self.LARGURA - 2 * self.PADDING
        altura = self.PADDING + 14
        for tipo, texto in self.itens:
            f, _ = self._fonte(tipo)
            altura += altura_paragrafo(texto, largura, f, f, 1.15) + 2
        if self.ao_salvar_nome:
            altura += 86
        altura += self.PADDING - 6
        antigo = self.rect.topleft
        self.rect = pygame.Rect(0, 0, self.LARGURA, altura)
        self.rect.center = centro
        if not self.widgets:
            self._criar_widgets(largura)
        else:
            dx, dy = self.rect.x - antigo[0], self.rect.y - antigo[1]
            for w in self.widgets:
                w.rect.move_ip(dx, dy)

    def _criar_widgets(self, largura: int) -> None:
        if self.ao_fechar:
            self.widgets.append(BotaoFechar((self.rect.right - 50, self.rect.y + 14, 36, 36), self.ao_fechar))
        if self.ao_salvar_nome:
            y = self.rect.bottom - self.PADDING - 58
            self.campo = CampoTexto((self.rect.x + self.PADDING, y, largura - 150, 56), "Seu nome", self._salvar)
            self.campo.focado = True
            salvar = Botao((self.campo.rect.right + 10, y, 140, 60), "Salvar",
                           lambda: self._salvar(self.campo.texto),
                           EstiloBotao(Paleta.AMARELO), Escala.SUBTITULO)
            self.widgets += [self.campo, salvar]

    def _salvar(self, nome: str) -> None:
        self.ao_salvar_nome(nome)
        if self.ao_fechar:
            self.ao_fechar()

    def tratar_evento(self, evento) -> bool:
        consumiu = False
        for w in self.widgets:
            if w.tratar_evento(evento) and evento.type != pygame.MOUSEMOTION:
                consumiu = True
                break
        if not consumiu and evento.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            consumiu = self.rect.collidepoint(evento.pos) and bool(self.widgets)
        return consumiu

    def desenhar(self, tela: pygame.Surface) -> None:
        sombra(tela, self.rect, (10, 12), 70, chanfro=16)
        placa(tela, self.rect, Paleta.PAPEL, Paleta.TINTA, 4, filete=self.cor, chanfro=16, recuo_filete=7)
        y = self.rect.y + self.PADDING + 14
        largura = self.LARGURA - 2 * self.PADDING
        for tipo, texto in self.itens:
            f, cor = self._fonte(tipo)
            area = pygame.Rect(self.rect.x + self.PADDING, y, largura, 0)
            y += desenhar_paragrafo(tela, texto, area, f, f, cor, cor, 1.15, centralizado=True) + 2
        for w in self.widgets:
            w.desenhar(tela)


class Palco:
    DESLOCAMENTO_FECHADO = (Layout.LARGURA - Layout.LARGURA_PALCO) // 2   # 280 px

    def __init__(self, controlador: ControladorJogo, ao_clicar: Callable[[], None]):
        self.controlador = controlador
        self.ao_clicar = ao_clicar
        self.geometria = GeometriaCruzamento(Layout.LARGURA, Layout.ALTURA, controlador.config.simulacao)
        self.cenario = Cenario(self.geometria)
        self.fabrica = FabricaCarros(self.geometria.carro_comprimento, self.geometria.carro_largura)
        self.semaforos = DesenhistaSemaforo()
        self.animador = AnimadorCarros(self.geometria, self.fabrica)
        self.cartao: Cartao | None = None
        self.botao_trocar = BotaoTrocar((0, 0, 320, 112), controlador.pedir_troca)
        self.botao_trocar.visivel = False
        self.abertura = 0.0

    # ----- câmera -----
    @property
    def x0(self) -> float:
        """Coluna do cenário que aparece na borda esquerda da tela."""
        return self.DESLOCAMENTO_FECHADO * (1 - self.abertura)

    @property
    def rect(self) -> pygame.Rect:
        largura = Layout.LARGURA_PALCO + (Layout.LARGURA - Layout.LARGURA_PALCO) * self.abertura
        return pygame.Rect(0, 0, round(largura), Layout.ALTURA)

    def _na_tela(self, x: float, y: float) -> tuple[float, float]:
        return x - self.x0, y

    # ----- cartões -----
    def mostrar_cartao(self, cartao: Cartao | None) -> None:
        self.cartao = cartao
        if cartao:
            cartao.posicionar(self.rect.center)

    def fechar_cartao(self) -> None:
        self.cartao = None

    @property
    def digitando(self) -> bool:
        return bool(self.cartao and self.cartao.campo and self.cartao.campo.focado)

    # ----- eventos -----
    def tratar_evento(self, evento) -> bool:
        if self.cartao and self.cartao.tratar_evento(evento):
            return True
        if self.botao_trocar.visivel and self.botao_trocar.tratar_evento(evento):
            return True
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.rect.collidepoint(evento.pos):
            if self.controlador.rodada_humana:
                self.ao_clicar()
            elif self.cartao and not self.cartao.widgets:
                self.cartao = None      # cartão de máquina: um clique dispensa
            return True
        return False

    @property
    def sob_mouse(self) -> bool:
        cartao = bool(self.cartao and any(w.sob_mouse for w in self.cartao.widgets))
        return cartao or (self.botao_trocar.visivel and self.botao_trocar.sob_mouse)

    # ----- desenho -----
    def desenhar(self, tela: Tela) -> None:
        if self.cenario.k != Resolucao.k:      # a janela mudou de tamanho: redesenha o cenário
            self.cenario = Cenario(self.geometria)
        ctrl = self.controlador
        cruz = ctrl.cruzamento_visivel
        self.animador.sincronizar(cruz)
        area = self.rect
        anterior = tela.get_clip()
        tela.set_clip(area)

        tela.blit(self.cenario.superficie, (-self.x0, 0))
        self.animador.desenhar(tela, (-self.x0, 0), ctrl.fracao_passo)
        self._desenhar_semaforos(tela, cruz)
        tela.blit(self.cenario.cobertura, (-self.x0, 0))
        self._desenhar_espera(tela)

        if ctrl.rodada is not None:
            self._desenhar_temporizador(tela)
        b = self.botao_trocar
        b.visivel = ctrl.rodada_humana
        if b.visivel:
            x, y = self._na_tela(self.geometria.cx + 330, Layout.ALTURA - 96)
            b.rect.center = (round(x), round(y))
            b.aguardando = not cruz.semaforo.pode_trocar
            b.desenhar(tela)
        if self.cartao:
            self.cartao.posicionar(area.center)
            self.cartao.desenhar(tela)
        tela.set_clip(anterior)

    def _desenhar_semaforos(self, tela, cruz) -> None:
        for direcao in Direcao:
            horizontal = direcao in (Direcao.NORTE, Direcao.SUL)
            sprite = self.semaforos.sprite(cruz.semaforo.cor(direcao.eixo), horizontal)
            x, y = self._na_tela(*self.geometria.posicao_semaforo(direcao))
            tela.blit(sprite, sprite.get_rect(center=(x, y)))

    def _desenhar_espera(self, tela) -> None:
        """Placa "+N" na borda visível para os carros da fila que estão fora da tela."""
        g, area = self.geometria, self.rect
        lateral = g.meia_rua + g.meio_fio + g.calcada / 2
        alcance = {
            Direcao.NORTE: g.cy, Direcao.SUL: g.cy,
            Direcao.LESTE: self.x0 + area.w - g.cx, Direcao.OESTE: g.cx - self.x0,
        }
        fonte = Fontes.obter(20, "letreiro")
        m = 24
        for d in Direcao:
            n = self.animador.fora_de_vista(d, alcance[d])
            if not n:
                continue
            pos = {
                Direcao.NORTE: (g.cx - lateral, m),
                Direcao.SUL: (g.cx + lateral, g.altura - m),
                Direcao.LESTE: (g.cx + alcance[d] - m - 6, g.cy - lateral),
                Direcao.OESTE: (g.cx - alcance[d] + m + 6, g.cy + lateral),
            }[d]
            x, y = self._na_tela(*pos)
            rotulo = fonte.render(f"+{n}", True, Paleta.BRANCO)
            caixa = rotulo.get_rect(center=(x, y)).inflate(18, 10)
            placa(tela, caixa, Paleta.VERMELHO, Paleta.BRANCO, 2, chanfro=6)
            tela.blit(rotulo, rotulo.get_rect(center=(caixa.centerx, caixa.centery + 2)))

    def _desenhar_temporizador(self, tela) -> None:
        """Placa branca na grama com os segundos que faltam e uma faixa que esvazia."""
        ctrl = self.controlador
        x, y = self._na_tela(self.geometria.cx - 250, 86)
        r = pygame.Rect(0, 0, 196, 104)
        r.center = (round(x), round(y))
        sombra(tela, r, (7, 9), 70, chanfro=14)
        placa(tela, r, Paleta.BRANCO, Paleta.TINTA, 4, filete=Paleta.TINTA, chanfro=14, recuo_filete=6)
        restante = ctrl.tempo_restante
        desenhar_texto(tela, str(restante), Fontes.obter(52, "letreiro"), Paleta.TINTA,
                       (r.centerx, r.centery - 4), "center")
        fracao = restante / ctrl.config.rodada.passos
        barra = pygame.Rect(r.x + 22, r.bottom - 26, r.w - 44, 8)
        tela.rect(Paleta.CONCRETO, barra)
        cor = Paleta.VERDE if fracao > 0.5 else (Paleta.AMARELO if fracao > 0.2 else Paleta.VERMELHO)
        tela.rect(cor, (barra.x, barra.y, round(barra.w * fracao), barra.h))
        tela.rect(escurecer(Paleta.CONCRETO, 0.8), barra, 1)
