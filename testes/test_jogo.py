from datetime import date

import pytest

from semaforo.config import Config, ConfigTreino
from semaforo.jogo import ControladorJogo, ModoRodada, Ranking, RodadaTerminada, TreinoConcluido


@pytest.fixture
def controlador(tmp_path):
    cfg = Config(treino=ConfigTreino(episodios=50, intervalo_curva=25, duracao_ms=1),
                 arquivo_ia=tmp_path / "ia.json", arquivo_ranking=tmp_path / "ranking.json")
    return ControladorJogo(cfg)


def jogar_ate_o_fim(ctrl: ControladorJogo) -> None:
    while ctrl.rodada is not None:
        ctrl.atualizar(300)


def test_rodada_de_maquina_registra_no_placar(controlador):
    eventos = []
    controlador.inscrever(eventos.append)
    controlador.iniciar_rodada(ModoRodada.FIXO)
    assert controlador.ocupado
    jogar_ate_o_fim(controlador)
    fim = [e for e in eventos if isinstance(e, RodadaTerminada)]
    assert len(fim) == 1
    assert controlador.placar.obter(ModoRodada.FIXO).tempo_perdido == fim[0].resultado.tempo_perdido


def test_maquinas_jogam_em_3x(controlador):
    controlador.iniciar_rodada(ModoRodada.FIXO)
    assert controlador.rodada.ms_por_passo == 100
    jogar_ate_o_fim(controlador)
    controlador.iniciar_rodada(ModoRodada.VOCE)
    assert controlador.rodada.ms_por_passo == 300


def test_rodada_humana_troca_quando_pede(controlador):
    controlador.iniciar_rodada(ModoRodada.VOCE)
    controlador.pedir_troca()
    controlador.atualizar(300)
    assert controlador.rodada.cruzamento.semaforo.trocas == 1
    controlador.atualizar(300)
    assert controlador.rodada.cruzamento.semaforo.trocas == 1   # o pedido não fica "guardado"
    jogar_ate_o_fim(controlador)
    assert controlador.pendente_ranking is not None
    controlador.salvar_no_ranking("Beatriz")
    assert controlador.ranking.do_dia()[0].nome == "Beatriz"
    assert controlador.pendente_ranking is None


def test_treino_salva_e_recarrega_ia(controlador):
    eventos = []
    controlador.inscrever(eventos.append)
    controlador.iniciar_treino()
    while controlador.treinando:
        controlador.atualizar(16)
    assert controlador.treinada
    assert any(isinstance(e, TreinoConcluido) for e in eventos)
    assert controlador.config.arquivo_ia.exists()

    outro = ControladorJogo(controlador.config)
    assert outro.treinada and outro.agente.q == controlador.agente.q

    outro.apagar_aprendizado()
    assert not outro.treinada and not controlador.config.arquivo_ia.exists()


def test_ia_sem_treino_nao_vale_como_referencia(controlador):
    controlador.iniciar_rodada(ModoRodada.IA)
    jogar_ate_o_fim(controlador)
    assert controlador.placar.ia_de_referencia() is None


def test_ranking_do_dia(tmp_path):
    dia = [date(2026, 11, 9)]
    r = Ranking(tmp_path / "r.json", hoje=lambda: dia[0])
    r.adicionar("  Ana   Clara ", 500)
    r.adicionar("", 400)
    assert [(e.nome, e.tempo_perdido) for e in r.do_dia()] == [("Anônimo", 400), ("Ana Clara", 500)]
    dia[0] = date(2026, 11, 10)
    assert Ranking(tmp_path / "r.json", hoje=lambda: dia[0]).do_dia() == []
