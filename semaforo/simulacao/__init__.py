"""Modelo do cruzamento: autômato celular de carros controlado por um semáforo."""
from .tipos import CorLuz, Direcao, Eixo
from .demanda import Demanda
from .semaforo import Semaforo
from .faixa import Faixa, VAZIO
from .cruzamento import Cruzamento

__all__ = ["CorLuz", "Direcao", "Eixo", "Demanda", "Semaforo", "Faixa", "VAZIO", "Cruzamento"]
