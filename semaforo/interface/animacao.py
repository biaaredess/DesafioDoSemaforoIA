"""Animação suave dos carros entre um passo da simulação e o seguinte."""
from collections import deque
from dataclasses import dataclass

import pygame

from ..simulacao import VAZIO, Cruzamento, Direcao
from .geometria import GeometriaCruzamento
from .sprites import FabricaCarros
from .tema import Paleta


@dataclass
class CarroVisual:
    direcao: Direcao
    s0: float      # posição no passo anterior
    s1: float      # posição no passo atual
    cor: int

    def s(self, fracao: float) -> float:
        return self.s0 + (self.s1 - self.s0) * fracao


class AnimadorCarros:
    """Acompanha o cruzamento e guarda, para cada carro, de onde veio e para onde vai.

    Os carros que ainda não entraram nas vagas (``espera_externa`` da simulação)
    não têm identidade no modelo; aqui eles ganham uma cor e um lugar na fila,
    para aparecerem de verdade quando a câmera abre na tela cheia. A cor é
    mantida quando o carro sai da fila e entra na rua.
    """

    def __init__(self, geometria: GeometriaCruzamento, fabrica: FabricaCarros):
        self.g = geometria
        self.fabrica = fabrica
        self.carros: dict[int, CarroVisual] = {}
        self.saindo: list[CarroVisual] = []
        self.espera: dict[Direcao, list[CarroVisual]] = {d: [] for d in Direcao}
        self._cores_espera: dict[Direcao, deque[int]] = {d: deque() for d in Direcao}
        self._chegadas = 0
        self._cruzamento: Cruzamento | None = None
        self._t = -1

    def _nova_cor(self) -> int:
        self._chegadas += 1
        return self._chegadas * 5 % len(Paleta.CARROS)

    def sincronizar(self, cruzamento: Cruzamento) -> None:
        if cruzamento is not self._cruzamento:
            self._cruzamento, self._t = cruzamento, cruzamento.t
            self.carros, self.saindo = {}, []
            self._cores_espera = {d: deque() for d in Direcao}
            self._atualizar(instantaneo=True)
        elif cruzamento.t != self._t:
            # mais de um passo entre dois quadros (treino acelerado): pula a animação
            instantaneo = cruzamento.t - self._t > 1
            self._t = cruzamento.t
            self._atualizar(instantaneo)

    def _atualizar(self, instantaneo: bool) -> None:
        g = self.g
        novos: dict[int, CarroVisual] = {}
        for faixa in self._cruzamento.faixas:
            d = faixa.direcao
            cores = self._cores_espera[d]
            espera_antes = len(cores)
            entrou = [c for c in faixa.celulas if c != VAZIO and c not in self.carros]
            if instantaneo:
                cores.clear()
                cores.extend(self._nova_cor() for _ in range(faixa.espera_externa))
            else:
                # chegadas deste passo entram no fim da fila; quem entrou na rua sai do começo
                chegadas = faixa.espera_externa - espera_antes + len(entrou)
                cores.extend(self._nova_cor() for _ in range(max(0, chegadas)))
            cores_entrada = {c: (cores.popleft() if cores and not instantaneo else self._nova_cor())
                             for c in entrou}

            for i, carro in enumerate(faixa.celulas):
                if carro == VAZIO:
                    continue
                s1 = g.s_da_celula(i)
                antes = self.carros.get(carro)
                if instantaneo:
                    s0 = s1
                elif antes:
                    s0 = antes.s1
                else:
                    s0 = g.s_espera(1)      # sai de baixo da passarela / da borda
                cor = antes.cor if antes else cores_entrada[carro]
                novos[carro] = CarroVisual(d, s0, s1, cor)

            fila = []
            for j, cor in enumerate(cores, start=1):
                s1 = g.s_espera(j)
                if instantaneo:
                    s0 = s1
                elif j + len(entrou) <= espera_antes:
                    s0 = g.s_espera(j + len(entrou))     # andou uma vaga para frente
                else:
                    s0 = g.alcance(d) + g.celula          # acabou de chegar, vem da borda
                fila.append(CarroVisual(d, s0, s1, cor))
            self.espera[d] = fila

        if instantaneo:
            self.saindo = []
        else:
            deslocamento = g.celula_cruzamento * 1.1
            for c in self.saindo:
                c.s0, c.s1 = c.s1, c.s1 - deslocamento
            # quem sumiu da simulação depois de entrar no cruzamento segue até sair da tela
            for carro, c in self.carros.items():
                if carro not in novos and c.s1 < g.parada:
                    self.saindo.append(CarroVisual(c.direcao, c.s1, c.s1 - deslocamento, c.cor))
            self.saindo = [c for c in self.saindo if c.s0 > -g.alcance(c.direcao) - g.celula * 2]
        self.carros = novos

    def fora_de_vista(self, direcao: Direcao, alcance_visivel: float) -> int:
        """Quantos carros da fila de espera estão além da borda visível."""
        limite = alcance_visivel - self.g.carro_comprimento / 2
        return sum(1 for c in self.espera[direcao] if c.s1 > limite)

    def desenhar(self, tela: pygame.Surface, origem: tuple[float, float], fracao: float) -> None:
        ox, oy = origem
        todos = [*self.carros.values(), *self.saindo]
        for fila in self.espera.values():
            todos.extend(fila)
        for c in todos:
            x, y, angulo = self.g.posicao(c.direcao, c.s(fracao))
            sprite = self.fabrica.sprite(c.cor, angulo)
            tela.blit(sprite, sprite.get_rect(center=(ox + x, oy + y)))
