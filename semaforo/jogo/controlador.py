"""Controlador do jogo: junta simulação, IA, placar e ranking num só lugar.

A interface só conversa com esta classe: chama ações (iniciar rodada,
trocar sinal, treinar...) e escuta eventos. Assim o visual pode mudar
inteiro sem tocar nas regras, e as regras podem ser testadas sem janela.
"""
import time
from typing import Callable

from ..config import Config
from ..ia import AgenteQLearning, ObservadorEstado, PoliticaAprendida, SemaforoFixo, Treinador, avaliar
from ..simulacao import Cruzamento
from .eventos import Evento, RodadaIniciada, RodadaTerminada, TreinoConcluido
from .placar import Placar, Resultado
from .ranking import Ranking
from .rodada import ModoRodada, Rodada

Ouvinte = Callable[[Evento], None]


class ControladorJogo:
    ORCAMENTO_TREINO_MS = 22     # tempo máximo de treino por quadro, para a tela não travar

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.observador = ObservadorEstado()
        self.agente = AgenteQLearning(self.observador.n_estados, self.config.treino.gamma)
        self.treinada = False
        self._curva_salva: list[float] = []
        self._carregar_ia()

        self.placar = Placar()
        self.ranking = Ranking(self.config.arquivo_ranking)
        self.rodada: Rodada | None = None
        self.treinador: Treinador | None = None
        self.pendente_ranking: int | None = None   # tempo da última rodada humana ainda não salva
        self.cruzamento_visivel: Cruzamento = self._cruzamento_demonstracao()
        self.base_fixo = avaliar(SemaforoFixo(), self.config.treino.sementes_validacao,
                                 self.config.treino.passos_por_episodio, self.config.simulacao)
        self._ouvintes: list[Ouvinte] = []
        self._inicio_treino = 0.0

    # ----- eventos -----
    def inscrever(self, ouvinte: Ouvinte) -> None:
        self._ouvintes.append(ouvinte)

    def _publicar(self, evento: Evento) -> None:
        for ouvinte in self._ouvintes:
            ouvinte(evento)

    # ----- estado consultado pela interface -----
    @property
    def treinando(self) -> bool:
        return self.treinador is not None

    @property
    def ocupado(self) -> bool:
        return self.rodada is not None or self.treinando

    @property
    def rodada_humana(self) -> bool:
        return self.rodada is not None and self.rodada.humana

    @property
    def curva(self) -> list[float]:
        return self.treinador.curva if self.treinador else self._curva_salva

    @property
    def fracao_passo(self) -> float:
        return self.rodada.fracao_passo if self.rodada else 1.0

    @property
    def mostrando_demonstracao(self) -> bool:
        return self.cruzamento_visivel is self._demonstracao or self.treinando

    @property
    def tempo_restante(self) -> int:
        if self.mostrando_demonstracao:
            return self.config.rodada.passos
        cruz = self.cruzamento_visivel
        return max(0, cruz.passos - cruz.t)

    def nome_modo(self, modo: ModoRodada) -> str:
        if modo is ModoRodada.VOCE:
            return "Você"
        if modo is ModoRodada.FIXO:
            return "Semáforo comum"
        return "IA" if self.treinada else "IA sem treino"

    # ----- rodadas -----
    def iniciar_rodada(self, modo: ModoRodada) -> None:
        if self.treinando:
            return
        politica = {
            ModoRodada.VOCE: None,
            ModoRodada.FIXO: SemaforoFixo(),
            ModoRodada.IA: PoliticaAprendida(self.agente, self.observador),
        }[modo]
        self.rodada = Rodada(modo, politica, self.config.rodada, self.config.simulacao)
        self.cruzamento_visivel = self.rodada.cruzamento
        if modo is ModoRodada.VOCE:
            self.pendente_ranking = None
        self._publicar(RodadaIniciada(modo))

    def pedir_troca(self) -> None:
        if self.rodada is not None:
            self.rodada.pedir_troca()

    def _terminar_rodada(self) -> None:
        rodada, self.rodada = self.rodada, None
        cruz = rodada.cruzamento
        ia_valida = rodada.modo is not ModoRodada.IA or self.treinada
        resultado = Resultado(rodada.modo, self.nome_modo(rodada.modo), cruz.tempo_perdido,
                              cruz.carros_que_passaram, ia_valida)
        self.placar.registrar(resultado)
        venceu_ia = None
        if rodada.humana:
            self.pendente_ranking = cruz.tempo_perdido
            ia = self.placar.ia_de_referencia()
            if ia is not None:
                venceu_ia = cruz.tempo_perdido <= ia.tempo_perdido
        self._publicar(RodadaTerminada(resultado, venceu_ia))

    def salvar_no_ranking(self, nome: str) -> None:
        if self.pendente_ranking is None:
            return
        self.ranking.adicionar(nome, self.pendente_ranking)
        self.pendente_ranking = None

    # ----- treino -----
    def iniciar_treino(self) -> None:
        if self.ocupado:
            return
        self.agente.reiniciar()
        self.treinada = False
        self.treinador = Treinador(self.agente, self.observador, self.config.treino, self.config.simulacao)
        self._inicio_treino = time.perf_counter()

    def apagar_aprendizado(self) -> None:
        if self.ocupado:
            return
        self.agente.reiniciar()
        self.treinada = False
        self._curva_salva = []
        self.placar.remover(ModoRodada.IA)
        try:
            self.config.arquivo_ia.unlink(missing_ok=True)
        except OSError:
            pass

    def _avancar_treino(self) -> None:
        treinador = self.treinador
        decorrido_ms = (time.perf_counter() - self._inicio_treino) * 1000
        alvo = min(treinador.total_passos,
                   int(treinador.total_passos * decorrido_ms / self.config.treino.duracao_ms) + 1)
        limite = time.perf_counter() + self.ORCAMENTO_TREINO_MS / 1000
        while treinador.passos_feitos < alvo and time.perf_counter() < limite:
            treinador.avancar(min(400, alvo - treinador.passos_feitos))
        if treinador.cruzamento is not None:
            self.cruzamento_visivel = treinador.cruzamento
        if treinador.concluido:
            self._concluir_treino()

    def _concluir_treino(self) -> None:
        treinador, self.treinador = self.treinador, None
        self.treinada = True
        self._curva_salva = list(treinador.curva)
        self.placar.remover(ModoRodada.IA)
        self.cruzamento_visivel = self._cruzamento_demonstracao()
        try:
            self.agente.salvar(self.config.arquivo_ia, treinada=True, curva=self._curva_salva)
        except OSError:
            pass
        self._publicar(TreinoConcluido(treinador.episodio, treinador.passos_feitos // 3600))

    def _carregar_ia(self) -> None:
        if not self.config.arquivo_ia.exists():
            return
        try:
            dados = self.agente.carregar(self.config.arquivo_ia)
        except (OSError, ValueError, KeyError, TypeError):
            self.agente.reiniciar()
            return
        self.treinada = bool(dados.get("treinada"))
        self._curva_salva = [float(v) for v in dados.get("curva", [])]

    # ----- relógio -----
    def atualizar(self, dt_ms: float) -> None:
        if self.rodada is not None:
            self.rodada.atualizar(dt_ms)
            if self.rodada.terminou:
                self._terminar_rodada()
        elif self.treinador is not None:
            self._avancar_treino()

    def _cruzamento_demonstracao(self) -> Cruzamento:
        """Cruzamento parado com alguns carros, só para a tela inicial não ficar vazia."""
        cruz = Cruzamento(self.config.rodada.semente, self.config.rodada.passos, False, self.config.simulacao)
        for _ in range(24):
            cruz.passo(False)
        self._demonstracao = cruz
        return cruz
