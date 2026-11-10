"""Componentes de interface: tudo é uma placa de cantos chanfrados."""
from dataclasses import dataclass
from typing import Any, Callable

import pygame

from .formas import placa, sombra
from .tema import Escala, Fontes, Paleta, clarear, escurecer, texto_sobre
from .texto import desenhar_texto


class Widget:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.visivel = True
        self.habilitado = True
        self.sob_mouse = False

    @property
    def ativo(self) -> bool:
        return self.visivel and self.habilitado

    def tratar_evento(self, evento: pygame.event.Event) -> bool:
        """Devolve True se consumiu o evento."""
        return False

    def desenhar(self, tela: pygame.Surface) -> None:
        raise NotImplementedError

    def _acompanhar_mouse(self, evento) -> None:
        if evento.type == pygame.MOUSEMOTION:
            self.sob_mouse = self.ativo and self.rect.collidepoint(evento.pos)


class Clicavel(Widget):
    """Base dos botões: clique completo (apertar e soltar em cima)."""

    def __init__(self, rect, ao_clicar: Callable[[], None]):
        super().__init__(rect)
        self.ao_clicar = ao_clicar
        self._pressionado = False

    @property
    def afundado(self) -> bool:
        return self._pressionado and self.sob_mouse

    def tratar_evento(self, evento) -> bool:
        self._acompanhar_mouse(evento)
        if not self.ativo:
            self._pressionado = False
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.rect.collidepoint(evento.pos):
            self._pressionado = True
            return True
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self._pressionado:
            self._pressionado = False
            if self.rect.collidepoint(evento.pos):
                self.ao_clicar()
            return True
        return False


@dataclass(frozen=True)
class EstiloBotao:
    cor: tuple                 # cor de identidade: o botão é sempre pintado com ela


class Botao(Clicavel):
    def __init__(self, rect, texto: str, ao_clicar: Callable[[], None], estilo: EstiloBotao,
                 tamanho: int = Escala.MEDIO, fonte: str = "texto_extra"):
        super().__init__(rect, ao_clicar)
        self.texto, self.estilo, self.tamanho, self.fonte = texto, estilo, tamanho, fonte

    def desenhar(self, tela) -> None:
        if not self.visivel:
            return
        cor = self.estilo.cor
        degrau = 4
        if not self.habilitado:
            # desativado continua colorido, só apagado (como uma lâmpada desligada)
            apagada = escurecer(cor, 0.42)
            corpo = pygame.Rect(self.rect.x, self.rect.y + degrau, self.rect.w, self.rect.h - degrau)
            placa(tela, corpo, apagada, escurecer(cor, 0.3), 3)
            cor_texto = escurecer(cor, 0.78)
        else:
            if self.sob_mouse:
                cor = clarear(cor, 0.18)
            afunda = degrau if self.afundado else 0
            base = pygame.Rect(self.rect.x, self.rect.y + degrau, self.rect.w, self.rect.h - degrau)
            corpo = pygame.Rect(self.rect.x, self.rect.y + afunda, self.rect.w, self.rect.h - degrau)
            placa(tela, base, escurecer(self.estilo.cor, 0.55))
            placa(tela, corpo, cor, escurecer(self.estilo.cor, 0.55), 3, filete=clarear(cor, 0.55))
            cor_texto = texto_sobre(cor)
        desenhar_texto(tela, self.texto, Fontes.obter(self.tamanho, self.fonte), cor_texto,
                       (corpo.centerx, corpo.centery + 1), "center")


class BotaoTrocar(Clicavel):
    """O grande botão vermelho da tela cheia, pintado na grama como uma placa."""

    def __init__(self, rect, ao_clicar: Callable[[], None]):
        super().__init__(rect, ao_clicar)
        self.aguardando = False    # troca em andamento: o botão fica "apagado"

    def desenhar(self, tela) -> None:
        if not self.visivel:
            return
        degrau = 8
        cor = escurecer(Paleta.VERMELHO, 0.72) if self.aguardando else Paleta.VERMELHO
        afunda = degrau - 2 if self.afundado else 0
        sombra(tela, self.rect, (6, degrau + 6), 60, chanfro=22)
        placa(tela, self.rect.move(0, degrau), Paleta.VERMELHO_ESCURO, chanfro=22)
        corpo = self.rect.move(0, afunda)
        placa(tela, corpo, cor, Paleta.BRANCO, 5, filete=Paleta.BRANCO, chanfro=22, recuo_filete=6)
        rotulo = Fontes.obter(44, "letreiro").render("TROCAR", True, Paleta.BRANCO)
        tela.blit(rotulo, rotulo.get_rect(center=(corpo.centerx, corpo.centery + 3)))


class BotaoFechar(Clicavel):
    def __init__(self, rect, ao_clicar: Callable[[], None]):
        super().__init__(rect, ao_clicar)

    def desenhar(self, tela) -> None:
        cor = Paleta.VERMELHO if self.sob_mouse else Paleta.TINTA
        placa(tela, self.rect, Paleta.PAPEL, cor, 3, chanfro=6)
        c, m = self.rect.center, self.rect.w // 4
        for a, b in (((-m, -m), (m, m)), ((-m, m), (m, -m))):
            tela.line(cor, (c[0] + a[0], c[1] + a[1]), (c[0] + b[0], c[1] + b[1]), 4)


class Abas(Widget):
    """Abas do cabeçalho, na ordem do semáforo: 1 vermelho, 2 amarelo, 3 verde.
    É uma sequência de verdade (jogar → treinar → entender), por isso os números."""

    CORES = (Paleta.VERMELHO, Paleta.AMARELO, Paleta.VERDE)

    def __init__(self, pos, largura: int, opcoes: list[tuple[str, str]], valor: str,
                 ao_mudar: Callable[[str], None]):
        self.fonte = Fontes.obter(Escala.BASE, "texto_extra")
        self.opcoes, self.valor, self.ao_mudar = opcoes, valor, ao_mudar
        larguras = [self.fonte.size(r)[0] + 64 for r, _ in opcoes]
        sobra = (largura - sum(larguras) - 8 * (len(opcoes) - 1)) / len(opcoes)
        self.rects, x = [], pos[0]
        for w in larguras:
            self.rects.append(pygame.Rect(round(x), pos[1], round(w + sobra), 48))
            x += w + sobra + 8
        super().__init__(self.rects[0].unionall(self.rects))
        self._hover = -1

    def tratar_evento(self, evento) -> bool:
        if evento.type == pygame.MOUSEMOTION:
            self._hover = next((i for i, r in enumerate(self.rects) if r.collidepoint(evento.pos)), -1)
            self.sob_mouse = self._hover >= 0
        if evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            for r, (_, valor) in zip(self.rects, self.opcoes):
                if r.collidepoint(evento.pos):
                    self.valor = valor
                    self.ao_mudar(valor)
                    return True
        return False

    def desenhar(self, tela) -> None:
        numero = Fontes.obter(20, "letreiro")
        for i, (r, (rotulo, valor)) in enumerate(zip(self.rects, self.opcoes)):
            cor = self.CORES[i % 3]
            ativa = valor == self.valor
            if ativa:
                placa(tela, r, cor, escurecer(cor, 0.55), 3, filete=clarear(cor, 0.55))
                cor_texto = texto_sobre(cor)
            else:
                fundo = escurecer(cor, 0.55 if i == self._hover else 0.42)
                placa(tela, r, fundo, escurecer(cor, 0.3), 3)
                cor_texto = Paleta.TEXTO
            selo = pygame.Rect(r.x + 10, r.y + 10, 28, 28)
            placa(tela, selo, Paleta.ESCURO if ativa else cor, chanfro=6)
            desenhar_texto(tela, str(i + 1), numero, cor if ativa else texto_sobre(cor),
                           (selo.centerx, selo.centery + 2), "center")
            # texto no meio do botão, com um pequeno respiro em relação ao número
            desenhar_texto(tela, rotulo, self.fonte, cor_texto, (r.centerx + 8, r.centery + 1), "center")


class Alternancia(Widget):
    """Placas vizinhas, uma selecionada de cada vez."""

    def __init__(self, pos, opcoes: list[tuple[str, Any]], valor: Any, ao_mudar: Callable[[Any], None],
                 cor_ativa=Paleta.AMARELO, altura: int = 42, padding: int = 18):
        self.fonte = Fontes.obter(Escala.BASE, "texto_forte")
        self.larguras = [self.fonte.size(r)[0] + 2 * padding for r, _ in opcoes]
        super().__init__((pos[0], pos[1], sum(self.larguras) + 6 * (len(opcoes) - 1), altura))
        self.opcoes, self.valor, self.ao_mudar, self.cor_ativa = opcoes, valor, ao_mudar, cor_ativa

    def _segmentos(self):
        x = self.rect.x
        for (rotulo, valor), w in zip(self.opcoes, self.larguras):
            yield rotulo, valor, pygame.Rect(x, self.rect.y, w, self.rect.h)
            x += w + 6

    def tratar_evento(self, evento) -> bool:
        self._acompanhar_mouse(evento)
        if self.ativo and evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
            for _, valor, r in self._segmentos():
                if r.collidepoint(evento.pos):
                    if valor != self.valor:
                        self.valor = valor
                        self.ao_mudar(valor)
                    return True
        return False

    def desenhar(self, tela) -> None:
        for rotulo, valor, r in self._segmentos():
            if valor == self.valor:
                placa(tela, r, self.cor_ativa, escurecer(self.cor_ativa, 0.55), 3, chanfro=7)
                cor = texto_sobre(self.cor_ativa)
            else:
                placa(tela, r, escurecer(self.cor_ativa, 0.42), escurecer(self.cor_ativa, 0.3), 3, chanfro=7)
                cor = Paleta.TEXTO
            desenhar_texto(tela, rotulo, self.fonte, cor, (r.centerx, r.centery + 1), "center")


class CampoTexto(Widget):
    """Campo de uma linha que aceita acentos (eventos TEXTINPUT do SDL)."""

    def __init__(self, rect, placeholder: str, ao_confirmar: Callable[[str], None], limite: int = 18):
        super().__init__(rect)
        self.placeholder, self.ao_confirmar, self.limite = placeholder, ao_confirmar, limite
        self.texto = ""
        self.focado = False
        self.fonte = Fontes.obter(Escala.SUBTITULO, "texto_forte")

    def tratar_evento(self, evento) -> bool:
        self._acompanhar_mouse(evento)
        if not self.ativo:
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.focado = self.rect.collidepoint(evento.pos)
            return self.focado
        if not self.focado:
            return False
        if evento.type == pygame.TEXTINPUT:
            self.texto = (self.texto + evento.text)[: self.limite]
            return True
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.ao_confirmar(self.texto)
            return True
        return False

    def desenhar(self, tela) -> None:
        placa(tela, self.rect, Paleta.PAPEL, Paleta.TINTA if self.focado else Paleta.CONCRETO_ESCURO, 3, chanfro=7)
        x, cy = self.rect.x + 16, self.rect.centery + 1
        if self.texto:
            fim = desenhar_texto(tela, self.texto, self.fonte, Paleta.TINTA, (x, cy), "midleft").right + 3
        else:
            desenhar_texto(tela, self.placeholder, self.fonte, Paleta.CONCRETO_ESCURO, (x, cy), "midleft")
            fim = x
        if self.focado and pygame.time.get_ticks() // 500 % 2 == 0:
            tela.line(Paleta.VERMELHO, (fim, cy - 13), (fim, cy + 12), 3)
