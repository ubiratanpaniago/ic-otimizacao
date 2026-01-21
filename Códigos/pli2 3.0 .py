import pulp as pl
import glob
import os
import time

# --- Configurações ---
PASTA_ENTRADA = 'instancia teste 3.0'  # Confirme se o nome da pasta está correto
ARQUIVO_SAIDA = 'resultado_final 3.0.txt'
TEMPO_LIMITE = 600                  # 10 minutos = 600 segundos (construção + resolução)

def carregar_instancia(caminho_arquivo):
    """ Lê o arquivo e retorna os dados. """
    dados_instancia = {}
    lista_de_itens = []

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            linha_n = f.readline().strip()
            if not linha_n: return None
            num_itens = int(linha_n.split()[0])
            dados_instancia['total_itens'] = num_itens

            linha_bin = f.readline().strip()
            partes_bin = linha_bin.split()
            dados_instancia['bin_largura'] = int(partes_bin[0])
            dados_instancia['bin_altura'] = int(partes_bin[1])

            for i in range(num_itens):
                linha_item = f.readline().strip()
                partes_item = linha_item.split()
                item = {
                    'id': i,
                    'largura': int(partes_item[0]),
                    'altura': int(partes_item[1]),
                    'valor': int(partes_item[2])
                }
                lista_de_itens.append(item)
            
            dados_instancia['itens'] = lista_de_itens
            linha_nome = f.readline().strip()
            dados_instancia['nome_instancia'] = linha_nome.split()[0] if linha_nome else "Desconhecido"

        return dados_instancia

    except Exception as e:
        print(f"  [Erro] Falha ao ler {os.path.basename(caminho_arquivo)}: {e}")
        return None

def solve_2opp_knapsack(L, C, items_list, time_limit):
    """ 
    Resolve usando Formulação de Coordenadas (Big-M).
    Muito mais rápido para construir, mas pode ser difícil de resolver se N for muito grande.
    """
    inicio_construcao = time.time()
    
    m = len(items_list)
    ids = range(m)
    w = {i: items_list[i]['largura'] for i in ids}
    h = {i: items_list[i]['altura'] for i in ids}
    
    # Define valores (se valor=0, usa área)
    v = {}
    for i in ids:
        val = items_list[i]['valor']
        v[i] = val if val > 0 else (w[i] * h[i])

    prob = pl.LpProblem("2OPP_Mochila_Coords", pl.LpMaximize)

    # --- VARIÁVEIS ---
    # u[i] = 1 se o item i for escolhido, 0 caso contrário
    u = pl.LpVariable.dicts("Use", ids, cat=pl.LpBinary)

    # x[i], y[i] = coordenadas do canto inferior esquerdo do item i
    # Limites: 0 até L-w[i] (se escolhido)
    x = pl.LpVariable.dicts("X", ids, lowBound=0, upBound=L, cat=pl.LpInteger)
    y = pl.LpVariable.dicts("Y", ids, lowBound=0, upBound=C, cat=pl.LpInteger)

    # Função Objetivo: Maximizar valor dos itens escolhidos
    prob += pl.lpSum(v[i] * u[i] for i in ids)

    # --- RESTRIÇÕES GEOMÉTRICAS BÁSICAS ---
    M_L = L + 1000 # Big-M para Largura
    M_C = C + 1000 # Big-M para Altura

    for i in ids:
        # Se item não for usado, as coordenadas não importam, 
        # mas precisamos garantir que se for usado, cabe no bin.
        # x_i + w_i <= L  --> transformado com Big-M se u[i]=0 relaxa
        # Na verdade, bounds simples funcionam, mas vamos garantir:
        prob += x[i] + w[i] <= L + (1 - u[i]) * M_L
        prob += y[i] + h[i] <= C + (1 - u[i]) * M_C

    # --- RESTRIÇÕES DE NÃO-SOBREPOSIÇÃO (O Coração do Problema) ---
    # Para cada par (i, j), se AMBOS forem escolhidos, um deve estar
    # à esquerda, à direita, acima ou abaixo do outro.
    
    # Precisamos de variaveis binarias auxiliares para a posição relativa
    # left[i][j] = 1 se i está à esquerda de j
    # below[i][j] = 1 se i está abaixo de j
    
    # Isso gera O(N^2) variáveis, o que é muito melhor que O(L*C) do grid.
    
    for i in ids:
        for j in range(i + 1, m): # Apenas pares únicos (i < j)
            
            # Variaveis binarias de separação
            # a = i left of j, b = i right of j, c = i below j, d = i above j
            bin_left  = pl.LpVariable(f"l_{i}_{j}", cat=pl.LpBinary)
            bin_right = pl.LpVariable(f"r_{i}_{j}", cat=pl.LpBinary)
            bin_below = pl.LpVariable(f"b_{i}_{j}", cat=pl.LpBinary)
            bin_above = pl.LpVariable(f"a_{i}_{j}", cat=pl.LpBinary)

            # Se ambos itens (i e j) forem escolhidos (u[i]=1 e u[j]=1),
            # então pelo menos UMA das condições de separação deve ser verdade.
            # bin_left + bin_right + bin_below + bin_above >= u[i] + u[j] - 1
            prob += bin_left + bin_right + bin_below + bin_above >= u[i] + u[j] - 1

            # Restrições Big-M para efetivar a separação
            # Se bin_left=1 -> x[i] + w[i] <= x[j]
            prob += x[i] + w[i] <= x[j] + M_L * (1 - bin_left)
            
            # Se bin_right=1 -> x[j] + w[j] <= x[i]
            prob += x[j] + w[j] <= x[i] + M_L * (1 - bin_right)
            
            # Se bin_below=1 -> y[i] + h[i] <= y[j]
            prob += y[i] + h[i] <= y[j] + M_C * (1 - bin_below)
            
            # Se bin_above=1 -> y[j] + h[j] <= y[i]
            prob += y[j] + h[j] <= y[i] + M_C * (1 - bin_above)

            # Checagem de tempo de construção (segurança)
            if time.time() - inicio_construcao > time_limit:
                 return "Time Limit (Building)", 0, None

    # --- 3. RESOLUÇÃO ---
    
    tempo_gasto_construcao = time.time() - inicio_construcao
    tempo_restante = time_limit - tempo_gasto_construcao
    
    if tempo_restante <= 0:
        return "Time Limit (Before Solve)", 0, None

    prob.solve(pl.PULP_CBC_CMD(msg=False, timeLimit=tempo_restante)) 

    status = pl.LpStatus[prob.status]
    
    valor_total_obtido = pl.value(prob.objective) # Pega o valor maximizado
    
    solution = []
    
    if status == 'Optimal' or status == 'Feasible':
        for i in ids: # Usamos 'ids', não 'item_ids'
            # Verificamos se u[i] é 1 (item escolhido)
            if pl.value(u[i]) is not None and pl.value(u[i]) > 0.5:
                
                # Pegamos as coordenadas diretamente das variáveis x e y
                coord_x = int(pl.value(x[i]))
                coord_y = int(pl.value(y[i]))
                
                solution.append({
                    'item_id': items_list[i]['id'],
                    'l': w[i], 
                    'c': h[i],
                    'p': coord_x, # Não iteramos mais, pegamos direto
                    'q': coord_y, 
                    'v': v[i]
                })
        return status, valor_total_obtido, solution
    else:
        return status, 0, None

# --- Bloco Principal ---
if __name__ == "__main__":
    
    padrao_busca = os.path.join(PASTA_ENTRADA, "*.txt")
    arquivos = glob.glob(padrao_busca)
    
    total_arquivos = len(arquivos)
    print(f"--- Iniciando Bateria de Testes ---")
    print(f"Pasta de entrada: {PASTA_ENTRADA}")
    print(f"Arquivos encontrados: {total_arquivos}")
    print(f"Tempo limite por instância: {TEMPO_LIMITE}s\n")

    if total_arquivos == 0:
        print("Nenhum arquivo encontrado.")
        exit()

    with open(ARQUIVO_SAIDA, 'a', encoding='utf-8') as f:
        f.write(f"\n\n>>> NOVA BATERIA - {time.ctime()} <<<\n")

    for index, caminho_arquivo in enumerate(arquivos):
        nome_arquivo = os.path.basename(caminho_arquivo)
        print(f"[{index+1}/{total_arquivos}] Processando: {nome_arquivo}...", end="\r")
        
        # Carregar
        dados = carregar_instancia(caminho_arquivo)
        
        if dados:
            inicio = time.time()
            
            status_final, valor_total, solucao = solve_2opp_knapsack(
                dados['bin_largura'], 
                dados['bin_altura'], 
                dados['itens'],
                TEMPO_LIMITE
            )
            
            fim = time.time()
            tempo_decorrido = fim - inicio

            # Gravar Log
            with open(ARQUIVO_SAIDA, 'a', encoding='utf-8') as f:

                # Cabeçalho da Instância
                f.write(f"Instância: {dados['nome_instancia']} ({nome_arquivo})\n")
                f.write(f"Dimensões Bin: {dados['bin_largura']} x {dados['bin_altura']}\n")
                f.write(f"Tempo: {tempo_decorrido:.4f}s\n")
                f.write(f"Status Solver: {status_final}\n")
                
                f.write("-" * 20 + " RESULTADOS " + "-" * 20 + "\n")
                
                # Tratamento do Valor Total
                valor_final = valor_total if valor_total is not None else 0
                area_bin = dados['bin_largura'] * dados['bin_altura']
                ocupacao = (valor_final / area_bin) * 100
                
                f.write(f"Valor Total (Área Preenchida): {valor_final}\n")
                f.write(f"Taxa de Ocupação: {ocupacao:.2f}%\n")
                
                # Tratamento da Quantidade de Itens
                qtd_escolhidos = len(solucao) if solucao else 0
                
                # Métricas Finais
                f.write(f"Valor Total (Área Preenchida): {valor_final}\n")
                f.write(f"Taxa de Ocupação: {ocupacao:.2f}%\n")
                f.write(f"Itens Empacotados: {qtd_escolhidos} de {dados['total_itens']}\n")

                # Linha separadora para a próxima instância
                f.write("=" * 55 + "\n\n")
            
            # Atualiza terminal com resultado rápido
            print(f"[{index+1}/{total_arquivos}] {nome_arquivo}: {status_final} ({ocupacao:.1f}%) in {tempo_decorrido:.2f}s      ")
        
        else:
            print(f"[{index+1}/{total_arquivos}] {nome_arquivo}: ERRO DE LEITURA")

    print("\n--- Bateria Finalizada ---")