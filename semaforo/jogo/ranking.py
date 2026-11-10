"""Ranking do dia, gravado em JSON para sobreviver se o jogo for fechado."""
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class EntradaRanking:
    nome: str
    tempo_perdido: int
    data: str


class Ranking:
    TAMANHO_NOME = 18

    def __init__(self, caminho: Path, hoje=date.today):
        self.caminho = caminho
        self._hoje = hoje
        self._entradas = self._ler()

    def _ler(self) -> list[EntradaRanking]:
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            return [EntradaRanking(**d) for d in dados]
        except (OSError, ValueError, TypeError):
            return []

    def _gravar(self) -> None:
        try:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            self.caminho.write_text(json.dumps([asdict(e) for e in self._entradas], ensure_ascii=False),
                                    encoding="utf-8")
        except OSError:
            pass  # sem disco gravável o ranking continua valendo enquanto o jogo estiver aberto

    def adicionar(self, nome: str, tempo_perdido: int) -> EntradaRanking:
        nome = " ".join(nome.split())[: self.TAMANHO_NOME] or "Anônimo"
        entrada = EntradaRanking(nome, tempo_perdido, self._hoje().isoformat())
        self._entradas.append(entrada)
        self._gravar()
        return entrada

    def do_dia(self, limite: int | None = None) -> list[EntradaRanking]:
        hoje = self._hoje().isoformat()
        lista = sorted((e for e in self._entradas if e.data == hoje), key=lambda e: e.tempo_perdido)
        return lista[:limite] if limite else lista

    def limpar_dia(self) -> None:
        hoje = self._hoje().isoformat()
        self._entradas = [e for e in self._entradas if e.data != hoje]
        self._gravar()
