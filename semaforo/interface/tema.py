"""Identidade visual em modo escuro, com o fundo da cor do asfalto.

Conceito: placas e pintura de rua. Os blocos da interface são "placas" de
cantos chanfrados com um filete interno, como placas de trânsito. As três
cores do semáforo são as cores de identidade dos participantes, e os botões
são sempre pintados com elas.
"""
from pathlib import Path

import pygame

from ..jogo import ModoRodada
from .tela import Fonte


class Paleta:
    # trio do semáforo (vibrante)
    VERMELHO = (229, 32, 42)
    AMARELO = (255, 194, 14)
    VERDE = (23, 176, 74)
    LARANJA = (255, 128, 0)
    VERMELHO_ESCURO = (160, 16, 24)
    AMARELO_ESCURO = (196, 140, 0)
    VERDE_ESCURO = (12, 120, 48)

    # interface escura: o painel é o próprio asfalto
    FUNDO = (58, 59, 64)           # mesma cor do asfalto do cruzamento
    SUPERFICIE = (74, 76, 82)      # linhas do ranking, células vazias
    SUPERFICIE_BORDA = (104, 107, 115)
    ESCURO = (30, 32, 36)          # fundo de código, logotipo
    TEXTO = (246, 246, 246)        # mesma cor da pintura de rua
    TEXTO_SUAVE = (190, 194, 200)

    # placas brancas (tempos, temporizador, resultado): texto escuro por cima
    PAPEL = (255, 255, 255)
    CONCRETO = (232, 235, 229)
    CONCRETO_ESCURO = (206, 211, 203)
    TINTA = (35, 38, 44)
    CINZA = (98, 104, 112)
    BRANCO = (255, 255, 255)

    # cenário
    GRAMA = (104, 204, 38)
    GRAMA_CLARA = (132, 222, 58)
    GRAMA_ESCURA = (76, 170, 26)
    ARBUSTO = (46, 150, 40)
    ARBUSTO_CLARO = (84, 190, 54)
    CALCADA = (205, 208, 212)
    CALCADA_CLARA = (226, 228, 231)
    CALCADA_BORDA = (120, 125, 132)
    MEIO_FIO = (255, 200, 0)
    ASFALTO = (58, 59, 64)
    PINTURA = (246, 246, 246)
    PARAFUSO = (70, 74, 80)
    CAIXA_SEMAFORO = (34, 36, 40)
    VERMELHO_APAGADO = (92, 22, 24)
    AMARELO_APAGADO = (92, 72, 10)
    VERDE_APAGADO = (16, 78, 34)
    PASSARELA = (214, 216, 210)
    PASSARELA_SOMBRA = (150, 154, 150)

    CARROS = (
        (34, 70, 226),    # azul
        (240, 36, 44),    # vermelho
        (255, 196, 0),    # amarelo
        (34, 196, 76),    # verde
        (255, 120, 10),   # laranja
        (0, 172, 236),    # ciano
        (150, 64, 236),   # roxo
        (255, 72, 160),   # rosa
        (244, 244, 244),  # branco
    )
    VIDRO = (170, 220, 255)
    VIDRO_ESCURO = (92, 150, 210)
    FAROL = (255, 246, 190)
    LANTERNA = (255, 40, 40)

    IDENTIDADE = {
        ModoRodada.FIXO: VERMELHO,
        ModoRodada.VOCE: AMARELO,
        ModoRodada.IA: VERDE,
    }


def escurecer(cor, fator: float = 0.7):
    return tuple(max(0, int(c * fator)) for c in cor[:3])


def clarear(cor, fator: float = 0.35):
    return tuple(min(255, int(c + (255 - c) * fator)) for c in cor[:3])


def texto_sobre(cor):
    """Cor de texto legível sobre um fundo colorido."""
    r, g, b = cor[:3]
    return Paleta.TINTA if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else Paleta.BRANCO


class Fontes:
    """Bungee (letreiro urbano) para título e números; Barlow Semi Condensed
    (desenhada a partir de placas de rodovia) para o texto. Ambas embutidas."""

    PASTA = Path(__file__).resolve().parent / "recursos" / "fontes"
    ARQUIVOS = {
        "letreiro": "Bungee-Regular.ttf",
        "texto": "BarlowSemiCondensed-Medium.ttf",
        "texto_medio": "BarlowSemiCondensed-SemiBold.ttf",
        "texto_forte": "BarlowSemiCondensed-Bold.ttf",
        "texto_extra": "BarlowSemiCondensed-ExtraBold.ttf",
        "mono": "DejaVuSansMono.ttf",
        "mono_forte": "DejaVuSansMono-Bold.ttf",
    }
    _cache: dict[tuple[str, int], Fonte] = {}

    @classmethod
    def obter(cls, tamanho: int, estilo: str = "texto") -> Fonte:
        """Fonte em tamanho lógico; os pixels reais acompanham a resolução da janela."""
        chave = (estilo, tamanho)
        if chave not in cls._cache:
            cls._cache[chave] = Fonte(str(cls.PASTA / cls.ARQUIVOS[estilo]), tamanho,
                                      negrito_falso=estilo != "texto")
        return cls._cache[chave]


class Escala:
    """Escala tipográfica (razão ~1,25). Nada menor que 16 px na tela."""

    BASE = 18
    MEDIO = 21
    SUBTITULO = 24
    TITULO = 30
    NUMERO = 40


class Layout:
    LARGURA = 1280
    ALTURA = 720
    LARGURA_PALCO = 720            # cruzamento quando o painel está aberto
    PAINEL_X = 720
    MARGEM = 28
    CHANFRO = 9                    # corte a 45° dos cantos das placas

    @classmethod
    def conteudo(cls, painel_x: int = PAINEL_X) -> pygame.Rect:
        return pygame.Rect(painel_x + cls.MARGEM, 150, cls.LARGURA - cls.PAINEL_X - 2 * cls.MARGEM,
                           cls.ALTURA - 150 - 16)
