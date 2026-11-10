"""Tipos básicos do domínio: eixos, direções de chegada e cores do semáforo."""
from enum import Enum, IntEnum


class Eixo(IntEnum):
    NORTE_SUL = 0
    LESTE_OESTE = 1

    @property
    def oposto(self) -> "Eixo":
        return Eixo(1 - self)

    @property
    def nome(self) -> str:
        return "Norte–Sul" if self is Eixo.NORTE_SUL else "Leste–Oeste"


class Direcao(IntEnum):
    """De onde o carro vem. A ordem importa: define a ordem do sorteio de chegadas."""

    NORTE = 0
    SUL = 1
    LESTE = 2
    OESTE = 3

    @property
    def eixo(self) -> Eixo:
        return Eixo.NORTE_SUL if self in (Direcao.NORTE, Direcao.SUL) else Eixo.LESTE_OESTE


class CorLuz(Enum):
    VERDE = "verde"
    AMARELO = "amarelo"
    VERMELHO = "vermelho"
