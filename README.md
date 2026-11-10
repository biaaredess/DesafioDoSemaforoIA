# Desafio do Semáforo

Jogo para feira de ciências: **você consegue controlar o trânsito melhor que uma inteligência artificial?**
O visitante troca o sinal de um cruzamento, depois assiste a um semáforo comum e a uma IA que
**aprendeu sozinha** por aprendizado por reforço (Q-learning). Todos enfrentam
exatamente os mesmos carros, e ganha quem deixar os carros parados por menos tempo.

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

No Windows, use `.venv\Scripts\python main.py`.

| Tecla / ação                | O que faz                                   |
|-----------------------------|---------------------------------------------|
| Botão vermelho **TROCAR**, `Espaço` ou clique no cruzamento | troca o sinal (na sua rodada) |
| `F11`                       | tela cheia na resolução do monitor (ideal para o estande) |
| `Esc`                       | sai da tela cheia                           |
| `Ctrl` + `Delete`           | apaga o ranking do dia (para quem cuida do estande) |

### Roteiro sugerido no estande

1. **Jogar**: o painel sai de cena e o cruzamento ocupa a tela inteira, com o temporizador em
   cima e o botão vermelho **TROCAR** na grama. São 160 s de trânsito; no fim, o nome vai para o ranking.
2. *Semáforo* e *IA joga* para comparar (a IA sem treino vai mal!). Máquinas jogam em 3×.
3. **Treinar a IA** → *Começar o treino*: 1.500 partidas em ~14 s, com o gráfico caindo ao vivo.
4. Voltar e clicar *IA joga* de novo.
5. **Como a IA pensa**: os três passos, o código do Q-learning e o "cérebro"
   (tabela Q) que a IA preencheu sozinha.

## Arquitetura

O projeto é orientado a objetos e separado em camadas. Cada camada só depende das de baixo,
então a IA e as regras **não sabem que o pygame existe**: dá para testá-las e treiná-las sem janela.

```
main.py                      ponto de entrada
semaforo/
├── config.py                todos os parâmetros (simulação, rodada, treino, arquivos)
├── simulacao/               MODELO DO TRÂNSITO (Python puro)
│   ├── tipos.py             Eixo, Direcao, CorLuz
│   ├── demanda.py           Demanda: quantos carros chegam (horário de pico)
│   ├── semaforo.py          Semaforo: verde → amarelo → vermelho geral → verde
│   ├── faixa.py             Faixa: autômato celular de uma rua
│   └── cruzamento.py        Cruzamento: 4 faixas + semáforo + tempo perdido
├── ia/                      INTELIGÊNCIA ARTIFICIAL (Python puro)
│   ├── estado.py            ObservadorEstado: cruzamento → uma de 50 "situações"
│   ├── agente_q.py          AgenteQLearning: tabela Q, ε-gulosa, Bellman, salvar/carregar
│   ├── politicas.py         Politica (abstrata), SemaforoFixo, PoliticaAprendida e RegraEscrita
│   │                        (a regra if/else não aparece no jogo; é referência no treino pelo terminal)
│   ├── avaliacao.py         executar_episodio, avaliar
│   ├── treinador.py         Treinador: Q-learning em fatias, para animar na tela
│   └── treinar.py           treino pelo terminal (python -m semaforo.ia.treinar)
├── jogo/                    REGRAS DO JOGO (Python puro)
│   ├── rodada.py            Rodada, ModoRodada (você, semáforo comum, IA)
│   ├── placar.py            Placar, Resultado
│   ├── ranking.py           Ranking do dia (dados/ranking.json)
│   ├── eventos.py           eventos publicados para a interface (padrão observador)
│   └── controlador.py       ControladorJogo: fachada única usada pela interface
└── interface/               DESIGN (pygame)
    ├── tema.py              paleta escura (asfalto) + trio do semáforo, fontes, escala tipográfica, layout
    ├── tela.py              desenho em resolução nativa (coordenadas lógicas → pixels reais)
    ├── formas.py            a placa de cantos chanfrados usada em toda a interface
    ├── geometria.py         células da simulação → pixels
    ├── cenario.py           grama, calçadas com meio-fio amarelo, faixas de pedestre, passarelas
    ├── sprites.py           carros vistos de cima e semáforos de 3 luzes (desenhados por código)
    ├── animacao.py          interpolação suave dos carros e a fila de espera visível
    ├── palco.py             Palco (câmera, temporizador, botão TROCAR) e Cartao (resultado)
    ├── widgets.py           Botao, BotaoTrocar, BotaoFechar, Abas, Alternancia, CampoTexto
    ├── grafico.py           curva de aprendizado
    ├── paineis/             um painel por aba + a tela "Como a IA pensa"
    ├── recursos/fontes/     Bungee, Barlow Semi Condensed e DejaVu Sans Mono (licenças junto)
    └── app.py               Aplicacao: laço principal e roteamento de eventos
```

## Como a IA funciona

* **Simulação**: cada rua é uma fila de células; 1 passo = 1 segundo. Carros só entram no cruzamento
  com verde. Cada carro parado soma 1 s ao *tempo perdido*. A troca de sinal leva 3 s
  (2 s de amarelo + 1 s de vermelho geral), então trocar demais também custa caro.
* **O que a IA vê** (`ObservadorEstado`): fila no verde e fila no vermelho, cada uma em 5 faixas
  (0, 1–3, 4–7, 8–13, 14+), e se o verde abriu há menos de 5 s. São 5 × 5 × 2 = 50 situações.
* **O que ela decide**: manter ou trocar, só quando a troca é possível.
* **Recompensa**: −1 por segundo para cada carro parado, somada até a próxima decisão.
* **Aprendizado** (`AgenteQLearning`):
  `Q[s][a] ← Q[s][a] + α · (r + γ · max Q[s'] − Q[s][a])`, com γ = 0,9;
  a curiosidade ε começa em 100% e cai até 3%; α cai de 0,2 para 0,03.
* **Treino**: 1.500 partidas de 300 s com demanda sorteada (a IA não decora uma situação só).
  A curva do gráfico é medida em 3 partidas de teste que ela nunca viu.

Treino pelo terminal, com comparação entre as políticas:

```bash
.venv/bin/python -m semaforo.ia.treinar            # só mostra os números
.venv/bin/python -m semaforo.ia.treinar --salvar   # grava em dados/ia_treinada.json
```

Resultado típico (tempo perdido médio nas partidas de teste, menos é melhor):
semáforo comum ≈ 2.430 s, regra `if/else` escrita à mão ≈ 1.160 s, **IA treinada ≈ 990 s**.

A IA treinada no jogo é salva em `dados/ia_treinada.json` e recarregada ao abrir o jogo.
O botão *Apagar o que ela aprendeu* apaga esse arquivo.

## Testes

```bash
.venv/bin/python -m pytest              # todos (inclui um treino completo, ~8 s)
.venv/bin/python -m pytest -m "not lento"
```

Os testes cobrem determinismo e conservação de carros na simulação, o ciclo do semáforo,
a codificação de estados, a equação de Bellman, persistência da IA, o controlador
(rodadas, ritmo 3× das máquinas, ranking, treino) e se a IA treinada vence o semáforo comum e a regra.

## Ajustes

Tudo fica em `semaforo/config.py`: duração da rodada, semente dos carros, velocidade das máquinas,
número de partidas de treino, hiperparâmetros do Q-learning e duração da animação do treino.
Se mudar `celulas_chegada`, o desenho do cruzamento se adapta sozinho (`GeometriaCruzamento`),
mas vale rodar `python -m semaforo.ia.treinar` para confirmar que a IA continua vencendo a regra.
