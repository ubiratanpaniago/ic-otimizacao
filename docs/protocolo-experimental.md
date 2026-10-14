# Protocolo experimental e registro de decisões

*Estado em 14/10/2026. Documento de continuidade: reúne o que foi decidido, corrigido e validado, para retomar o trabalho em outro computador e para escrever a seção de metodologia do artigo.*

Branch de trabalho: `feature/rotacao-dentro-do-bl` (parte de `main`).

---

## 1. Resumo em 10 linhas

1. O código usado no "Experimento Final" (`src/strip_packing_discretização_irregulares.py`, resultados em `results/agosto/ExperimentoFinal/`) **nunca rotacionava peças**: o laço de rotação ficava por fora do laço de pontos, e a rotação 0° sempre achava lugar.
2. Por isso os resultados de agosto ("com rotação") e de setembro ("sem rotação", `results/setembro/`) são, na prática, o **mesmo algoritmo**. A diferença entre eles é ruído do Recozimento Simulado (sem semente fixa). Eles **não servem** como comparação de rotação.
3. Foram criados dois códigos novos que diferem **apenas** em permitir ou não a rotação:
   - `src/strip_packing_rotacao_interna.py` (com rotação)
   - `src/strip_packing_sem_rotacao.py` (só 0°)
4. Três correções de geometria tornaram a rotação correta (seção 3).
5. Os leiautes foram validados com geometria exata, independente das matrizes NFP: zero sobreposições nas 30 execuções testadas (seção 4).
6. O experimento definitivo roda as duas versões em paralelo, com semente fixa, limite de 3600 s e validação automática: `src/rodar_experimento_paralelo.py`.
7. A análise estatística sai de `src/analise_de_resultados/analisa_experimento.py`.
8. Os resultados de agosto/setembro podem ser citados só como histórico, nunca na mesma tabela dos novos.

---

## 2. Cronologia da descoberta

| Passo | O que foi feito | Resultado |
|---|---|---|
| 1 | Revisão do código do Experimento Final | Laço de rotação por fora do laço de pontos |
| 2 | Contagem de rotações na solução final do código antigo (*blazewicz1*, *rco1*, *fu5*, semente 42) | 100% das peças em 0° |
| 3 | Rotação movida para dentro da varredura de pontos | Surgiram sobreposições |
| 4 | Comparação das matrizes NFP com geometria exata (SAT em convexos; fecho convexo nos não convexos) | Ponto de referência errado em 90°/270° |
| 5 | Correção do ponto de referência e da caixa envolvente | Divergências caíram a zero |
| 6 | Validação independente dos leiautes finais (amostragem de pontos nos polígonos) | 0 sobreposições em 30 execuções |
| 7 | Descoberta de pasta inválida (`w-item`) em `data/STRIP` | Filtro de instâncias adicionado |

---

## 3. Correções aplicadas ao código

### 3.1 Rotação dentro da varredura de pontos
Antes: `para cada peça → para cada rotação → para cada ponto`. A rotação 0° quase sempre achava um ponto livre, e as demais não eram testadas.
Agora: `para cada peça → para cada ponto (x crescente, depois y crescente) → para cada rotação`. No mesmo ponto, se mais de uma rotação couber, fica a que menos aumenta o comprimento L (empate: a de menor índice).

### 3.2 Ponto de referência do NFP
A matriz NFP(A, B) é indexada pela posição relativa de B em relação a A. O ponto de referência é a caixa envolvente de B **na rotação testada**. O código antigo usava os vértices sem rotação.

| Instância | Pontos testados | Divergências (regra antiga) | Divergências (regra nova) |
|---|---|---|---|
| fu5 | 1,7 milhão | 33.344 | 0 |
| poly1a | 9,4 milhões | 98.463 | 0 |

### 3.3 Caixa envolvente rotacionada
Erros de ponto flutuante no seno e cosseno (por exemplo 4,0000000001) faziam o `ceil` inflar a caixa em 1 unidade nas rotações 90°, 180° e 270°. A rotação passou a ser arredondada (`rotacionar_ponto`).

### 3.4 Outras mudanças
- Limite de tempo de 3600 s por execução (o RS devolve a melhor solução até então e registra `Limite Atingido`).
- Resultado informa se houve rotação, quantos itens e quais ângulos.
- Pastas sem peças (`w-item`) são ignoradas; antes o `sys.exit` do leitor derrubaria o lote inteiro.
- A contagem correta de instâncias do Experimento Final é **45**, e não 40 (inclui `three`, `threep2`, `threep2w9`, `threep3`, `threep3w9`).

---

## 4. Validação

**O que foi validado**
- Matrizes NFP contra geometria exata (*fu5*, *rco1*, *blazewicz1*, *poly1a*). Em peças não convexas, só foram verificadas as falsas colisões (o NFP ser conservador); colisões não detectadas em peças não convexas não foram verificadas por esse método.
- Leiautes finais com geometria exata (ponto-dentro-de-polígono por amostragem a cada 0,25 unidade), **sem usar NFP**. Resultado: 15 instâncias × 2 versões, 0 sobreposições e 0 peças fora da faixa.
  - Instâncias: *fu5*, *blazewicz1*, *blazewicz2*, *rco2*, *poly1a*, *poly1c*, *poly1e*, *shapes2*, *shapes4*, *shirts1-2*, *shirts2-4*, *dagli1*, *jakobs1*, *threep3*.

**Limites da validação**
- Foram usados parâmetros curtos do RS (α = 0,8; 60 iterações), pois o objetivo era testar a geometria.
- Não foram validadas as instâncias grandes (*shirts*, *shapes15*, *dighe1*, *han*).
- Sobreposições menores que 1/16 de unidade de área podem não ser detectadas.

**No experimento definitivo** a validação roda ao final de cada execução (`validado`, `fora_da_faixa`, `pares_sobrepostos`, `fallbacks` no `resultados.csv`). Uma execução só conta como válida se todas as peças foram empacotadas, sem sobreposição, sem peça fora da faixa e sem uso do mecanismo de *fallback*.

---

## 5. Resultados preliminares (ilustrativos)

Semente 42, uma execução, parâmetros T₀ = 100, α = 0,9, 300 iterações. **Não são conclusivos.**

| Instância | L antigo (sem rotação efetiva) | L novo (com rotação) | Itens rotacionados | Tempo antigo → novo |
|---|---|---|---|---|
| blazewicz1 | 8 | 8 | 1/7 | 5 s → 6 s |
| rco1 | 8 | 8 | 2/7 | 5 s → 7 s |
| fu5 | 18 | 17 | 3/5 | 7 s → 24 s |
| blasz2 | 22 | 20 | 5/16 | 91 s → 214 s |
| poly1a | 16 | 15 | 13/15 | 113 s → 235 s |

Fator de tempo medido: de 1,2× a 3,4×, crescendo com o número de rotações permitidas.

---

## 6. Protocolo do experimento definitivo

### 6.1 Princípios (o que torna a comparação defensável)
1. As duas versões diferem **apenas** na permissão de rotação (mesmo BL, mesmo RS, mesmos parâmetros, mesmo limite).
2. Mesma máquina, mesmo número de processos, mesmas sementes. As duas versões da mesma instância ficam adjacentes na fila.
3. Semente fixa e registrada por execução.
4. Instâncias cortadas pelo limite de tempo são marcadas e analisadas à parte.
5. O subconjunto da Rodada B foi **definido antes de ver os resultados novos** (seção 6.3).
6. O tempo de execução só é comparado na Rodada C (um processo por vez).

### 6.2 Parâmetros (iguais aos do Experimento Final)
T₀ = 100, α = 0,9, 300 iterações por temperatura, parada com T < 0,1, solução inicial ordenada por área decrescente, vizinhança por troca (*swap*), limite de 3600 s.

### 6.3 Rodadas

| Rodada | Objetivo | Instâncias | Sementes | Processos | Estimativa* |
|---|---|---|---|---|---|
| **A** | Tabela completa | 45 | 42 | 3 | 8 a 10 h |
| **B** | Análise estatística | 14 do subconjunto abaixo | 42 a 51 (10) | 3 | 9 a 10 h (5 sementes: ~5 h) |
| **C** | Tempo | *fu5*, *fu8*, *rco2*, *poly1a*, *dagli1*, *shapes4*, *blazewicz2*, *rco3* | 42 | 1 | cerca de 40 min |

\* Estimativas a partir dos tempos do Experimento Final (computador de casa), aplicando 2,5× na versão com rotação e 15% de acréscimo por disputa de recursos. São aproximadas.

**Subconjunto da Rodada B** (estratificado por família e tamanho, definido a priori, sem as instâncias que batem o teto de 3600 s):
`blazewicz2, blazewicz3, dagli1, fu, fu8, jakobs1, poly1a, poly1c, rco2, rco3, shapes4, shapes5, shirts2-4, shirts3-6`

### 6.4 Comandos (a partir da raiz do repositório)

```bash
# Rodada A
python src/rodar_experimento_paralelo.py --processos 3 --sementes 42 \
    --saida results/outubro/RodadaA

# Rodada B
python src/rodar_experimento_paralelo.py --processos 3 --sementes 42-51 \
    --instancias blazewicz2,blazewicz3,dagli1,fu,fu8,jakobs1,poly1a,poly1c,rco2,rco3,shapes4,shapes5,shirts2-4,shirts3-6 \
    --saida results/outubro/RodadaB

# Rodada C (um processo por vez)
python src/rodar_experimento_paralelo.py --processos 1 --sementes 42 \
    --instancias fu5,fu8,rco2,poly1a,dagli1,shapes4,blazewicz2,rco3 \
    --saida results/outubro/RodadaC_tempo

# Análise de qualquer rodada
python src/analise_de_resultados/analisa_experimento.py results/outubro/RodadaA
```

- O CSV é gravado a cada execução concluída. Se o computador desligar, rode o **mesmo comando** de novo: as execuções já feitas são puladas.
- `ambiente.json` registra commit, Python, sistema, processador, número de processos e parâmetros.
- As imagens dos leiautes ficam em `<saida>/imagens/<versao>/`. Use `--sem-imagens` para economizar espaço.

### 6.5 Hardware (computador de casa)
Ryzen 5 3400G (4 núcleos físicos, 8 threads), 16 GB DDR4-3200, RX 570 (não usada: o código roda só em CPU). Usar **3 processos** (núcleos físicos menos 1). Acima disso, dois processos dividem o mesmo núcleo físico e os tempos ficam distorcidos.

### 6.6 Checklist para o outro computador
1. `git fetch && git checkout feature/rotacao-dentro-do-bl`
2. `pip install matplotlib numpy scipy` (scipy é opcional, para o teste de Wilcoxon)
3. Conferir que `data/STRIP` tem as 45 instâncias (mais `w-item`, ignorada).
4. Teste rápido: `python src/rodar_experimento_paralelo.py --instancias fu5,blazewicz1 --sementes 42 --limite 20 --saida results/outubro/teste_rapido`
5. Desativar suspensão do sistema, ligar na tomada e fechar programas pesados.
6. Rodar em `tmux`, `screen` ou `nohup`, para não depender do terminal aberto.
7. Monitorar a memória nas instâncias *shirts* e *shapes15*. Se o sistema usar *swap*, reduza `--processos`.

---

## 6.7 Plano reduzido (decidido em 14/10/2026, para entregar à orientadora no mesmo dia)

O tempo disponível não comportava a Rodada A completa (cerca de 7 h com 3 processos). Decisão: rodar primeiro uma **Rodada A reduzida**, com 1 semente, nas instâncias cujo tempo no Experimento Final foi de **até 400 s** (critério de tamanho, fixado antes de ver os resultados novos).

| Plano (1 semente, 3 processos) | Instâncias | Relógio estimado |
|---|---|---|
| Completo, limite 3600 s | 45 | cerca de 7 h |
| Limite 600 s | 45 | cerca de 2,6 h |
| **Reduzido: tempo antigo ≤ 400 s, limite 3600 s (escolhido)** | **33** | **cerca de 1,2 h** |

**Instâncias da Rodada A reduzida (33):**
`blasz2,blazewicz1,blazewicz2,blazewicz3,blazewicz4,dagli1,fu,fu10,fu5,fu6,fu7,fu8,fu9,jakobs1,poly1a,poly1b,poly1c,poly1d,poly1e,rco1,rco2,rco3,rco4,shapes2,shapes4,shapes5,shirts1-2,shirts2-4,three,threep2,threep2w9,threep3,threep3w9`

```bash
python src/rodar_experimento_paralelo.py --processos 3 --sementes 42 \
    --instancias blasz2,blazewicz1,blazewicz2,blazewicz3,blazewicz4,dagli1,fu,fu10,fu5,fu6,fu7,fu8,fu9,jakobs1,poly1a,poly1b,poly1c,poly1d,poly1e,rco1,rco2,rco3,rco4,shapes2,shapes4,shapes5,shirts1-2,shirts2-4,three,threep2,threep2w9,threep3,threep3w9 \
    --saida results/outubro/RodadaA_reduzida
python src/analise_de_resultados/analisa_experimento.py results/outubro/RodadaA_reduzida
```

**Instâncias deixadas para depois (12), das menos para as mais longas:**
`blazewicz5,rco5,shirts3-6,dighe2,han,shapes7,shirts4-8,shapes9,dighe1,shirts5-10,shapes15,shirts`
(rodar com o mesmo comando e `--saida results/outubro/RodadaA_grandes`; devem bater o limite de 3600 s e ser analisadas à parte).

**No artigo:** declarar o recorte por tamanho como limitação. Os resultados reduzidos não substituem a Rodada B (10 sementes), necessária para a análise estatística.

---

## 6.8 Onde parei (retomar daqui)

1. Código com e sem rotação, executor paralelo, análise e documentação estão **commitados** na branch `feature/rotacao-dentro-do-bl`.
2. **Ainda não foi rodado nenhum experimento definitivo.** Só testes de fumaça (16 tarefas em 4 instâncias, todas validadas).
3. Próximo passo: rodar a Rodada A reduzida (seção 6.7), conferir a seção "Auditoria" do `analise.md` (execuções não validadas ou cortadas) e depois decidir as rodadas B e C.
4. Antes de rodar no outro computador: `git fetch && git checkout feature/rotacao-dentro-do-bl`, e a branch precisa ter sido enviada com `git push -u origin feature/rotacao-dentro-do-bl` neste computador.

---

## 7. Como relatar no artigo

- Descrever o algoritmo: RS sobre permutações, decodificador Bottom-Left discreto com teste de colisão por matriz de *no-fit*, rotação testada em cada ponto.
- Indicar que as **duas versões foram executadas nas mesmas condições**, com a mesma semente, e informar o hardware, o número de processos e o limite de 3600 s.
- Reportar L médio e desvio entre sementes (Rodada B), vitórias/empates/derrotas e o teste de Wilcoxon pareado.
- Listar as instâncias cortadas pelo limite e analisá-las à parte.
- Reportar tempos apenas da Rodada C.
- Se possível, comparar L com os melhores valores da literatura para essas instâncias (gap), o que dá contexto ao resultado.
- Citar os resultados de agosto/setembro apenas como histórico do desenvolvimento, dizendo que a rotação não era efetivamente aplicada.

---

## 8. Pendências e ideias

- Rodar as Rodadas A, B e C e analisar.
- Completar a literatura de referência (melhores valores conhecidos de L por instância).
- Ainda não incorporados à versão para irregulares: operadores de inversão e inserção, e busca local (*Hill Climbing*), que existem na Fase 2.
- Avaliar escolher a rotação como parte da solução do RS, em vez de decidir no decodificador.
- Aceleração do decodificador **sem mudar o resultado** (verificável pela mesma semente), para ampliar o número de sementes.
- A taxa de ocupação usa L inteiro (caixa envolvente na grade), podendo ser subestimada.

---

## 9. Arquivos importantes

| Arquivo | Papel |
|---|---|
| `src/strip_packing_rotacao_interna.py` | Versão com rotação (uso sequencial, uma instância por vez via `main`) |
| `src/strip_packing_sem_rotacao.py` | Mesma versão restrita a 0° |
| `src/rodar_experimento_paralelo.py` | Executor paralelo das duas versões com validação |
| `src/analise_de_resultados/analisa_experimento.py` | Tabelas, vitórias/empates/derrotas e Wilcoxon |
| `src/strip_packing_discretização_irregulares.py` | Código do Experimento Final (histórico; sem rotação efetiva) |
| `src/strip_packing_no_rotation.py` | Versão sem rotação de setembro (histórico) |
| `results/agosto/ExperimentoFinal/`, `results/setembro/` | Resultados históricos (45 instâncias, sem limite de tempo, sem semente fixa) |
| `docs/evolucao-do-codigo.md` | Texto da evolução do código (para o artigo) |
| `docs/guia-codigos-src.md` | Descrição de cada arquivo de `src` |

---

## 10. Sobre o histórico da conversa com o Claude

Esta documentação existe para que o trabalho não dependa da conversa. O histórico bruto da sessão fica **apenas localmente**, no computador em que foi feita:

`~/.claude/projects/-home-ubiratanfilho-Documentos-Projetos-ic-otimizacao/71c7ddfa-a0a6-4a15-8423-aa606cc6ab30.jsonl`

Não está no git nem é sincronizado entre computadores. Em uma nova sessão, peça ao Claude para **ler `docs/protocolo-experimental.md`** antes de continuar.
