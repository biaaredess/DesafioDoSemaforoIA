"""Mede uma política em partidas completas, sem animação."""
from ..config import ConfigSimulacao
from ..simulacao import Cruzamento
from .politicas import Politica


def executar_episodio(politica: Politica, semente: int, passos: int,
                      demanda_aleatoria: bool = True,
                      config: ConfigSimulacao | None = None) -> Cruzamento:
    cruzamento = Cruzamento(semente, passos, demanda_aleatoria, config)
    while not cruzamento.terminou:
        trocar = cruzamento.semaforo.pode_trocar and politica.decidir(cruzamento)
        cruzamento.passo(trocar)
    return cruzamento


def avaliar(politica: Politica, sementes, passos: int,
            config: ConfigSimulacao | None = None) -> float:
    """Tempo perdido médio (em segundos) em partidas que a IA nunca treinou."""
    sementes = tuple(sementes)
    total = sum(executar_episodio(politica, s, passos, True, config).tempo_perdido for s in sementes)
    return total / len(sementes)
