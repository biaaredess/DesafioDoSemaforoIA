"""Máquina de estados do semáforo: verde → amarelo → vermelho geral → verde do outro eixo."""
from .tipos import CorLuz, Eixo


class Semaforo:
    def __init__(self, passos_troca: int = 3):
        self.passos_troca = passos_troca
        self.verde = Eixo.NORTE_SUL
        self.transicao = 0       # passos restantes de amarelo + vermelho geral
        self.tempo_verde = 0     # segundos desde que o verde atual abriu
        self.trocas = 0

    @property
    def pode_trocar(self) -> bool:
        return self.transicao == 0

    def iniciar_troca(self) -> bool:
        if not self.pode_trocar:
            return False
        self.transicao = self.passos_troca
        self.trocas += 1
        return True

    def libera(self, eixo: Eixo) -> bool:
        """Os carros deste eixo podem entrar no cruzamento neste passo?"""
        return self.transicao == 0 and self.verde == eixo

    def avancar(self) -> None:
        if self.transicao > 0:
            self.transicao -= 1
            if self.transicao == 0:
                self.verde = self.verde.oposto
                self.tempo_verde = 0
        else:
            self.tempo_verde += 1

    def cor(self, eixo: Eixo) -> CorLuz:
        if self.transicao == 0:
            return CorLuz.VERDE if self.verde == eixo else CorLuz.VERMELHO
        # o último passo da transição é vermelho para todos (segurança)
        if self.verde == eixo and self.transicao > 1:
            return CorLuz.AMARELO
        return CorLuz.VERMELHO
