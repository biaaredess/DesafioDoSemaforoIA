"""Ponto de entrada do jogo.  Uso:  python main.py   (F11 = tela cheia)"""
from semaforo.interface.app import Aplicacao


def main() -> None:
    Aplicacao().executar()


if __name__ == "__main__":
    main()
