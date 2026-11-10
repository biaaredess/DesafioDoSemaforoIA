"""Janela principal: laço de eventos, abas, tela cheia de jogo e reação aos eventos."""
import pygame

from ..jogo import ControladorJogo, Evento, ModoRodada, RodadaIniciada, RodadaTerminada, TreinoConcluido
from .paineis import Cabecalho, PainelJogar, PainelPensa, PainelTreinar, TelaPensa
from .palco import Cartao, Palco
from .tela import Resolucao, Tela
from .tema import Layout, Paleta

FPS = 60
DURACAO_ABERTURA_MS = 520
EVENTOS_MOUSE = (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)


def suavizar(t: float) -> float:
    """Aceleração e frenagem suaves (ease-in-out cúbico)."""
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


class Aplicacao:
    def __init__(self, controlador: ControladorJogo | None = None):
        pygame.init()
        pygame.display.set_caption("Desafio do Semáforo")
        pygame.display.set_icon(self._icone())
        self._tamanho_janela = self._tamanho_inicial()
        self.tela_cheia_monitor = False
        self._configurar_janela(self._tamanho_janela)
        self.relogio = pygame.time.Clock()
        self.rodando = True

        self.controlador = controlador or ControladorJogo()
        self.controlador.inscrever(self._ao_evento)

        self.palco = Palco(self.controlador, self.controlador.pedir_troca)
        self.cabecalho = Cabecalho(self.abrir_aba)
        self.paineis = {
            "jogar": PainelJogar(self.controlador),
            "treinar": PainelTreinar(self.controlador),
            "pensa": PainelPensa(self.controlador),
        }
        self.tela_pensa = TelaPensa()
        self.aba = "jogar"
        self.tela_cheia = False      # rodada de quem joga: o painel sai e o cruzamento ocupa tudo
        self._progresso = 0.0        # 0 = painel aberto, 1 = tela cheia (antes da suavização)
        self._cursor_mao = False

    # ----- janela e resolução -----
    @staticmethod
    def _tamanho_inicial() -> tuple[int, int]:
        """Maior janela 16:9 que cabe com folga no monitor."""
        try:
            largura, altura = pygame.display.get_desktop_sizes()[0]
        except (pygame.error, IndexError):
            return Layout.LARGURA, Layout.ALTURA
        k = max(0.5, min(largura * 0.92 / Layout.LARGURA, altura * 0.86 / Layout.ALTURA))
        return round(Layout.LARGURA * k), round(Layout.ALTURA * k)

    def _configurar_janela(self, tamanho: tuple[int, int], tela_cheia: bool = False) -> None:
        """Cria a janela e prepara o desenho na resolução nativa dela (sem esticar imagem)."""
        if tela_cheia:
            try:
                tamanho = pygame.display.get_desktop_sizes()[0]
            except (pygame.error, IndexError):
                pass
            self.janela = pygame.display.set_mode(tamanho, pygame.FULLSCREEN)
        else:
            self.janela = pygame.display.set_mode(tamanho, pygame.RESIZABLE)
        self.tela_cheia_monitor = tela_cheia
        largura, altura = self.janela.get_size()
        self.area = Resolucao.ajustar(largura, altura)
        self.tela = Tela(self.janela.subsurface(self.area))
        self.superficie_painel = Tela.nova((Layout.LARGURA - Layout.PAINEL_X, Layout.ALTURA))

    def _alternar_tela_cheia(self) -> None:
        if self.tela_cheia_monitor:
            self._configurar_janela(self._tamanho_janela)
        else:
            self._configurar_janela(self._tamanho_janela, tela_cheia=True)

    # ----- navegação -----
    def abrir_aba(self, aba: str) -> None:
        self.aba = aba
        self.cabecalho.selecionar(aba)

    @property
    def painel_x(self) -> int:
        return round(Layout.PAINEL_X + (Layout.LARGURA - Layout.PAINEL_X) * self.palco.abertura)

    def _sair_da_tela_cheia(self) -> None:
        self.palco.fechar_cartao()
        self.tela_cheia = False

    # ----- eventos do jogo -----
    def _ao_evento(self, evento: Evento) -> None:
        ctrl = self.controlador
        if isinstance(evento, RodadaIniciada):
            self.palco.fechar_cartao()
            if evento.modo is ModoRodada.VOCE:
                self.tela_cheia = True
        elif isinstance(evento, RodadaTerminada):
            r = evento.resultado
            itens = [("rotulo", r.nome), ("grande", str(r.tempo_perdido)), ("texto", "segundos perdidos no trânsito")]
            cor = Paleta.IDENTIDADE[r.modo]
            if r.modo is ModoRodada.VOCE:
                if evento.venceu_ia is True:
                    itens.append(("destaque", "Você venceu a IA!"))
                elif evento.venceu_ia is False:
                    itens.append(("alerta", "A IA venceu desta vez"))
                self.palco.mostrar_cartao(Cartao(itens, cor, ao_salvar_nome=ctrl.salvar_no_ranking,
                                                 ao_fechar=self._sair_da_tela_cheia))
            else:
                self.palco.mostrar_cartao(Cartao(itens, cor))
        elif isinstance(evento, TreinoConcluido):
            episodios = f"{evento.episodios:,}".replace(",", ".")
            self.palco.mostrar_cartao(Cartao([
                ("rotulo", "Treino concluído"),
                ("texto", f"{episodios} partidas, {evento.horas} horas de trânsito"),
            ], Paleta.VERDE))

    # ----- laço principal -----
    def executar(self) -> None:
        while self.rodando:
            dt = min(100, self.relogio.tick(FPS))
            for evento in pygame.event.get():
                self._tratar(evento)
            self.controlador.atualizar(dt)
            self._animar_abertura(dt)
            self._desenhar()
            pygame.display.flip()
        pygame.quit()

    def _animar_abertura(self, dt: float) -> None:
        alvo = 1.0 if self.tela_cheia else 0.0
        passo = dt / DURACAO_ABERTURA_MS
        if self._progresso < alvo:
            self._progresso = min(alvo, self._progresso + passo)
        elif self._progresso > alvo:
            self._progresso = max(alvo, self._progresso - passo)
        self.palco.abertura = suavizar(self._progresso)

    def _tratar(self, evento: pygame.event.Event) -> None:
        if evento.type == pygame.QUIT:
            self.rodando = False
            return
        if evento.type == pygame.VIDEORESIZE and not self.tela_cheia_monitor:
            self._tamanho_janela = (max(640, evento.w), max(360, evento.h))
            self._configurar_janela(self._tamanho_janela)
            return
        if evento.type in EVENTOS_MOUSE:
            evento = self._para_logico(evento)
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_F11:
                self._alternar_tela_cheia()
                return
            if evento.key == pygame.K_ESCAPE and self.tela_cheia_monitor:
                self._alternar_tela_cheia()
                return
            if evento.key == pygame.K_SPACE and not self.palco.digitando:
                self.controlador.pedir_troca()
                return
            if evento.key == pygame.K_DELETE and evento.mod & pygame.KMOD_CTRL and not self.controlador.ocupado:
                self.controlador.ranking.limpar_dia()     # atalho de quem cuida do estande
                return
        if evento.type == pygame.TEXTINPUT and evento.text == " " and not self.palco.digitando:
            return

        if self.aba == "pensa" and not self.tela_cheia:
            if self.tela_pensa.tratar_evento(evento) and evento.type != pygame.MOUSEMOTION:
                return
        elif self.palco.tratar_evento(evento) and evento.type != pygame.MOUSEMOTION:
            return

        painel_visivel = self.palco.abertura < 0.01 and not self.tela_cheia
        if painel_visivel:
            local = self._para_painel(evento)
            for alvo in (self.cabecalho, self.paineis[self.aba]):
                if alvo.tratar_evento(local) and evento.type != pygame.MOUSEMOTION:
                    break
        if evento.type == pygame.MOUSEMOTION:
            self._atualizar_cursor(evento.pos, painel_visivel)

    def _para_logico(self, evento: pygame.event.Event) -> pygame.event.Event:
        """Pixels reais da janela → coordenadas lógicas de 1280×720."""
        dados = dict(evento.dict)
        x, y = evento.pos
        dados["pos"] = ((x - self.area.x) / Resolucao.k, (y - self.area.y) / Resolucao.k)
        return pygame.event.Event(evento.type, dados)

    def _para_painel(self, evento: pygame.event.Event) -> pygame.event.Event:
        """Traduz a posição do mouse para as coordenadas locais do painel."""
        if evento.type not in EVENTOS_MOUSE:
            return evento
        dados = dict(evento.dict)
        dados["pos"] = (evento.pos[0] - self.painel_x, evento.pos[1])
        return pygame.event.Event(evento.type, dados)

    def _atualizar_cursor(self, pos, painel_visivel: bool) -> None:
        no_palco = self.palco.rect.collidepoint(pos) and self.aba != "pensa"
        quer_mao = (no_palco and (self.controlador.rodada_humana or self.palco.sob_mouse)) or (
            painel_visivel and (self.cabecalho.sob_mouse or self.paineis[self.aba].sob_mouse))
        if quer_mao != self._cursor_mao:
            self._cursor_mao = quer_mao
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if quer_mao else pygame.SYSTEM_CURSOR_ARROW)
            except pygame.error:
                pass  # alguns ambientes (ex.: sem servidor gráfico) não têm cursores do sistema

    def _desenhar(self) -> None:
        self.janela.fill(Paleta.FUNDO)
        if self.aba == "pensa" and not self.tela_cheia and self.palco.abertura == 0:
            self.tela_pensa.desenhar(self.tela)
        else:
            self.palco.desenhar(self.tela)

        x = self.painel_x
        if x < Layout.LARGURA:
            s = self.superficie_painel
            s.fill(Paleta.FUNDO)
            self.cabecalho.desenhar(s)
            painel = self.paineis[self.aba]
            painel.atualizar()
            painel.desenhar(s)
            self.tela.blit(s, (x, 0))
            self.tela.rect(Paleta.MEIO_FIO, (x - 3, 0, 6, Layout.ALTURA))   # meio-fio entre os dois

    @staticmethod
    def _icone() -> pygame.Surface:
        icone = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.polygon(icone, Paleta.TINTA, [(13, 0), (19, 0), (24, 5), (24, 27), (19, 32), (13, 32),
                                                   (8, 27), (8, 5)])
        for i, cor in enumerate((Paleta.VERMELHO, Paleta.AMARELO, Paleta.VERDE)):
            pygame.draw.circle(icone, cor, (16, 7 + i * 9), 4)
        return icone
