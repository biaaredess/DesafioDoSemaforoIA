"""Uma faixa de rua como autômato celular: cada célula tem um carro (id) ou está vazia."""
from .tipos import Direcao

VAZIO = -1


class Faixa:
    """Carros de uma direção. Células ``[0, chegada)`` ficam antes da faixa de
    pedestre; as seguintes ficam dentro do cruzamento. Carros que ainda não
    cabem na tela esperam em ``espera_externa`` (contam como parados).
    """

    def __init__(self, direcao: Direcao, celulas_chegada: int, celulas_cruzamento: int):
        self.direcao = direcao
        self.chegada = celulas_chegada
        self.celulas = [VAZIO] * (celulas_chegada + celulas_cruzamento)
        self.espera_externa = 0

    def fila(self) -> int:
        """Carros esperando para entrar no cruzamento (visíveis + fora da tela)."""
        visiveis = sum(1 for carro in self.celulas[:self.chegada] if carro != VAZIO)
        return visiveis + self.espera_externa

    def avancar(self, aberta: bool, chegou_carro: bool, novo_id) -> tuple[int, int]:
        """Move os carros um passo. Devolve (carros parados, carros que saíram).

        Atualização síncrona: um carro só anda se a célula da frente estava
        livre no início do passo. Por isso uma fila parada "descola" aos poucos,
        como no trânsito de verdade.
        """
        antes = self.celulas
        depois = [VAZIO] * len(antes)
        ultima = len(antes) - 1
        saidas = 1 if antes[ultima] != VAZIO else 0

        # dentro do cruzamento os carros sempre seguem em frente
        for i in range(ultima - 1, self.chegada - 1, -1):
            if antes[i] != VAZIO:
                depois[i + 1] = antes[i]

        parados = 0
        for i in range(self.chegada - 1, -1, -1):
            carro = antes[i]
            if carro == VAZIO:
                continue
            if i == self.chegada - 1:
                livre = aberta and antes[self.chegada] == VAZIO
            else:
                livre = antes[i + 1] == VAZIO
            if livre:
                depois[i + 1] = carro
            else:
                depois[i] = carro
                parados += 1

        if chegou_carro:
            self.espera_externa += 1
        if self.espera_externa and depois[0] == VAZIO:
            depois[0] = novo_id()
            self.espera_externa -= 1

        self.celulas = depois
        return parados + self.espera_externa, saidas
