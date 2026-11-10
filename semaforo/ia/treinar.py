"""Treina a IA sem interface e compara com as outras políticas.

Uso:  python -m semaforo.ia.treinar [--salvar]
"""
import argparse
import time

from ..config import Config
from .agente_q import AgenteQLearning
from .avaliacao import avaliar
from .estado import ObservadorEstado
from .politicas import PoliticaAprendida, RegraEscrita, SemaforoFixo
from .treinador import Treinador


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salvar", action="store_true", help="grava a IA treinada em dados/")
    args = parser.parse_args()

    config = Config()
    observador = ObservadorEstado()
    agente = AgenteQLearning(observador.n_estados, config.treino.gamma)
    treinador = Treinador(agente, observador, config.treino, config.simulacao)

    inicio = time.perf_counter()
    treinador.treinar_tudo()
    duracao = time.perf_counter() - inicio
    print(f"Treino: {treinador.episodio} partidas, {treinador.passos_feitos} passos em {duracao:.1f} s")

    sementes = config.treino.sementes_validacao
    passos = config.treino.passos_por_episodio
    for politica in (SemaforoFixo(), RegraEscrita(), PoliticaAprendida(agente, observador)):
        print(f"  {politica.nome:<16} {avaliar(politica, sementes, passos, config.simulacao):8.0f} s perdidos")

    if args.salvar:
        agente.salvar(config.arquivo_ia, treinada=True, curva=treinador.curva)
        print(f"IA salva em {config.arquivo_ia}")


if __name__ == "__main__":
    main()
