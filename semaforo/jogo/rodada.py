"""Uma rodada jogável: quem controla o semáforo e em que ritmo o tempo passa."""
from enum import Enum

from ..config import ConfigRodada, ConfigSimulacao
from ..ia import Politica
from ..simulacao import Cruzamento


class ModoRodada(Enum):
    VOCE = "voce"
    FIXO = "fixo"
    IA = "ia"


class Rodada:
    """Avança a simulação no ritmo do relógio.

    Com uma política (máquina), ela decide sozinha. Sem política (você),
    a troca acontece quando ``pedir_troca`` foi chamado desde o último passo.
    """

    def __init__(self, modo: ModoRodada, politica: Politica | None, config: ConfigRodada,
                 config_sim: ConfigSimulacao):
        self.modo = modo
        self.politica = politica
        self.cruzamento = Cruzamento(config.semente, config.passos, False, config_sim)
        self.ms_por_passo = config.ms_por_passo / (1 if politica is None else config.velocidade_maquinas)
        self._acumulado = 0.0
        self._pedido_troca = False

    @property
    def humana(self) -> bool:
        return self.politica is None

    @property
    def terminou(self) -> bool:
        return self.cruzamento.terminou

    @property
    def fracao_passo(self) -> float:
        """Quanto do passo atual já passou (0–1), para animar os carros suavemente."""
        return min(1.0, self._acumulado / self.ms_por_passo)

    def pedir_troca(self) -> None:
        if self.humana:
            self._pedido_troca = True

    def atualizar(self, dt_ms: float) -> int:
        """Consome o tempo decorrido e devolve quantos passos foram simulados."""
        self._acumulado += dt_ms
        passos = 0
        while self._acumulado >= self.ms_por_passo and not self.terminou:
            self._acumulado -= self.ms_por_passo
            self._passo()
            passos += 1
        return passos

    def _passo(self) -> None:
        cruz = self.cruzamento
        if self.humana:
            trocar, self._pedido_troca = self._pedido_troca, False
        else:
            trocar = cruz.semaforo.pode_trocar and self.politica.decidir(cruz)
        cruz.passo(trocar)
