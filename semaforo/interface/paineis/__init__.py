"""Painéis do lado direito (um por aba) e a tela explicativa da aba 3."""
from .base import Painel
from .cabecalho import Cabecalho
from .painel_jogar import PainelJogar
from .painel_treinar import PainelTreinar
from .painel_pensa import PainelPensa, TelaPensa

__all__ = ["Painel", "Cabecalho", "PainelJogar", "PainelTreinar", "PainelPensa", "TelaPensa"]
