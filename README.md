*[Read this in English](README.en.md)*

# Simulador de Ordem de Embarque

Simulação em Python que compara diferentes métodos de embarque de passageiros em um avião, medindo o tempo total (em "ticks") que cada método leva até todos estarem sentados. Gera um gráfico comparativo e uma animação em GIF mostrando os quatro métodos embarcando lado a lado.

## O que o script faz

1. Monta um avião de `rows` fileiras × `seats_per_row` assentos (padrão: 30 fileiras, 6 assentos por fileira, no layout `Janela | Meio | Corredor || Corredor | Meio | Janela`).
2. Sorteia, **uma única vez**, um tempo fixo de "guardar bagagem" para cada passageiro (entre `min_stow_time` e `max_stow_time`). Esse tempo é o mesmo em todos os métodos e em todas as repetições — assim a comparação isola o efeito da **ordem de embarque**, e não da sorte de quem tem mala pequena ou grande.
3. Simula, tick a tick, um corredor de passagem única (ninguém ultrapassa ninguém). Quando um passageiro chega à sua fileira, ele "trava" o corredor pelo tempo de guardar a bagagem — e leva um tempo extra (`Seat_deley`) se precisar pedir para alguém que já está sentado no meio/corredor se levantar para dar passagem.
4. Roda cada método **várias vezes** (`TRIALS`, padrão 20), reembaralhando a ordem a cada repetição, e reporta média, desvio padrão, mínimo e máximo de ticks.
5. Gera dois arquivos de saída:
   - `comparacao_metodos.png`: gráfico de barras com a média (± desvio padrão) de cada método, do mais rápido ao mais lento.
   - `embarque_animado.gif`: animação com os quatro métodos embarcando simultaneamente, lado a lado, para comparação visual.

## Métodos de embarque simulados

| Método | Descrição |
|---|---|
| **Random** | Ordem totalmente aleatória, sem nenhuma organização por zona ou tipo de assento. |
| **Back to front** | Embarque por zonas, das fileiras de trás para as da frente (como a maioria das companhias aéreas faz hoje). Dentro de cada zona, a ordem é aleatória. |
| **Wilma** | Agrupa por tipo de assento: todos os passageiros de janela embarcam primeiro, depois os do meio, depois os do corredor. Reduz bastante a necessidade de pessoas já sentadas se levantarem para dar passagem. |
| **Steffen** | Método determinístico (sem aleatoriedade) inspirado no trabalho do físico Jason Steffen: janela → meio → corredor, alternando fileiras pares e ímpares dos dois lados do avião, para minimizar interferência entre passageiros vizinhos. |

## Requisitos

```
python >= 3.8
numpy
matplotlib
pillow
```

Instalação:

```bash
pip install numpy matplotlib pillow
```

## Como executar

```bash
python sim_visual.py
```

Os arquivos `comparacao_metodos.png` e `embarque_animado.gif` são salvos automaticamente na **mesma pasta onde o script está localizado**, independente de onde você o execute.

## Saída no terminal

```
Rodando 20 simulacoes por metodo (mesma 'lentidao' de bagagem por passageiro em todos os metodos/trials)...

Random          media= 1250.5  desvio_padrao=  92.2  min= 1115  max= 1414  (20 trials)
Back to front   media= 1904.2  desvio_padrao=  81.6  min= 1765  max= 2041  (20 trials)
Wilma           media=  940.9  desvio_padrao=  32.1  min=  875  max=  995  (20 trials)
Steffen         media=  400.0  desvio_padrao=   0.0  min=  400  max=  400  (20 trials)

Arquivos gerados: comparacao_metodos.png, embarque_animado.gif
```

> O desvio padrão de **0** no método Steffen não é erro: como esse método é 100% determinístico e o tempo de bagagem agora é fixo por passageiro, toda repetição produz exatamente o mesmo resultado.

## Parâmetros configuráveis (topo do arquivo)

| Parâmetro | Descrição | Padrão |
|---|---|---|
| `rows` | Número de fileiras do avião | 30 |
| `seats_per_row` | Assentos por fileira | 6 |
| `min_stow_time` / `max_stow_time` | Faixa de tempo (em ticks) para guardar a bagagem de mão | 5 / 25 |
| `Seat_deley` | Tempo extra quando é preciso pedir passagem a alguém já sentado | 10 |
| `TRIALS` | Número de repetições por método usadas para calcular média/desvio | 20 |
| `SKIP` | Subamostragem de frames na animação (quanto maior, GIF mais leve e menos suave) | 6 |

## Limitações conhecidas / próximos passos

- A animação usa uma execução única por método, separada dos `TRIALS` estatísticos — pode não representar exatamente o caso médio, especialmente nos métodos com maior desvio padrão (Random, Back to front).
- O modelo não simula fila externa com intervalo de leitura de cartão de embarque, grupos familiares/prioritários entrando juntos, nem bagagem excedente bloqueando fileiras diferentes da própria.
- Com poucos `TRIALS`, a distribuição pode ser assimétrica; um boxplot/histograma representaria melhor os dados do que apenas média ± desvio padrão.

## Licença

Uso livre para fins educacionais e de estudo.
