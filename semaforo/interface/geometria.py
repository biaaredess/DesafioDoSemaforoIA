"""Converte posições da simulação (células) em pixels do cenário."""
from ..config import ConfigSimulacao
from ..simulacao import Direcao


class GeometriaCruzamento:
    """Medidas do cenário visto de cima, em pixels.

    O cenário é mais largo que alto: as ruas Leste e Oeste continuam até as
    bordas, e a câmera mostra só o quadrado central quando o painel está aberto.

    ``s`` é a distância até o centro, medida ao longo da rua de onde o carro
    vem: positiva antes do centro, negativa depois que ele atravessou.
    Mão de direção brasileira: cada carro anda do lado direito da rua.
    """

    def __init__(self, largura: int, altura: int, config: ConfigSimulacao):
        self.largura, self.altura = largura, altura
        self.cx, self.cy = largura / 2, altura / 2
        self.meia_rua = 54                      # uma faixa para cada sentido
        self.largura_faixa = self.meia_rua
        self.meio_fio = 5
        self.calcada = 24
        self.raio_esquina = 34
        self.pedestre_inicio = self.meia_rua + 6
        self.pedestre_fim = self.meia_rua + 32
        self.linha_parada = (self.meia_rua + 38, self.meia_rua + 43)
        self.parada = self.meia_rua + 44        # onde termina a primeira vaga de espera
        self.borda = altura / 2                 # início da primeira vaga visível

        self.celulas_chegada = config.celulas_chegada
        self.celulas_cruzamento = config.celulas_cruzamento
        self.celula = (self.borda - self.parada) / self.celulas_chegada
        self.celula_cruzamento = 2 * self.parada / self.celulas_cruzamento
        self.carro_comprimento = round(self.celula - 5)
        self.carro_largura = round(self.carro_comprimento * 0.56)

        # passarela sobre as ruas Leste e Oeste: os carros surgem de baixo dela
        self.passarela = (self.borda + 12, self.borda + 12 + self.celula)

    def s_da_celula(self, i: int) -> float:
        if i < self.celulas_chegada:
            return self.borda - (i + 0.5) * self.celula
        return self.parada - (i - self.celulas_chegada + 0.5) * self.celula_cruzamento

    def s_espera(self, j: int) -> float:
        """Posição do j-ésimo carro (1, 2, ...) da fila que ainda não entrou nas vagas."""
        return self.borda + (j - 0.5) * self.celula

    def alcance(self, direcao: Direcao) -> float:
        """Até que distância do centro a rua aparece no cenário."""
        return self.cy if direcao in (Direcao.NORTE, Direcao.SUL) else self.cx

    def posicao(self, direcao: Direcao, s: float) -> tuple[float, float, int]:
        """(x, y, ângulo em graus) do centro do carro. Ângulo 0 = apontando para a direita."""
        cx, cy, lado = self.cx, self.cy, self.largura_faixa / 2
        if direcao is Direcao.NORTE:   # desce pela esquerda
            return cx - lado, cy - s, 270
        if direcao is Direcao.SUL:     # sobe pela direita
            return cx + lado, cy + s, 90
        if direcao is Direcao.LESTE:   # vai para a esquerda pela parte de cima
            return cx + s, cy - lado, 180
        return cx - s, cy + lado, 0    # OESTE: vai para a direita pela parte de baixo

    def posicao_semaforo(self, direcao: Direcao) -> tuple[float, float]:
        """Semáforo na esquina à direita de quem chega, logo antes da faixa de pedestre."""
        cx, cy = self.cx, self.cy
        lateral = self.meia_rua + 40
        frente = self.pedestre_fim + 22
        return {
            Direcao.NORTE: (cx - lateral, cy - frente),
            Direcao.SUL: (cx + lateral, cy + frente),
            Direcao.LESTE: (cx + frente, cy - lateral),
            Direcao.OESTE: (cx - frente, cy + lateral),
        }[direcao]
