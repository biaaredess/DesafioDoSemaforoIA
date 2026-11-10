"""Desafio do Semáforo: você contra uma IA que aprende a controlar o trânsito.

Organização em camadas (cada uma só conhece as de baixo):

    simulacao/  modelo do cruzamento (carros, faixas, semáforo). Python puro.
    ia/         estado observado, políticas e o agente Q-learning. Python puro.
    jogo/       regras do jogo: rodadas, placar, ranking e treino. Python puro.
    interface/  tudo o que é visual (pygame): cenário, carros, painéis.
"""
