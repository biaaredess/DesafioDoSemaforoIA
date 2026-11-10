"""Parâmetros do jogo, agrupados por assunto.

Nada aqui depende de pygame: a simulação e a IA podem ser usadas
(e testadas) sem abrir nenhuma janela.
"""
from dataclasses import dataclass, field
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"


@dataclass(frozen=True)
class ConfigSimulacao:
    """Geometria lógica do cruzamento. 1 passo da simulação = 1 segundo."""

    celulas_chegada: int = 6      # vagas visíveis em cada rua até a faixa de pedestre
    celulas_cruzamento: int = 3   # vagas dentro do cruzamento
    passos_troca: int = 3         # 2 s de amarelo + 1 s de vermelho geral


@dataclass(frozen=True)
class ConfigRodada:
    """Uma rodada jogável: todos enfrentam exatamente os mesmos carros."""

    semente: int = 2026
    passos: int = 160
    ms_por_passo: int = 300       # ritmo de quem joga
    velocidade_maquinas: int = 3  # máquinas jogam 3× mais rápido


@dataclass(frozen=True)
class ConfigTreino:
    """Hiperparâmetros do Q-learning e ritmo da animação do treino."""

    episodios: int = 1500
    passos_por_episodio: int = 300
    semente: int = 404
    semente_base_episodios: int = 100_000
    sementes_validacao: tuple[int, ...] = (11, 22, 33)
    intervalo_curva: int = 25     # avalia a IA a cada N partidas de treino
    gamma: float = 0.9            # peso do futuro
    epsilon_minimo: float = 0.03  # curiosidade mínima
    fracao_exploracao: float = 0.6
    alpha_inicial: float = 0.2    # taxa de aprendizado
    alpha_minimo: float = 0.03
    duracao_ms: int = 14_000      # duração desejada da animação do treino


@dataclass(frozen=True)
class Config:
    simulacao: ConfigSimulacao = field(default_factory=ConfigSimulacao)
    rodada: ConfigRodada = field(default_factory=ConfigRodada)
    treino: ConfigTreino = field(default_factory=ConfigTreino)
    arquivo_ia: Path = PASTA_DADOS / "ia_treinada.json"
    arquivo_ranking: Path = PASTA_DADOS / "ranking.json"
