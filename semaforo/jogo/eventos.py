"""Avisos que o controlador publica para a interface reagir (padrão observador)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .placar import Resultado
    from .rodada import ModoRodada


@dataclass(frozen=True)
class Evento:
    pass


@dataclass(frozen=True)
class RodadaIniciada(Evento):
    modo: ModoRodada


@dataclass(frozen=True)
class RodadaTerminada(Evento):
    resultado: Resultado
    venceu_ia: bool | None = None   # só em rodadas humanas; None = ainda não há IA para comparar


@dataclass(frozen=True)
class TreinoConcluido(Evento):
    episodios: int
    horas: int
