"""Políticas de controle: quem decide se o semáforo troca ou não."""
import random
from abc import ABC, abstractmethod

from ..simulacao import Cruzamento
from .agente_q import Acao, AgenteQLearning
from .estado import ObservadorEstado


class Politica(ABC):
    nome = "política"

    @abstractmethod
    def decidir(self, cruzamento: Cruzamento) -> bool:
        """True = trocar o sinal agora. Só é chamada quando a troca é possível."""


class SemaforoFixo(Politica):
    """O semáforo comum da rua: troca a cada N segundos, sem olhar os carros."""

    nome = "Semáforo comum"

    def __init__(self, tempo_verde: int = 12):
        self.tempo_verde = tempo_verde

    def decidir(self, cruzamento: Cruzamento) -> bool:
        return cruzamento.semaforo.tempo_verde >= self.tempo_verde


class RegraEscrita(Politica):
    """Uma regra if/else que uma pessoa pensou. Não aparece no jogo: serve de
    referência no treino pelo terminal, para conferir que a IA vai além dela."""

    nome = "Regra if/else"

    def __init__(self, tempo_minimo: int = 4, margem: int = 2):
        self.tempo_minimo = tempo_minimo
        self.margem = margem

    def decidir(self, cruzamento: Cruzamento) -> bool:
        semaforo = cruzamento.semaforo
        fila_verde = cruzamento.fila(semaforo.verde)
        fila_vermelho = cruzamento.fila(semaforo.verde.oposto)
        return semaforo.tempo_verde >= self.tempo_minimo and fila_vermelho > fila_verde + self.margem


class PoliticaAprendida(Politica):
    """Usa a tabela Q do agente, sem explorar (só o que ela já aprendeu)."""

    nome = "IA"

    def __init__(self, agente: AgenteQLearning, observador: ObservadorEstado, semente_desempate: int = 0):
        self.agente = agente
        self.observador = observador
        self._rng = random.Random(semente_desempate)

    def decidir(self, cruzamento: Cruzamento) -> bool:
        estado = self.observador.observar(cruzamento)
        return self.agente.melhor_acao(estado, self._rng) is Acao.TROCAR
