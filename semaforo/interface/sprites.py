"""Sprites desenhados por código: carros vistos de cima e semáforos de três luzes."""
import pygame

from ..simulacao import CorLuz
from .tela import Imagem, Resolucao
from .tema import Paleta, clarear, escurecer

SUPERAMOSTRA = 4  # desenha 4× maior e reduz até os pixels reais: bordas suaves sem imagens


def _reduzir(sup: pygame.Surface) -> Imagem:
    """Reduz o desenho superamostrado para o tamanho real na resolução atual."""
    escala = Resolucao.k / SUPERAMOSTRA
    tamanho = (max(1, round(sup.get_width() * escala)), max(1, round(sup.get_height() * escala)))
    return Imagem(pygame.transform.smoothscale(sup, tamanho))


class FabricaCarros:
    """Cria (e guarda) o sprite de cada cor de carro nas quatro direções."""

    def __init__(self, comprimento: int, largura: int):
        self.comprimento = comprimento
        self.largura = largura
        self._cache: dict[tuple[int, int, float], Imagem] = {}

    def sprite(self, indice_cor: int, angulo: int) -> Imagem:
        k = Resolucao.k
        chave = (indice_cor, angulo, k)
        if chave not in self._cache:
            if (indice_cor, 0, k) not in self._cache:
                self._cache[(indice_cor, 0, k)] = self._desenhar(Paleta.CARROS[indice_cor])
            self._cache[chave] = self._cache[(indice_cor, 0, k)].rotacionar(angulo)
        return self._cache[chave]

    def _desenhar(self, cor) -> Imagem:
        """Carro apontando para a direita (frente em +x), no estilo cartum da referência."""
        k = SUPERAMOSTRA
        L, W = self.comprimento * k, self.largura * k
        margem = 4 * k
        sup = pygame.Surface((L + 2 * margem, W + 2 * margem), pygame.SRCALPHA)
        x0, y0 = margem, margem
        contorno = escurecer(cor, 0.45)
        brilho = clarear(cor, 0.35)

        # sombra
        pygame.draw.rect(sup, (0, 0, 0, 70), (x0 + 2 * k, y0 + 3 * k, L, W), border_radius=int(W * 0.38))
        # espelhos retrovisores
        for lado in (-1, 1):
            ey = y0 + W / 2 + lado * (W / 2 + k) - 1.5 * k
            pygame.draw.ellipse(sup, contorno, (x0 + L * 0.58, ey, 4 * k, 3 * k))
        # carroceria
        corpo = pygame.Rect(x0, y0, L, W)
        pygame.draw.rect(sup, contorno, corpo, border_radius=int(W * 0.38))
        pygame.draw.rect(sup, cor, corpo.inflate(-2 * k, -2 * k), border_radius=int(W * 0.34))
        # faixa de brilho lateral
        pygame.draw.rect(sup, brilho, (x0 + L * 0.1, y0 + 2 * k, L * 0.78, W * 0.16), border_radius=int(W * 0.08))
        # para-brisa (frente) e vidro traseiro
        pygame.draw.rect(sup, contorno, (x0 + L * 0.56, y0 + W * 0.13, L * 0.19, W * 0.74), border_radius=int(W * 0.18))
        pygame.draw.rect(sup, Paleta.VIDRO, (x0 + L * 0.575, y0 + W * 0.17, L * 0.16, W * 0.66), border_radius=int(W * 0.15))
        pygame.draw.rect(sup, contorno, (x0 + L * 0.13, y0 + W * 0.18, L * 0.13, W * 0.64), border_radius=int(W * 0.14))
        pygame.draw.rect(sup, Paleta.VIDRO_ESCURO, (x0 + L * 0.145, y0 + W * 0.22, L * 0.1, W * 0.56), border_radius=int(W * 0.12))
        # teto
        pygame.draw.rect(sup, clarear(cor, 0.12), (x0 + L * 0.27, y0 + W * 0.16, L * 0.28, W * 0.68), border_radius=int(W * 0.16))
        pygame.draw.line(sup, Paleta.VIDRO, (x0 + L * 0.6, y0 + W * 0.3), (x0 + L * 0.66, y0 + W * 0.24), k)
        # faróis e lanternas
        for lado in (0, 1):
            fy = y0 + (W * 0.12 if lado == 0 else W * 0.88 - 3 * k)
            pygame.draw.ellipse(sup, Paleta.FAROL, (x0 + L - 5 * k, fy, 4 * k, 3 * k))
            pygame.draw.rect(sup, Paleta.LANTERNA, (x0 + k, fy, 2.5 * k, 3 * k), border_radius=k)
        return _reduzir(sup)


class DesenhistaSemaforo:
    """Caixa preta com três lâmpadas (vermelha, amarela, verde) e um halo na acesa."""

    ORDEM = (CorLuz.VERMELHO, CorLuz.AMARELO, CorLuz.VERDE)
    ACESA = {CorLuz.VERMELHO: Paleta.VERMELHO, CorLuz.AMARELO: Paleta.AMARELO, CorLuz.VERDE: Paleta.VERDE}
    APAGADA = {CorLuz.VERMELHO: Paleta.VERMELHO_APAGADO, CorLuz.AMARELO: Paleta.AMARELO_APAGADO,
               CorLuz.VERDE: Paleta.VERDE_APAGADO}

    def __init__(self, raio_lampada: int = 8):
        self.raio = raio_lampada
        self._cache: dict[tuple[CorLuz, bool, float], Imagem] = {}

    def sprite(self, acesa: CorLuz, horizontal: bool) -> Imagem:
        chave = (acesa, horizontal, Resolucao.k)
        if chave not in self._cache:
            base = self._desenhar(acesa)
            self._cache[chave] = base if horizontal else base.rotacionar(-90)
        return self._cache[chave]

    def _desenhar(self, acesa: CorLuz) -> Imagem:
        k = SUPERAMOSTRA
        r = self.raio * k
        passo = int(r * 2.5)
        halo = int(r * 1.0)
        w = passo * 3 + halo * 2
        h = int(r * 2.9) + halo * 2
        sup = pygame.Surface((w, h), pygame.SRCALPHA)
        caixa = pygame.Rect(halo, halo, passo * 3, int(r * 2.9))
        # halo da lâmpada acesa (anéis concêntricos com transparência)
        i = self.ORDEM.index(acesa)
        cx = caixa.x + passo * i + passo // 2
        cy = caixa.centery
        for n in range(8, 0, -1):
            anel = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(anel, (*self.ACESA[acesa], 22), (cx, cy), r + halo * n / 8 + r * 0.6)
            sup.blit(anel, (0, 0))
        # caixa
        pygame.draw.rect(sup, (0, 0, 0, 90), caixa.move(k * 2, k * 3), border_radius=int(r * 0.9))
        pygame.draw.rect(sup, Paleta.CAIXA_SEMAFORO, caixa, border_radius=int(r * 0.9))
        pygame.draw.rect(sup, (78, 82, 90), caixa, k, border_radius=int(r * 0.9))
        for j, luz in enumerate(self.ORDEM):
            lx = caixa.x + passo * j + passo // 2
            pygame.draw.circle(sup, (14, 15, 18), (lx, cy), r + k)
            if luz is acesa:
                pygame.draw.circle(sup, self.ACESA[luz], (lx, cy), r)
                pygame.draw.circle(sup, clarear(self.ACESA[luz], 0.6), (lx - r * 0.3, cy - r * 0.3), r * 0.35)
            else:
                pygame.draw.circle(sup, self.APAGADA[luz], (lx, cy), r)
        return _reduzir(sup)
