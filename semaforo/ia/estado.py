"""Transforma o cruzamento em uma "situação" discreta que cabe numa tabela."""
from ..simulacao import Cruzamento


class ObservadorEstado:
    """A IA não vê carros um a um: vê só três informações resumidas.

    1. quantos carros esperam no verde   (em faixas: 0, 1–3, 4–7, 8–13, 14+)
    2. quantos carros esperam no vermelho (mesmas faixas)
    3. se o verde abriu há pouco (< 5 s) ou não

    Isso dá 5 × 5 × 2 = 50 situações possíveis.
    """

    LIMITES_FILA = (0, 1, 4, 8, 14)
    ROTULOS_FILA = ("0", "1–3", "4–7", "8–13", "14+")
    LIMIAR_TEMPO = 5

    def __init__(self):
        self.faixas_fila = len(self.LIMITES_FILA)
        self.n_estados = self.faixas_fila * self.faixas_fila * 2

    def faixa_da_fila(self, fila: int) -> int:
        faixa = 0
        for i, limite in enumerate(self.LIMITES_FILA):
            if fila >= limite:
                faixa = i
        return faixa

    def codificar(self, faixa_verde: int, faixa_vermelho: int, verde_antigo: bool) -> int:
        return (faixa_verde * self.faixas_fila + faixa_vermelho) * 2 + int(verde_antigo)

    def decodificar(self, estado: int) -> tuple[int, int, bool]:
        filas, verde_antigo = divmod(estado, 2)
        faixa_verde, faixa_vermelho = divmod(filas, self.faixas_fila)
        return faixa_verde, faixa_vermelho, bool(verde_antigo)

    def observar(self, cruzamento: Cruzamento) -> int:
        semaforo = cruzamento.semaforo
        fila_verde = cruzamento.fila(semaforo.verde)
        fila_vermelho = cruzamento.fila(semaforo.verde.oposto)
        return self.codificar(self.faixa_da_fila(fila_verde),
                              self.faixa_da_fila(fila_vermelho),
                              semaforo.tempo_verde >= self.LIMIAR_TEMPO)
