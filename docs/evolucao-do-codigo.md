# Evolução do código desenvolvido na Iniciação Científica

*Texto de apoio para o artigo. Linha do tempo reconstruída a partir do histórico de commits (nov/2025 a set/2026) e dos arquivos das pastas `src/` e `results/`.*

---

## 1. Visão geral

O desenvolvimento computacional deste projeto seguiu um caminho incremental. Começou com problemas mais simples e bem conhecidos e foi aproximando-se, passo a passo, do problema-alvo da pesquisa: o **corte de itens irregulares em faixa bidimensional** (*irregular strip packing*), resolvido por uma heurística baseada em **Recozimento Simulado** (RS, *Simulated Annealing*). Cada etapa reaproveitou a anterior e incluiu uma única dificuldade nova. Assim, os componentes de cada versão puderam ser validados isoladamente antes de serem combinados.

As fases podem ser resumidas assim:

| Fase | Período | Problema tratado | Método |
|---|---|---|---|
| 0 | nov/2025 | Funções contínuas de teste | RS genérico |
| 1 | nov/2025 – jan/2026 | Empacotamento ortogonal 2D e mochila 2D | Programação Linear Inteira (PuLP) |
| 2 | jan – abr/2026 | Mochila 2D com retângulos | RS + heurísticas construtivas (BL, zig-zag) |
| 3 | mai – jun/2026 | *Strip packing* com retângulos | RS + BL, zig-zag vertical e discretização |
| 4 | jul – set/2026 | *Strip packing* com itens irregulares | RS + BL discreto + matrizes de *no-fit* |

Ao longo de todas as fases manteve-se a mesma ideia central. Uma solução é representada por uma **sequência (permutação) dos itens**, e uma **heurística construtiva** transforma essa sequência em um leiaute físico. O RS não manipula coordenadas: ele explora o espaço das ordens de empacotamento, e o decodificador construtivo se encarrega de posicionar as peças.

---

## 2. Fase 0 — Estudo da metaheurística

O primeiro código (`recozimento simulado.py`) foi uma implementação didática do RS para minimizar uma função de uma variável, f(x) = x² + 10·sen(x). Logo depois veio uma segunda versão (`RS.py`), aplicada a uma função do tipo Rastrigin, x² − 10·cos(2πx). Essas funções têm vários mínimos locais e por isso servem para observar o mecanismo fundamental do RS: aceitar soluções piores com probabilidade exp(Δ/T), o que permite escapar de ótimos locais enquanto a temperatura T é alta.

Nessa fase foram fixados os elementos que se repetem em todos os códigos posteriores:

- temperatura inicial T₀ e temperatura final T_f;
- resfriamento geométrico, T ← α·T;
- número fixo de iterações por nível de temperatura;
- armazenamento da melhor solução já encontrada, independentemente da solução corrente.

No mesmo período foram feitos testes isolados da heurística **Bottom-Left (BL)** com retângulos (`BLArray.py`) e da geração de pontos em **zig-zag** (`HZZ.py`), duas ideias que mais tarde se tornaram os decodificadores do RS.

---

## 3. Fase 1 — Modelos exatos de Programação Linear Inteira

Antes de construir heurísticas, foram implementados modelos exatos com a biblioteca PuLP. O objetivo era ter uma referência de qualidade de solução e entender a estrutura matemática do problema.

1. **`modelo PLI.py` e `pli 2.py`**: modelo de viabilidade para o empacotamento ortogonal bidimensional (2OPP), baseado na formulação de Junqueira et al. As variáveis binárias x_ipq indicam se o item *i* ocupa o ponto (p, q) de uma grade discreta do recipiente. O modelo apenas responde se todos os itens cabem no recipiente.

2. **`pli2 (mochila) 2.0.py`**: o modelo foi transformado em um **problema da mochila bidimensional**. Passou a maximizar o valor dos itens empacotados, usando a área quando o valor não é informado, e cada item pode ser escolhido no máximo uma vez. Também ganhou execução em lote sobre uma pasta de instâncias, com limite de 600 s por instância.

3. **`pli2 3.0 .py`**: a formulação por grade foi substituída por uma **formulação por coordenadas**, com variáveis contínuas (x_i, y_i) e variáveis binárias de posição relativa (esquerda, direita, abaixo, acima) para cada par de itens, ligadas por restrições do tipo *Big-M*. A formulação por grade cresce com o número de pontos do recipiente, O(L·W). A formulação por coordenadas cresce com o número de pares de itens, O(N²). Por isso ela foi bem mais rápida nas instâncias testadas (commit "PLI agora resolve por coordenadas, algoritmo mais rápido", jan/2026).

Essa fase mostrou na prática a limitação dos métodos exatos. Mesmo para retângulos, o tempo de solução cresce rapidamente com o tamanho da instância. Isso justifica o uso de heurísticas para o problema com itens irregulares, que é ainda mais difícil.

---

## 4. Fase 2 — Recozimento Simulado com heurísticas construtivas (mochila 2D)

Nessa fase o RS foi aplicado a um problema de empacotamento pela primeira vez. O problema escolhido foi a mochila bidimensional com retângulos: o recipiente tem tamanho fixo W×H e deseja-se maximizar o valor (ou a área) empacotado.

### 4.1 Primeira versão: RS + BL (`RS+BL_v1.py`)

A solução é uma permutação dos itens. O decodificador BL posiciona cada item, na ordem dada, no ponto candidato viável mais abaixo e mais à esquerda. Os pontos candidatos são gerados nos cantos dos itens já posicionados: (x + w, y) e (x, y + h). O RS usava um único operador de vizinhança (troca de dois itens, *swap*), partia de uma permutação aleatória e avaliava a solução pela área total empacotada.

### 4.2 Testes de parâmetros e visualização

Em fevereiro/2026 foram feitas baterias de teste variando o fator de resfriamento α (0,50; 0,80; 0,90; 0,95; 0,99 com T₀ = 1000). Os resultados foram consolidados por um script de análise com pandas e seaborn (`analise_de_resultados/script_analise.py`). Também foi criada uma função que gera a **imagem do leiaute** de cada solução, recurso usado daí em diante para validar visualmente os resultados.

### 4.3 Vizinhança com três operadores (`RS+BL_v2-3_operadores.py`)

A segunda versão ampliou a vizinhança do RS com três operadores sobre a permutação, escolhidos por roleta:

- **troca (*swap*)**, 40%: troca a posição de dois itens;
- **inversão (*2-opt*)**, 30%: inverte um trecho da sequência;
- **inserção (*shift*)**, 30%: retira um item e o reinsere em outra posição.

A solução inicial deixou de ser aleatória e passou a ser a ordenação por área decrescente, uma regra clássica da literatura de empacotamento. A função de avaliação ganhou um termo de desempate, de modo que, entre soluções de mesmo valor, é preferida a mais compacta (valor − 0,0001 × dispersão).

### 4.4 Rotação e decodificador alternativo (zig-zag)

A partir dessa base foram criadas variantes para comparar decodificadores:

- **BL com rotação de 90°**: o decodificador testa também a orientação girada de cada item;
- **zig-zag horizontal (HZZ)**: os pontos candidatos são percorridos linha a linha, alternando o sentido do eixo x conforme a paridade da linha;
- **HZZ com rotação**.

### 4.5 Uso do valor dos itens e correções na métrica

Em março/2026 o código passou a considerar o **valor** de cada item, e não apenas a área. Isso revelou um erro de métrica: o campo apresentado como "área máxima" podia ser, na verdade, a soma dos valores. As versões corrigidas (pasta `semana 06-10 de abril/`) separam três grandezas:

- o **tipo de objetivo** ("Área" quando todos os valores são nulos, "Valor" caso contrário);
- o **valor objetivo** alcançado;
- a **ocupação física**, área empacotada ÷ área do recipiente (%).

Na mesma época foi feito um protótipo de interface em Streamlit (`app.py`) para executar o RS+BL com rotação em lote, com upload de instâncias.

### 4.6 Hibridização com busca local (Hill Climbing)

Em abril/2026 o RS foi hibridizado com uma etapa de **busca local do tipo Hill Climbing** (pasta `semana 20-24 abril/`). Ao fim de cada nível de temperatura são feitas 20 trocas adicionais, aceitas apenas se melhorarem a solução, antes de reduzir T. Essa intensificação explora melhor a vizinhança da solução corrente sem perder a capacidade de diversificação do RS. As quatro combinações (BL/HZZ, com e sem rotação, com e sem HC) foram comparadas em uma bateria de testes no mesmo conjunto de instâncias (`results/testes abril/`).

---

## 5. Fase 3 — *Strip packing* com retângulos

Em maio/2026 o problema passou a ser o da pesquisa: o **empacotamento em faixa** (*strip packing*). A largura W da faixa é fixa, o comprimento L é livre e **todos os itens precisam ser empacotados**; o objetivo é **minimizar L**. No código, o RS maximiza −L, o que mantém a lógica de aceitação das fases anteriores.

Três decodificadores foram testados:

1. **`strip_packing.py`**: BL com pontos candidatos nos cantos dos itens, ordenados primeiro por x e depois por y, com o operador de troca no RS. Também passou a registrar a taxa de ocupação e a quantidade de itens empacotados em relação ao total.
2. **`strip_packing VZZ.py`**: zig-zag vertical. Preenche uma coluna no eixo y e abre uma nova coluna quando o próximo item não cabe. É construtivo simples, sem teste de colisão geral.
3. **`strip_packing_discretização.py`**: BL sobre uma **grade discreta de pontos normais**, isto é, as combinações inteiras das dimensões dos itens que não ultrapassam o limite do recipiente (teoria de *normal patterns*), em vez dos pontos de canto.

A discretização foi a **ponte conceitual para os itens irregulares**: com polígonos não existem "cantos" naturais para gerar candidatos, e trabalhar sobre uma grade de pontos é a forma mais direta de tratar geometrias arbitrárias.

---

## 6. Fase 4 — *Strip packing* com itens irregulares

### 6.1 Nova representação dos dados

Em julho/2026 foi implementado o algoritmo para itens irregulares (`strip_packing_discretização_irregulares.py`). A primeira mudança foi no formato das instâncias. Cada instância passou a ser uma pasta com:

- `general_data.in`: escala, número de peças, **demanda** de cada peça e **rotações permitidas** (ex.: 0°, 90°, 180°, 270°);
- `items/`: vértices de cada polígono;
- `rfr/`: representação discreta (matriz 0/1) de cada peça em cada rotação;
- `bins/`: dimensões da faixa;
- `nfr/`: matrizes de *no-fit* discretas para cada par (peça A, rotação A, peça B, rotação B).

A leitura foi escrita como um gerador de *tokens* que ignora comentários, e cada peça é replicada de acordo com sua demanda antes da otimização.

### 6.2 Teste de colisão por matriz de *no-fit*

A principal mudança algorítmica foi no teste de sobreposição. Com retângulos bastava comparar intervalos. Com polígonos, a colisão é verificada por **consulta a uma matriz de *no-fit* pré-calculada**. Para posicionar a peça B no ponto (c_x, c_y), o código calcula, para cada peça A já posicionada, a posição relativa de B em relação a A. Em seguida consulta a célula correspondente da matriz NFP(A, B). Um valor positivo indica sobreposição. Como as matrizes vêm prontas, cada teste de colisão é uma consulta O(1), e todo o custo geométrico fica no pré-processamento.

O decodificador BL percorre a grade em ordem (x crescente e, para cada x, y crescente). Na versão de agosto, o laço de rotação ficava por fora do laço de pontos: para cada peça, as rotações eram testadas em ordem e a **primeira posição viável** era aceita (a consequência disso e a correção estão na seção 6.6). Se nenhuma posição for encontrada, há um mecanismo de segurança (*fallback*) que coloca a peça no fim da faixa já ocupada, garantindo que a solução seja sempre completa.

### 6.3 Correções que tornaram o algoritmo correto

O código só se tornou confiável depois de uma sequência de correções em agosto/2026, documentadas nos commits:

1. **Leitura das pastas `nfr` e `rfr`** (jul/2026): os nomes dos arquivos dependem do ângulo de rotação (ex.: `1_0_2_90.in`), e a leitura precisou ser ajustada para isso.
2. **Itens dentro do recipiente** (ago/2026): a caixa envolvente (*bounding box*) de cada peça era calculada a partir do tamanho da matriz discreta, o que gerava dimensões inconsistentes e peças fora da faixa. Ela passou a ser calculada **a partir dos vértices rotacionados**, arredondando para cima (`ceil`) para cobrir a grade. A área de cada peça passou a ser a área geométrica exata, calculada pela **fórmula de Shoelace** (fórmula do laço de Gauss), e não pela contagem de células.
3. **Sobreposição** (ago/2026): o ponto de referência da matriz NFP era tomado como o centro da matriz. Foi corrigido para ser derivado das dimensões da peça B. Além disso, o limite estimado do comprimento da faixa passou a usar a maior dimensão entre todas as rotações. Depois disso **todas as peças passaram a ser empacotadas sem sobreposição**.
4. **Consumo de memória** (ago/2026): a primeira versão criava explicitamente a lista de todos os pontos candidatos (c_x, c_y) da grade a cada chamada do decodificador, ou seja, milhares de chamadas por execução do RS. Nas instâncias maiores isso esgotava a memória. A lista foi substituída por laços sobre `range`, que geram os pontos sob demanda. Também foi adotado um *backend* não interativo do matplotlib para a geração das imagens.

### 6.4 Configuração final do RS

Na versão final o RS usa a ordenação por **área decrescente** como solução inicial, o operador de **troca** como vizinhança e os parâmetros T₀ = 100, α = 0,9, 300 iterações por nível de temperatura e parada quando T < 0,1. Isso equivale a cerca de 66 níveis de temperatura e aproximadamente 20 mil decodificações por execução.

### 6.5 Experimentos

Foram feitos três tipos de experimento com essa versão:

- **Experimento final** (`results/agosto/ExperimentoFinal/`): 45 instâncias de referência da literatura (famílias *blasz*, *blazewicz*, *dagli*, *dighe*, *fu*, *han*, *jakobs*, *poly*, *rco*, *shapes*, *shirts* e *three*). **Em todas as 45, 100% das peças foram empacotadas**, com taxas de ocupação entre cerca de 47% e 100%; a maioria ficou entre 60% e 85%. O tempo vai de poucos segundos nas instâncias pequenas a cerca de 5 horas na maior (*shirts*, 99 peças). **Atenção:** apesar do nome "com rotação", nenhuma peça foi rotacionada nesse experimento (ver 6.6).
- **Teste de robustez e de plataforma** (`strip_packing_teste_OS.py`): a mesma versão foi instrumentada para rodar com **30 sementes aleatórias** por instância. Ela conta o número de avaliações de pontos do BL e de consultas às matrizes NFP e reporta média e desvio-padrão de L e do tempo. Foi executada em Linux (Mint) e Windows. Nas execuções registradas, L foi o mesmo em todas as sementes (ex.: L = 24 em *fu8*, L = 22 em *blasz2*), o que indica um comportamento estável da heurística nessas instâncias.
- **Versão sem rotação** (`strip_packing_no_rotation.py`, set/2026): cada peça tem uma única orientação e, portanto, uma única matriz discreta e uma única matriz NFP por par de peças. Rodada nas mesmas instâncias, ela foi pensada para medir o efeito da rotação. Como se descobriu depois (seção 6.6), a versão "com rotação" também nunca rotacionava, então **as duas rodadas eram, na prática, o mesmo algoritmo**. As diferenças de L entre elas (a versão "com rotação" melhor em 6 instâncias e a "sem rotação" melhor em 5) vêm da aleatoriedade do Recozimento Simulado, sem semente fixa, e não da rotação. Esses resultados **não devem ser usados** como comparação de rotação no artigo.

### 6.6 Revisão: a rotação nunca era usada (out/2026)

Ao revisar o código do Experimento Final, notou-se que o laço de rotação ficava **por fora** do laço de varredura de pontos. Como a rotação 0° sempre encontrava algum ponto livre ao longo da faixa, as demais rotações nunca eram testadas. Isso foi confirmado contando a rotação de cada peça na solução final em três instâncias (*blazewicz1*, *rco1*, *fu5*): 100% das peças em 0°. Nas demais instâncias a conclusão decorre da estrutura do código.

A correção está em `src/strip_packing_rotacao_interna.py` (branch `feature/rotacao-dentro-do-bl`):

1. **Rotação dentro da varredura.** Em cada ponto (c_x, c_y), na ordem x crescente e depois y crescente, todas as rotações permitidas são testadas. Se mais de uma couber no ponto, fica a que menos aumenta o comprimento L.
2. **Ponto de referência do NFP.** A referência era calculada com os vértices da peça sem rotação. Agora usa a caixa envolvente da peça já rotacionada. Sem isso, rotações de 90° e 270° geravam sobreposição. Conferido contra geometria exata: 33 mil divergências em *fu5* e 98 mil em *poly1a* com a regra antiga, e zero com a nova.
3. **Caixa envolvente rotacionada.** Erros de ponto flutuante no seno/cosseno faziam o `ceil` inflar a caixa em 1 unidade (por exemplo 5×6 em vez de 4×5). A rotação passou a ser arredondada.

Uma segunda versão, `src/strip_packing_sem_rotacao.py`, é o mesmo código restrito a 0°, para comparação justa.

**Validação.** Os leiautes finais foram conferidos com geometria exata dos polígonos (ponto-dentro-de-polígono por amostragem a cada 0,25 unidade), sem usar as matrizes NFP. Em 15 instâncias × 2 versões, incluindo peças não convexas, houve **zero sobreposições e zero peças fora da faixa**. No experimento definitivo essa verificação é feita automaticamente ao final de cada execução.

**Resultados preliminares** (semente 42, uma execução; ilustrativos, não conclusivos):

| Instância | L sem rotação | L com rotação | Itens rotacionados |
|---|---|---|---|
| blazewicz1 | 8 | 8 | 1/7 |
| rco1 | 8 | 8 | 2/7 |
| fu5 | 18 | 17 | 3/5 |
| blasz2 | 22 | 20 | 5/16 |
| poly1a | 16 | 15 | 13/15 |

O custo é maior: de 1,2× a 3,4× o tempo da versão anterior, e cresce com o número de rotações permitidas.

---

## 7. Síntese da evolução

Do ponto de vista metodológico, a evolução do código pode ser resumida em quatro movimentos:

1. **Do exato ao heurístico.** Os modelos de PLI serviram de referência e mostraram, na prática, o crescimento do tempo de solução com o tamanho da instância. Isso motivou o uso do RS.
2. **Do problema simples ao problema-alvo.** Mochila 2D → *strip packing* com retângulos → *strip packing* com irregulares. A cada passo, apenas um elemento novo foi introduzido (objetivo, geometria, rotação).
3. **Separação entre busca e decodificação.** O RS sempre operou sobre permutações, enquanto os decodificadores (BL, zig-zag, BL discreto com NFP) foram trocados e comparados sem alterar a metaheurística.
4. **Da geometria explícita à geometria pré-processada.** Com retângulos, a colisão era calculada diretamente. Com irregulares, ela passou a ser uma consulta a matrizes de *no-fit* discretas, o que torna o decodificador independente da complexidade das formas.

Cada fase também melhorou a infraestrutura experimental: execução em lote, pastas de resultados com data e hora, geração automática de imagens dos leiautes, registro de ocupação, de itens empacotados e de tempo, e, por fim, repetição com várias sementes e coleta de métricas de esforço computacional.

### Limitações conhecidas da versão atual

- A grade de discretização tem resolução unitária, então a precisão do leiaute depende da escala da instância.
- O decodificador testa todos os pontos da grade para cada peça, o que explica o tempo elevado nas instâncias grandes (*shirts*, *shapes15*, *dighe1*).
- O RS final usa apenas o operador de troca. Os operadores de inversão e inserção e a busca local (Hill Climbing) da Fase 2 ainda não foram incorporados à versão para irregulares.
- A rotação só é aplicada nos ângulos para os quais a instância fornece matrizes RFR/NFR (0°, 90°, 180°, 270° ou um subconjunto). Várias instâncias (*shapes*, *blazewicz*, *shirts*) só permitem 0° e 180°, ou apenas 0°.
- O critério de parada por tempo (3600 s) torna o resultado das instâncias grandes dependente da máquina.
- A taxa de ocupação é calculada sobre W × L com L inteiro (limite da caixa envolvente na grade). Por isso ela pode ser ligeiramente subestimada em relação a medidas que usam o comprimento real do polígono mais à direita.
