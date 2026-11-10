"""Agente de aprendizado por reforço (Q-learning tabular)."""
import json
import random
from enum import IntEnum
from pathlib import Path


class Acao(IntEnum):
    MANTER = 0
    TROCAR = 1


class AgenteQLearning:
    """Guarda uma "nota" Q[situação][ação] e a melhora com a experiência.

    Regra de atualização (equação de Bellman):
        Q[s][a] ← Q[s][a] + α · (recompensa + γ · max Q[s'] − Q[s][a])
    """

    def __init__(self, n_estados: int, gamma: float = 0.9):
        self.n_estados = n_estados
        self.gamma = gamma
        self.reiniciar()

    def reiniciar(self) -> None:
        self.q = [[0.0, 0.0] for _ in range(self.n_estados)]
        self.visitas = [0] * self.n_estados

    # ----- decidir -----
    def melhor_acao(self, estado: int, rng: random.Random | None = None) -> Acao:
        manter, trocar = self.q[estado]
        if manter == trocar:  # empate (ex.: nunca aprendeu nada): sorteia
            return Acao((rng or random).random() < 0.5)
        return Acao.TROCAR if trocar > manter else Acao.MANTER

    def escolher(self, estado: int, epsilon: float, rng: random.Random) -> Acao:
        """Política ε-gulosa: com chance ε explora, senão usa o que já aprendeu."""
        if rng.random() < epsilon:
            return Acao(rng.random() < 0.5)
        return self.melhor_acao(estado, rng)

    def preferencia(self, estado: int, visitas_minimas: int = 30) -> Acao | None:
        """Ação aprendida, ou None se a situação quase nunca foi vista."""
        if self.visitas[estado] < visitas_minimas:
            return None
        manter, trocar = self.q[estado]
        return Acao.TROCAR if trocar > manter else Acao.MANTER

    # ----- aprender -----
    def aprender(self, estado: int, acao: Acao, recompensa: float,
                 estado_seguinte: int, alpha: float) -> float:
        """Atualiza Q e devolve o erro de diferença temporal."""
        futuro = max(self.q[estado_seguinte])
        alvo = recompensa + self.gamma * futuro
        erro = alvo - self.q[estado][acao]
        self.q[estado][acao] += alpha * erro
        return erro

    def registrar_visita(self, estado: int) -> None:
        self.visitas[estado] += 1

    # ----- persistência -----
    def para_dict(self) -> dict:
        return {"n_estados": self.n_estados, "gamma": self.gamma,
                "q": self.q, "visitas": self.visitas}

    def carregar_dict(self, dados: dict) -> None:
        if dados.get("n_estados") != self.n_estados:
            raise ValueError("tabela Q incompatível com o número de estados")
        self.gamma = dados.get("gamma", self.gamma)
        self.q = [[float(m), float(t)] for m, t in dados["q"]]
        self.visitas = [int(v) for v in dados["visitas"]]

    def salvar(self, caminho: Path, **extras) -> None:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps({**self.para_dict(), **extras}), encoding="utf-8")

    def carregar(self, caminho: Path) -> dict:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        self.carregar_dict(dados)
        return dados
