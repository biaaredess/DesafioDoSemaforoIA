import random

import pytest

from semaforo.config import ConfigTreino
from semaforo.ia import (Acao, AgenteQLearning, ObservadorEstado, PoliticaAprendida, RegraEscrita,
                         SemaforoFixo, Treinador, avaliar, executar_episodio)
from semaforo.simulacao import Cruzamento, Eixo


def test_codificacao_de_estado_e_reversivel():
    obs = ObservadorEstado()
    vistos = set()
    for v in range(5):
        for r in range(5):
            for antigo in (False, True):
                s = obs.codificar(v, r, antigo)
                assert obs.decodificar(s) == (v, r, antigo)
                vistos.add(s)
    assert vistos == set(range(obs.n_estados))


@pytest.mark.parametrize("fila,faixa", [(0, 0), (1, 1), (3, 1), (4, 2), (7, 2), (8, 3), (13, 3), (14, 4), (99, 4)])
def test_faixas_de_fila(fila, faixa):
    assert ObservadorEstado().faixa_da_fila(fila) == faixa


def test_observador_le_filas_do_verde_e_do_vermelho():
    cruz = Cruzamento(1, 100)
    for _ in range(40):
        cruz.passo(False)          # verde parado no Norte–Sul: o Leste–Oeste acumula
    obs = ObservadorEstado()
    verde, vermelho, antigo = obs.decodificar(obs.observar(cruz))
    assert vermelho == obs.faixa_da_fila(cruz.fila(Eixo.LESTE_OESTE)) > 0
    assert verde == obs.faixa_da_fila(cruz.fila(Eixo.NORTE_SUL))
    assert antigo


def test_atualizacao_q_segue_bellman():
    agente = AgenteQLearning(n_estados=2, gamma=0.9)
    agente.q[1] = [-10.0, -4.0]
    erro = agente.aprender(0, Acao.TROCAR, recompensa=-2.0, estado_seguinte=1, alpha=0.5)
    alvo = -2.0 + 0.9 * -4.0
    assert erro == pytest.approx(alvo)
    assert agente.q[0][Acao.TROCAR] == pytest.approx(0.5 * alvo)
    assert agente.melhor_acao(0) is Acao.MANTER


def test_exploracao_total_e_nenhuma():
    agente = AgenteQLearning(1)
    agente.q[0] = [0.0, 5.0]
    rng = random.Random(0)
    assert all(agente.escolher(0, 0.0, rng) is Acao.TROCAR for _ in range(50))
    escolhas = {agente.escolher(0, 1.0, rng) for _ in range(200)}
    assert escolhas == {Acao.MANTER, Acao.TROCAR}


def test_salvar_e_carregar(tmp_path):
    a = AgenteQLearning(4)
    a.q[2] = [1.5, -3.0]
    a.visitas[2] = 7
    caminho = tmp_path / "ia.json"
    a.salvar(caminho, treinada=True)
    b = AgenteQLearning(4)
    extras = b.carregar(caminho)
    assert b.q == a.q and b.visitas == a.visitas and extras["treinada"] is True


def test_politicas_fixas_respeitam_regras():
    fixo = executar_episodio(SemaforoFixo(12), 2026, 160, False)
    assert fixo.semaforo.trocas >= 160 // (12 + 3) - 1
    regra = executar_episodio(RegraEscrita(), 2026, 160, False)
    assert regra.tempo_perdido < fixo.tempo_perdido


def test_treino_curto_melhora_a_ia():
    obs = ObservadorEstado()
    agente = AgenteQLearning(obs.n_estados)
    cfg = ConfigTreino(episodios=300, intervalo_curva=100)
    treinador = Treinador(agente, obs, cfg)
    antes = treinador.curva[0]
    treinador.treinar_tudo()
    assert treinador.concluido and len(treinador.curva) == 4
    assert treinador.curva[-1] < antes


@pytest.mark.lento
def test_treino_completo_vence_semaforo_comum_e_regra():
    obs = ObservadorEstado()
    agente = AgenteQLearning(obs.n_estados)
    cfg = ConfigTreino()
    Treinador(agente, obs, cfg).treinar_tudo()
    sementes, passos = cfg.sementes_validacao, cfg.passos_por_episodio
    ia = avaliar(PoliticaAprendida(agente, obs), sementes, passos)
    assert ia < avaliar(SemaforoFixo(), sementes, passos)
    assert ia < avaliar(RegraEscrita(), sementes, passos)
