# Guia dos códigos da pasta `src`

Resumo do que cada arquivo `.py` faz e de onde ele se encaixa na evolução da IC.

## Linha do tempo (visão geral)

```
Etapa 0  Estudos soltos        HZZ.py, recozimento simulado.py, RS.py, BLArray.py
Etapa 1  Modelos PLI (exato)   modelo PLI.py -> pli 2.py -> pli2 (mochila) 2.0.py -> pli2 3.0 .py
Etapa 2  RS + BL (mochila 2D)  RS+BL_v1.py -> RS+BL_v2-3_operadores.py -> RS+BL+Rotacao_...py
                               (variante com zig-zag: RS+HZZ_...py e RS+HZZ+Rotacao_...py)
Etapa 3  Strip Packing         strip_packing.py -> strip_packing VZZ.py -> strip_packing_discretização.py
Etapa 4  Itens irregulares     strip_packing_discretização_irregulares.py
                               -> strip_packing_no_rotation.py / strip_packing_teste_OS.py
```

Convenções que aparecem em quase todos os arquivos:
- **BL** = Bottom-Left (heurística construtiva de posicionamento).
- **RS / SA** = Recozimento Simulado (Simulated Annealing).
- **HZZ / VZZ** = Zig-Zag horizontal / vertical (variação da ordem de varredura dos pontos candidatos).
- **NFP/NFR** = No-Fit Polygon (matriz de colisão entre duas peças), **RFR** = matriz discreta (raster) de uma peça.
- Quando o score é negativo (`-L`), o RS está *maximizando* `-L`, ou seja, minimizando o comprimento da faixa.

---

## Etapa 0 — Estudos e testes isolados

| Arquivo | O que faz |
|---|---|
| `HZZ.py` | Teste de 11 linhas: gera a lista de pontos de uma grade `width x height` percorrida em zig-zag (linhas ímpares invertidas). Origem da ideia usada em `RS+HZZ_*`. |
| `recozimento simulado.py` | Implementação "de livro" do Recozimento Simulado genérico (`F`, `gerar_vizinho`, `T0`, `Tf`, `alpha`, `N_iter`). Exemplo: minimizar `x² + 10·sen(x)`. |
| `RS.py` | Segunda versão do RS genérico, guardando `f(x_otimo)` em variável (evita recalcular). Exemplo com função tipo Rastrigin (`x² - 10·cos(2πx)`). |
| `BLArray.py` | Primeiro teste da heurística Bottom-Left com classe `Item`, `check_collision` e ordenação por área decrescente; plota o resultado. Sem RS. |

## Etapa 1 — Modelos de Programação Linear Inteira (PuLP)

Todos usam retângulos e leem instâncias `.txt` (n itens, dimensões do bin, `l c v` por item).

| Arquivo | O que faz |
|---|---|
| `modelo PLI.py` | Primeiro modelo PLI: **2OPP** (empacotamento ortogonal 2D, viabilidade) de Junqueira et al. com variáveis `X_ipq` (item `i` no ponto `(p,q)`). Leitura da instância solta no topo + função `solve_2opp`. |
| `pli 2.py` | Mesmo modelo, organizado: `carregar_instancia` + `solve_2opp_feasibility`. Verifica se **todos** os itens cabem no bin (função objetivo dummy). É o citado no README para Google Colab. |
| `pli2 (mochila) 2.0.py` | Evolui para **Problema da Mochila 2D**: maximiza valor dos itens (valor 0 → usa área), `<= 1` por item, restrições de cobertura de grade + cortes. Roda em lote sobre uma pasta de instâncias com limite de 600 s e grava o resultado em `.txt`. |
| `pli2 3.0 .py` | Mesma mochila 2D, mas com **formulação por coordenadas (Big-M)**: variáveis `x_i, y_i`, `u_i` e binárias left/right/below/above por par de itens. Cresce com O(N²) em vez de O(L·C) da grade. Mesmo harness de lote do 2.0. |

## Etapa 2 — Heurística RS + BL para a mochila 2D (retângulos, bin fixo)

Todos têm a mesma estrutura: `Item`, `Instance`, `plot_solution`, `preparar_pasta`, posicionamento, `recozimento_simulado`, `load_instance`, `main`. O objetivo é maximizar valor/área dentro de um bin W×H. A solução é uma **permutação** dos itens; o BL decodifica a permutação em um layout.

| Arquivo | O que faz |
|---|---|
| `RS+BL_v1.py` | Versão base: BL com pontos candidatos `(x+w, y)` e `(x, y+h)`, RS com **um operador** (swap), partida aleatória, avalia por área total empacotada. |
| `RS+BL_v2-3_operadores.py` | Adiciona valor `v` do item (0 → área), score = valor − dispersão·0,0001 (desempate por compactação), partida ordenada por área e **3 operadores** do RS por roleta: swap (40%), inversão/2-opt (30%) e inserção/shift (30%). |
| `RS+BL+Rotacao_v2-3_operadores.py` | Igual ao anterior, mas o BL testa também a orientação rotacionada 90° do item (`rotated` registrado no layout). |
| `RS+HZZ_v2-3_operadores.py` | Igual ao `v2-3`, trocando o BL por **zig-zag horizontal** (`horizontal_zig_zag_placement`): candidatos ordenados por linha, alternando o sentido de X conforme a paridade de Y. |
| `RS+HZZ+Rotacao_v2-3_operadores.py` | Zig-zag horizontal + rotação de 90°. |

> Obs.: nos arquivos `RS+HZZ_*` o comentário de seção ainda diz "Bottom-Left (BL)" — é só herança de cópia.

## Etapa 3 — Strip Packing com retângulos (minimizar L)

Muda o problema: a largura `W` é fixa e o comprimento `L` da faixa é minimizado; **todos** os itens precisam ser alocados. Score = `-L`.

| Arquivo | O que faz |
|---|---|
| `strip_packing.py` | RS (swap) + BL com candidatos `(x+l, y)` e `(x, y+w)` ordenados por X depois Y. Primeira versão do strip packing; lê instâncias `.txt` em lote. |
| `strip_packing VZZ.py` | Troca o BL por **zig-zag vertical**: preenche colunas no eixo Y e, quando não cabe, abre outra coluna. Não faz busca de pontos, é construtivo simples (não testa colisão). |
| `strip_packing_discretização.py` | Volta ao BL, mas com **grade discreta de pontos normais** (`gerar_pontos_normais`: combinações inteiras das dimensões dos itens) em vez de pontos candidatos pelas bordas. Ponte para a ideia de discretização usada nos irregulares. |

## Etapa 4 — Strip Packing com itens irregulares (grade + NFP)

Passam a ler instâncias modulares (`general_data.in`, pastas `items`, `rfr`, `bins`, `nfr`), com demanda por item, rotações permitidas e matrizes de colisão NFP pré-calculadas. A posição é testada varrendo a grade `(cx, cy)` e consultando o NFP contra cada peça já posicionada.

| Arquivo | O que faz |
|---|---|
| `strip_packing_discretização_irregulares.py` | **Versão principal com rotação**: `Item` com bounding box por rotação, BL testa as rotações em ordem (primeira que couber), NFP indexado `[idA][rotA][idB][rotB]`, RS com swap. Grava layout (`.png`) e `resultados.txt` por instância. Tem fallback "REJEITADA" para peça que não coube. Contém `gerar_pontos_normais` sem uso (resíduo). |
| `strip_packing_no_rotation.py` | Mesma ideia **sem rotação** (uma matriz RFR/NFP por peça: `nfp_map[idA][idB]`), usado para o experimento "Strip Packing sem Rotação". Menos custo por não iterar sobre rotações. |
| `strip_packing_teste_OS.py` | Cópia da versão com rotação instrumentada para **experimento estatístico**: roda 30 sementes por instância, conta avaliações do BL e verificações NFP (`MetricasExecucao`), reporta média/desvio de L e tempo. Pré-calcula a grade de candidatos (`range`). Foi usado para comparar Windows x Linux ("OS"). Contém `print` de depuração por peça. |

---

## Subpastas de `src`

### `analise_de_resultados/`

| Arquivo | O que faz |
|---|---|
| `script_analise.py` | Lê 5 arquivos `resulttesteinst.txt` (testes de `alpha` = 0,50 / 0,80 / 0,90 / 0,95 / 0,99 com T0 = 1000, de fev/2026), junta em um DataFrame (pandas), imprime tabela de média/melhor área e tempo médio por alpha e gera o gráfico de barras `comparacao_5_arquivos.png` (seaborn). Analisa os resultados da Etapa 2 (RS+BL mochila). |

### `semana 06-10 de abril/` — versões "consertadas" da Etapa 2

Mesmos algoritmos dos arquivos `RS+...v2-3_operadores` da raiz, corrigidos para separar **área física** de **valor do objetivo** (antes o "Area Maxima" podia ser, na verdade, a soma de valores). Mudanças comuns:
- `Instance` ganha `modo_calculo` ("Área" se todos os valores são 0, "Valor" caso contrário) e `area_total_container`.
- BL/HZZ retorna 4 valores: `score, itens, area_ocupada, valor_objetivo`; o RS devolve também `best_area` e `best_val`.
- Resultado grava coluna de tipo (Valor/Área), valor objetivo e **ocupação** (`área/área_container (%)`).

| Arquivo | O que faz |
|---|---|
| `RS+BL_v2-3_operadores-consertado.py` | RS (swap/inversão/inserção) + BL sem rotação, versão corrigida. |
| `RS+BL+Rotacao_v2-3_operadores-consertado.py` | RS + BL com rotação 90°, versão corrigida. |
| `RS+HZZ_v2-3_operadores-consertado.py` | RS + zig-zag horizontal sem rotação, versão corrigida. |
| `RS+HZZ+Rotacao_v2-3_operadores-consertado.py` | RS + zig-zag horizontal com rotação, versão corrigida. |
| `app.py` | Interface **Streamlit**: upload de várias instâncias `.txt`, parâmetros (T0, alpha, iterações) na barra lateral, executa RS+BL+Rotação em lote, mostra métricas, layout plotado e tabela das peças. **Importa `RS_BL_Rot`, que não existe mais** (precisa apontar para `RS+BL+Rotacao_..-consertado.py` ou renomear o módulo; os nomes com `+` e `-` não são importáveis diretamente). |

### `semana 20-24 abril/` — RS com busca local (HC)

Partem das versões consertadas com rotação e acrescentam, ao final de cada temperatura, um **refinamento tipo Hill Climbing**: 20 trocas (swap) aceitas apenas se melhorarem a solução, antes de reduzir a temperatura. Hibridiza o RS com busca local gulosa.

| Arquivo | O que faz |
|---|---|
| `RS(HC)+BL+Rotacao_v2-3_operadores-consertado.py` | RS + Hill Climbing com BL e rotação. |
| `RS(HC)+HZZ+Rotacao_v2-3_operadores-consertado.py` | RS + Hill Climbing com zig-zag horizontal e rotação. |

---

## Sugestão de organização

| Situação | Arquivos |
|---|---|
| **Manter como principal** | `strip_packing_discretização_irregulares.py` (com rotação), `strip_packing_no_rotation.py` (sem rotação) |
| **Manter (melhor versão da Etapa 2)** | `semana 06-10 de abril/*-consertado.py`, `semana 20-24 abril/RS(HC)*`, `app.py` (corrigir import), `analise_de_resultados/script_analise.py` |
| **Manter como experimento** | `strip_packing_teste_OS.py` (30 seeds + métricas), `pli2 3.0 .py` / `pli2 (mochila) 2.0.py` (baseline exato para comparação) |
| **Histórico (pode ir para `src/legado/`)** | `RS+BL_v1.py`, `RS+BL_v2-3_operadores.py`, `RS+HZZ_*`, `RS+BL+Rotacao_*` (da raiz, substituídas pelas `-consertado`), `strip_packing.py`, `strip_packing VZZ.py`, `strip_packing_discretização.py`, `modelo PLI.py`, `pli 2.py` |
| **Estudos/testes soltos (pode ir para `docs/` ou `legado/`)** | `HZZ.py`, `RS.py`, `recozimento simulado.py`, `BLArray.py` |

Pontos de atenção:
- Os nomes com espaços, acentos e `+` (`pli2 3.0 .py`, `RS+BL_v1.py`, `strip_packing_discretização.py`) dificultam importação; vale padronizar caso queiram reutilizar funções como módulo.
- `plot_solution`, `Item`, `Instance`, leitura de instância e RS estão duplicados em quase todos os arquivos; extrair para um módulo comum evitaria divergências entre versões.
- Os caminhos de instâncias/resultados estão fixos (`C:\Users\ubira\...`) nas versões de irregulares.
