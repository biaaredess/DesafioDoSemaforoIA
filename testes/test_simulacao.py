from semaforo.config import ConfigSimulacao
from semaforo.simulacao import VAZIO, CorLuz, Cruzamento, Direcao, Eixo, Faixa, Semaforo


def contar_carros(cruz: Cruzamento) -> int:
    return sum(sum(1 for c in f.celulas if c != VAZIO) + f.espera_externa for f in cruz.faixas)


def test_mesma_semente_gera_mesmo_transito():
    a, b = Cruzamento(42, 200), Cruzamento(42, 200)
    for t in range(200):
        trocar = t % 15 == 0
        assert a.passo(trocar) == b.passo(trocar)
    assert a.tempo_perdido == b.tempo_perdido
    assert [f.celulas for f in a.faixas] == [f.celulas for f in b.faixas]


def test_carros_nao_somem_nem_aparecem_do_nada():
    cruz = Cruzamento(7, 300, demanda_aleatoria=True)
    for t in range(300):
        criados_antes = cruz._proximo_id - 1
        cruz.passo(t % 10 == 0)
        criados = cruz._proximo_id - 1
        assert criados >= criados_antes
    na_tela = sum(1 for f in cruz.faixas for c in f.celulas if c != VAZIO)
    assert na_tela + cruz.carros_que_passaram == cruz._proximo_id - 1


def test_um_carro_por_celula_e_ids_unicos():
    cruz = Cruzamento(3, 200)
    for t in range(200):
        cruz.passo(t % 9 == 0)
        ids = [c for f in cruz.faixas for c in f.celulas if c != VAZIO]
        assert len(ids) == len(set(ids))


def test_sem_verde_ninguem_atravessa_no_eixo_fechado():
    cruz = Cruzamento(1, 120)
    for _ in range(120):
        cruz.passo(False)   # o verde fica sempre no Norte–Sul
    for f in cruz.faixas:
        if f.direcao.eixo is Eixo.LESTE_OESTE:
            assert all(c == VAZIO for c in f.celulas[f.chegada:])
    assert cruz.fila(Eixo.LESTE_OESTE) > 0


def test_ciclo_do_semaforo():
    s = Semaforo(passos_troca=3)
    assert s.cor(Eixo.NORTE_SUL) is CorLuz.VERDE and s.cor(Eixo.LESTE_OESTE) is CorLuz.VERMELHO
    assert s.iniciar_troca()
    assert not s.iniciar_troca()           # não dá para trocar no meio da troca
    s.avancar()
    assert s.cor(Eixo.NORTE_SUL) is CorLuz.AMARELO
    s.avancar()
    assert s.cor(Eixo.NORTE_SUL) is CorLuz.VERMELHO and s.cor(Eixo.LESTE_OESTE) is CorLuz.VERMELHO
    s.avancar()
    assert s.verde is Eixo.LESTE_OESTE and s.tempo_verde == 0 and s.pode_trocar
    assert s.trocas == 1


def test_faixa_parada_no_vermelho_conta_espera():
    f = Faixa(Direcao.NORTE, celulas_chegada=3, celulas_cruzamento=2)
    ids = iter(range(1, 100))
    total_parados = 0
    for _ in range(6):
        parados, _ = f.avancar(aberta=False, chegou_carro=True, novo_id=lambda: next(ids))
        total_parados += parados
    assert f.celulas[:3] == [3, 2, 1]       # fila cheia até a faixa de pedestre
    assert f.espera_externa == 3            # o resto espera fora da tela
    assert f.fila() == 6
    assert total_parados > 0


def test_tempo_perdido_soma_parados():
    cruz = Cruzamento(5, 50, config=ConfigSimulacao())
    soma = sum(cruz.passo(False) for _ in range(50))
    assert soma == cruz.tempo_perdido
    assert cruz.terminou
