"""Desenho em resolução nativa.

Todo o layout do jogo é pensado em coordenadas lógicas de 1280×720. Estas
classes convertem essas coordenadas para os pixels reais da janela (fator
``Resolucao.k``), de modo que texto, carros e placas são gerados já no tamanho
final, sem esticar uma imagem pequena. Na tela cheia de 1920×1080, k = 1,5.
"""
import pygame
import pygame.gfxdraw


class Resolucao:
    LARGURA = 1280
    ALTURA = 720
    k = 1.0          # pixels reais por unidade lógica

    @classmethod
    def ajustar(cls, largura_janela: int, altura_janela: int) -> pygame.Rect:
        """Define k para caber na janela e devolve a área útil (centralizada, em pixels reais)."""
        cls.k = min(largura_janela / cls.LARGURA, altura_janela / cls.ALTURA)
        w, h = round(cls.LARGURA * cls.k), round(cls.ALTURA * cls.k)
        return pygame.Rect((largura_janela - w) // 2, (altura_janela - h) // 2, w, h)


def _px(v: float) -> int:
    return round(v * Resolucao.k)


def _espessura(v: float) -> int:
    return max(1, round(v * Resolucao.k))


def _rect(r) -> pygame.Rect:
    """Retângulo lógico → retângulo real, sem frestas entre vizinhos."""
    r = r if isinstance(r, pygame.Rect) else pygame.Rect(r)
    x0, y0 = _px(r.x), _px(r.y)
    return pygame.Rect(x0, y0, _px(r.x + r.w) - x0, _px(r.y + r.h) - y0)


def _ponto(p) -> tuple[int, int]:
    return _px(p[0]), _px(p[1])


class Imagem:
    """Superfície em pixels reais que responde com medidas lógicas."""

    def __init__(self, superficie: pygame.Surface):
        self.superficie = superficie

    def get_width(self) -> float:
        return self.superficie.get_width() / Resolucao.k

    def get_height(self) -> float:
        return self.superficie.get_height() / Resolucao.k

    def get_size(self) -> tuple[float, float]:
        return self.get_width(), self.get_height()

    def get_rect(self, **posicao) -> pygame.Rect:
        rect = pygame.Rect(0, 0, round(self.get_width()), round(self.get_height()))
        for chave, valor in posicao.items():
            setattr(rect, chave, valor)
        return rect

    def rotacionar(self, graus: float) -> "Imagem":
        return Imagem(pygame.transform.rotate(self.superficie, graus))


class Fonte:
    """Fonte com tamanho lógico; a fonte real é carregada para o k atual."""

    _reais: dict[tuple[str, int], pygame.font.Font] = {}

    def __init__(self, caminho: str | None, tamanho: int, negrito_falso: bool = False):
        self.caminho, self.tamanho, self.negrito_falso = caminho, tamanho, negrito_falso

    def _real(self) -> pygame.font.Font:
        tamanho = max(6, round(self.tamanho * Resolucao.k))
        chave = (self.caminho, tamanho, self.negrito_falso)
        if chave not in self._reais:
            try:
                fonte = pygame.font.Font(self.caminho, tamanho)
            except (OSError, FileNotFoundError):
                fonte = pygame.font.Font(None, round(tamanho * 1.3))
                fonte.set_bold(self.negrito_falso)
            self._reais[chave] = fonte
        return self._reais[chave]

    def render(self, texto: str, antialias: bool, cor) -> Imagem:
        return Imagem(self._real().render(texto, antialias, cor))

    def size(self, texto: str) -> tuple[float, float]:
        w, h = self._real().size(texto)
        return w / Resolucao.k, h / Resolucao.k

    def get_height(self) -> float:
        return self._real().get_height() / Resolucao.k


class Tela:
    """Superfície de desenho em coordenadas lógicas (as primitivas de pygame.draw, escaladas)."""

    def __init__(self, superficie: pygame.Surface):
        self.superficie = superficie
        self._clip: pygame.Rect | None = None

    @classmethod
    def nova(cls, tamanho, transparente: bool = False) -> "Tela":
        real = (_px(tamanho[0]), _px(tamanho[1]))
        if transparente:
            return cls(pygame.Surface(real, pygame.SRCALPHA).convert_alpha())
        return cls(pygame.Surface(real).convert())

    # ----- medidas -----
    def get_size(self) -> tuple[int, int]:
        w, h = self.superficie.get_size()
        return round(w / Resolucao.k), round(h / Resolucao.k)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect((0, 0), self.get_size())

    def get_clip(self) -> pygame.Rect | None:
        return self._clip

    def set_clip(self, rect) -> None:
        self._clip = None if rect is None else pygame.Rect(rect)
        self.superficie.set_clip(None if rect is None else _rect(rect))

    # ----- composição -----
    def fill(self, cor, rect=None) -> None:
        self.superficie.fill(cor, None if rect is None else _rect(rect))

    def blit(self, origem, pos) -> None:
        real = origem.superficie if isinstance(origem, (Imagem, Tela)) else origem
        x, y = (pos.x, pos.y) if isinstance(pos, pygame.Rect) else pos
        self.superficie.blit(real, (_px(x), _px(y)))

    # ----- primitivas -----
    def rect(self, cor, rect, largura: int = 0, **raios) -> None:
        raios = {k: _px(v) for k, v in raios.items()}
        pygame.draw.rect(self.superficie, cor, _rect(rect), _espessura(largura) if largura else 0, **raios)

    def line(self, cor, a, b, largura: float = 1) -> None:
        pygame.draw.line(self.superficie, cor, _ponto(a), _ponto(b), _espessura(largura))

    def lines(self, cor, fechado: bool, pontos, largura: float = 1) -> None:
        pygame.draw.lines(self.superficie, cor, fechado, [_ponto(p) for p in pontos], _espessura(largura))

    def circle(self, cor, centro, raio: float, largura: float = 0) -> None:
        pygame.draw.circle(self.superficie, cor, _ponto(centro), max(1, _px(raio)),
                           _espessura(largura) if largura else 0)

    def ellipse(self, cor, rect, largura: float = 0) -> None:
        pygame.draw.ellipse(self.superficie, cor, _rect(rect), _espessura(largura) if largura else 0)

    def polygon(self, cor, pontos, largura: float = 0) -> None:
        pygame.draw.polygon(self.superficie, cor, [_ponto(p) for p in pontos],
                            _espessura(largura) if largura else 0)

    def poligono_suave(self, cor, pontos) -> None:
        """Polígono preenchido com borda antisserrilhada."""
        reais = [_ponto(p) for p in pontos]
        pygame.gfxdraw.filled_polygon(self.superficie, reais, cor)
        pygame.gfxdraw.aapolygon(self.superficie, reais, cor)
