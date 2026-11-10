"""Placar da rodada: o resultado mais recente de cada participante."""
from dataclasses import dataclass

from .rodada import ModoRodada


@dataclass(frozen=True)
class Resultado:
    modo: ModoRodada
    nome: str
    tempo_perdido: int
    carros_que_passaram: int
    ia_valida: bool = True   # False se a IA jogou sem treino


class Placar:
    ORDEM = (ModoRodada.FIXO, ModoRodada.VOCE, ModoRodada.IA)

    def __init__(self):
        self._resultados: dict[ModoRodada, Resultado] = {}

    def registrar(self, resultado: Resultado) -> None:
        self._resultados[resultado.modo] = resultado

    def remover(self, modo: ModoRodada) -> None:
        self._resultados.pop(modo, None)

    def obter(self, modo: ModoRodada) -> Resultado | None:
        return self._resultados.get(modo)

    def linhas(self) -> list[Resultado]:
        return [self._resultados[m] for m in self.ORDEM if m in self._resultados]

    def melhor_valor(self) -> int | None:
        linhas = self.linhas()
        return min(r.tempo_perdido for r in linhas) if linhas else None

    def ia_de_referencia(self) -> Resultado | None:
        """Resultado da IA que vale para comparar com pessoas (já treinada)."""
        ia = self.obter(ModoRodada.IA)
        return ia if ia and ia.ia_valida else None
