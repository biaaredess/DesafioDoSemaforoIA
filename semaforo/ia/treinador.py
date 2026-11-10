"""Treino do agente, passo a passo, para poder ser animado na tela."""
import random

from ..config import ConfigSimulacao, ConfigTreino
from ..simulacao import Cruzamento
from .agente_q import Acao, AgenteQLearning
from .avaliacao import avaliar
from .estado import ObservadorEstado
from .politicas import PoliticaAprendida


class Treinador:
    """Executa o Q-learning em fatias de passos (``avancar``).

    A IA só decide quando o semáforo pode trocar. A recompensa de uma decisão
    é −1 por carro parado, somada em todos os segundos até a próxima decisão.
    """

    def __init__(self, agente: AgenteQLearning, observador: ObservadorEstado,
                 config: ConfigTreino | None = None, config_sim: ConfigSimulacao | None = None):
        self.agente = agente
        self.observador = observador
        self.config = config or ConfigTreino()
        self.config_sim = config_sim
        self._rng = random.Random(self.config.semente)
        self.episodio = 0
        self.passos_feitos = 0
        self.cruzamento: Cruzamento | None = None
        self.curva: list[float] = [self.avaliar_agora()]
        self._estado_anterior = -1
        self._acao_anterior = Acao.MANTER
        self._recompensa = 0.0

    @property
    def concluido(self) -> bool:
        return self.episodio >= self.config.episodios

    @property
    def total_passos(self) -> int:
        return self.config.episodios * self.config.passos_por_episodio

    def epsilon(self, episodio: int | None = None) -> float:
        e = self.episodio if episodio is None else episodio
        c = self.config
        return max(c.epsilon_minimo, 1 - e / (c.episodios * c.fracao_exploracao))

    def alpha(self) -> float:
        c = self.config
        return max(c.alpha_minimo, c.alpha_inicial * (1 - self.episodio / c.episodios))

    def avaliar_agora(self) -> float:
        politica = PoliticaAprendida(self.agente, self.observador)
        return avaliar(politica, self.config.sementes_validacao,
                       self.config.passos_por_episodio, self.config_sim)

    def _novo_episodio(self) -> None:
        self.cruzamento = Cruzamento(self.config.semente_base_episodios + self.episodio,
                                     self.config.passos_por_episodio, True, self.config_sim)
        self._estado_anterior = -1
        self._acao_anterior = Acao.MANTER
        self._recompensa = 0.0

    def avancar(self, n_passos: int) -> None:
        agente = self.agente
        for _ in range(n_passos):
            if self.concluido:
                return
            if self.cruzamento is None:
                self._novo_episodio()
            cruz = self.cruzamento
            if cruz.semaforo.pode_trocar:
                estado = self.observador.observar(cruz)
                if self._estado_anterior >= 0:
                    agente.aprender(self._estado_anterior, self._acao_anterior,
                                    self._recompensa, estado, self.alpha())
                agente.registrar_visita(estado)
                acao = agente.escolher(estado, self.epsilon(), self._rng)
                self._estado_anterior, self._acao_anterior = estado, acao
                self._recompensa = -cruz.passo(acao is Acao.TROCAR)
            else:
                self._recompensa -= cruz.passo(False)
            self.passos_feitos += 1

            if cruz.terminou:
                self.episodio += 1
                self.cruzamento = None
                if self.episodio % self.config.intervalo_curva == 0:
                    self.curva.append(self.avaliar_agora())

    def treinar_tudo(self) -> None:
        self.avancar(self.total_passos - self.passos_feitos)
