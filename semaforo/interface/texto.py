"""Utilitários de texto: alinhamento, quebra de linha e negrito com **marcação**."""
import pygame


def desenhar_texto(tela: pygame.Surface, texto: str, fonte: pygame.font.Font, cor,
                   pos, ancora: str = "topleft") -> pygame.Rect:
    superficie = fonte.render(texto, True, cor)
    rect = superficie.get_rect(**{ancora: pos})
    tela.blit(superficie, rect)
    return rect


def _palavras(texto: str):
    """Divide em (palavra, negrito, colada). Trechos entre ** ficam em negrito;
    "colada" indica que não havia espaço antes (ex.: pontuação logo após um negrito)."""
    anterior_sem_espaco = False
    for i, trecho in enumerate(texto.split("**")):
        negrito = i % 2 == 1
        for j, palavra in enumerate(trecho.split(" ")):
            if palavra:
                yield palavra, negrito, j == 0 and anterior_sem_espaco
        if trecho:
            anterior_sem_espaco = not trecho.endswith(" ")


def quebrar_linhas(texto: str, fonte: pygame.font.Font, fonte_negrito: pygame.font.Font,
                   largura: int) -> list[list[tuple[str, bool, bool]]]:
    linhas, atual, largura_atual = [], [], 0
    espaco = fonte.size(" ")[0]
    for paragrafo in texto.split("\n"):
        for palavra, negrito, colada in _palavras(paragrafo):
            w = (fonte_negrito if negrito else fonte).size(palavra)[0]
            extra = w if (not atual or colada) else espaco + w
            if atual and not colada and largura_atual + extra > largura:
                linhas.append(atual)
                atual, largura_atual = [], 0
                extra = w
            atual.append((palavra, negrito, colada))
            largura_atual += extra
        linhas.append(atual)
        atual, largura_atual = [], 0
    return linhas


def desenhar_paragrafo(tela: pygame.Surface, texto: str, rect: pygame.Rect,
                       fonte: pygame.font.Font, fonte_negrito: pygame.font.Font,
                       cor, cor_negrito=None, entrelinha: float = 1.35,
                       centralizado: bool = False) -> int:
    """Desenha texto com quebra automática. Devolve a altura usada."""
    cor_negrito = cor_negrito or cor
    altura_linha = int(fonte.get_height() * entrelinha)
    espaco = fonte.size(" ")[0]
    y = rect.y
    for linha in quebrar_linhas(texto, fonte, fonte_negrito, rect.w):
        pedacos = [((fonte_negrito if n else fonte).render(p, True, cor_negrito if n else cor), c)
                   for p, n, c in linha]
        total = sum(s.get_width() + (0 if (i == 0 or c) else espaco) for i, (s, c) in enumerate(pedacos))
        x = rect.x + (rect.w - total) // 2 if centralizado else rect.x
        for i, (s, colada) in enumerate(pedacos):
            if i and not colada:
                x += espaco
            tela.blit(s, (x, y))
            x += s.get_width()
        y += altura_linha
    return y - rect.y


def altura_paragrafo(texto: str, largura: int, fonte, fonte_negrito, entrelinha: float = 1.35) -> int:
    return len(quebrar_linhas(texto, fonte, fonte_negrito, largura)) * int(fonte.get_height() * entrelinha)
