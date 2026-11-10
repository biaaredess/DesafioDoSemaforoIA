"""O cruzamento completo: quatro faixas, um semáforo e a contagem do tempo perdido."""
import random

from ..config import ConfigSimulacao
from .demanda import Demanda
from .faixa import Faixa
from .semaforo import Semaforo
from .tipos import Direcao, Eixo


class Cruzamento:
    """Simulação determinística: a mesma semente gera exatamente os mesmos carros.

    A cada passo (1 s), cada carro parado soma 1 s ao ``tempo_perdido``.
    Quem controla o semáforo quer deixar esse número o menor possível.
    """

    def __init__(self, semente: int, passos: int, demanda_aleatoria: bool = False,
                 config: ConfigSimulacao | None = None):
        self.config = config or ConfigSimulacao()
        self.passos = passos
        self.t = 0
        self._rng = random.Random(semente)
        self.demanda = Demanda(self._rng, passos, demanda_aleatoria)
        self.semaforo = Semaforo(self.config.passos_troca)
        self.faixas = [Faixa(d, self.config.celulas_chegada, self.config.celulas_cruzamento)
                       for d in Direcao]
        self._proximo_id = 1
        self.tempo_perdido = 0
        self.carros_que_passaram = 0
        self.parados_agora = 0

    @property
    def terminou(self) -> bool:
        return self.t >= self.passos

    def fila(self, eixo: Eixo) -> int:
        return sum(f.fila() for f in self.faixas if f.direcao.eixo is eixo)

    def _novo_id(self) -> int:
        carro = self._proximo_id
        self._proximo_id += 1
        return carro

    def passo(self, trocar: bool = False) -> int:
        """Avança 1 segundo. Devolve quantos carros ficaram parados neste passo."""
        if trocar:
            self.semaforo.iniciar_troca()
        parados = 0
        for faixa in self.faixas:
            aberta = self.semaforo.libera(faixa.direcao.eixo)
            chegou = self._rng.random() < self.demanda.probabilidade(self.t, faixa.direcao)
            p, saidas = faixa.avancar(aberta, chegou, self._novo_id)
            parados += p
            self.carros_que_passaram += saidas
        self.semaforo.avancar()
        self.tempo_perdido += parados
        self.parados_agora = parados
        self.t += 1
        return parados
