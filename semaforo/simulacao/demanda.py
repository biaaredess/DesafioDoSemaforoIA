"""Quantos carros chegam: probabilidade de surgir um carro por segundo em cada rua."""
import random

from .tipos import Direcao, Eixo


class Demanda:
    """Horário de pico que se inverte no meio da partida.

    Na rodada jogável (``aleatoria=False``) o Norte–Sul começa mais cheio e,
    depois da virada, o Leste–Oeste passa a ser o pico. No treino
    (``aleatoria=True``) as taxas e o instante da virada são sorteados, para
    a IA não decorar uma única situação.
    """

    PROBABILIDADE_MINIMA = 0.02

    def __init__(self, rng: random.Random, passos: int, aleatoria: bool):
        taxa_ns, taxa_lo, virada = 0.22, 0.10, 0.5
        ajuste = (0.015, -0.01)
        if aleatoria:
            taxa_ns = 0.12 + rng.random() * 0.14
            taxa_lo = 0.05 + rng.random() * 0.10
            virada = 0.3 + rng.random() * 0.4
            if rng.random() < 0.5:
                taxa_ns, taxa_lo = taxa_lo, taxa_ns
            ajuste = (rng.random() * 0.04 - 0.02, rng.random() * 0.04 - 0.02)
        self._taxa_inicio = (taxa_ns, taxa_lo)
        self._instante_virada = passos * virada
        self._ajuste = ajuste  # pequena diferença entre as duas mãos do mesmo eixo

    def probabilidade(self, t: int, direcao: Direcao) -> float:
        taxa_ns, taxa_lo = self._taxa_inicio
        if t >= self._instante_virada:
            taxa_ns, taxa_lo = taxa_lo, taxa_ns
        base = taxa_ns if direcao.eixo is Eixo.NORTE_SUL else taxa_lo
        return max(self.PROBABILIDADE_MINIMA, base + self._ajuste[direcao % 2])
