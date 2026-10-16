# Análise do experimento: RodadaA_reduzida

## 1. Auditoria

- Execuções registradas: 66 | com erro: 0
- Execuções NÃO validadas (sobreposição/fora da faixa/fallback): 1
    - com_rotacao fu10 s=42: fora=0 pares=1 fallbacks=0 empacotados=10/10
- Execuções que atingiram o limite de tempo: 0
- Instâncias com pelo menos uma execução cortada: nenhuma

## 2. L por instância (média ± desvio entre sementes)

instância        n      sem rotação      com rotação  diferença   rot.  cortada
blasz2           1     22.00± 0.00     20.00± 0.00      -2.00    31%         
blazewicz1       1      8.00± 0.00      8.00± 0.00      +0.00    14%         
blazewicz2       1     15.00± 0.00     14.00± 0.00      -1.00     7%         
blazewicz3       1     21.00± 0.00     21.00± 0.00      +0.00    10%         
blazewicz4       1     29.00± 0.00     28.00± 0.00      -1.00     7%         
dagli1           1     23.00± 0.00     23.00± 0.00      +0.00    20%         
fu               1     34.00± 0.00     33.00± 0.00      -1.00    42%         
fu10             1     30.00± 0.00     29.00± 0.00      -1.00    40%         
fu5              1     18.00± 0.00     17.00± 0.00      -1.00    60%         
fu6              1     24.00± 0.00     21.00± 0.00      -3.00    50%         
fu7              1     24.00± 0.00     21.00± 0.00      -3.00    43%         
fu8              1     24.00± 0.00     23.00± 0.00      -1.00    50%         
fu9              1     27.00± 0.00     25.00± 0.00      -2.00    67%         
jakobs1          1     12.00± 0.00     12.00± 0.00      +0.00    40%         
poly1a           1     17.00± 0.00     15.00± 0.00      -2.00    87%         
poly1b           1     19.00± 0.00     19.00± 0.00      +0.00    53%         
poly1c           1     13.00± 0.00     11.00± 0.00      -2.00    67%         
poly1d           1     13.00± 0.00     13.00± 0.00      +0.00    73%         
poly1e           1     13.00± 0.00     12.00± 0.00      -1.00    73%         
rco1             1      8.00± 0.00      8.00± 0.00      +0.00    29%         
rco2             1     15.00± 0.00     15.00± 0.00      +0.00    14%         
rco3             1     23.00± 0.00     22.00± 0.00      -1.00    10%         
rco4             1     29.00± 0.00     29.00± 0.00      +0.00    11%         
shapes2          1     14.00± 0.00     14.00± 0.00      +0.00     0%         
shapes4          1     26.00± 0.00     26.00± 0.00      +0.00     0%         
shapes5          1     32.00± 0.00     32.00± 0.00      +0.00     0%         
shirts1-2        1     13.00± 0.00     13.00± 0.00      +0.00     8%         
shirts2-4        1     20.00± 0.00     20.00± 0.00      +0.00     4%         
three            1      7.00± 0.00      6.00± 0.00      -1.00    33%         
threep2          1     10.00± 0.00     10.00± 0.00      +0.00    17%         
threep2w9        1      9.00± 0.00      8.00± 0.00      -1.00    17%         
threep3          1     14.00± 0.00     14.00± 0.00      +0.00    22%         
threep3w9        1     12.00± 0.00     10.00± 0.00      -2.00    22%         

## 3. Comparação (menor L é melhor)

Todas as instâncias (33 instâncias): com rotação melhor em 17, empate em 16, pior em 0
  Wilcoxon pareado: p = 0.0002   (L médio sem rotação = 18.73, com rotação = 17.94)

## 4. Uso de rotação (versão com rotação)

- Instâncias em que houve rotação em alguma execução: 30/33
- Instâncias que só permitem 0 grau (rotação impossível): 3: shapes2, shapes4, shapes5

## 5. Tempo médio por execução (s) — medido em paralelo

- sem_rotacao: média 134.0 s | soma 1.23 h de relógio por processo
- com_rotacao: média 305.0 s | soma 2.80 h de relógio por processo
