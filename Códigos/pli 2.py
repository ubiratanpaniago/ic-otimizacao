import pulp as pl

def carregar_instancia(nome_do_arquivo):
    """
    Lê um arquivo de instância e retorna um dicionário com os dados.
    """
    print(f"--- Carregando dados de '{nome_do_arquivo}' ---")
    dados_instancia = {}
    lista_de_itens = []

    try:
        with open(nome_do_arquivo, 'r', encoding='utf-8') as f:
            
            # --- 1. Lendo o número de itens ---
            linha_n = f.readline().strip()
            num_itens = int(linha_n.split()[0])
            dados_instancia['total_itens'] = num_itens

            # --- 2. Lendo as dimensões do "bin" (contêiner) ---
            linha_bin = f.readline().strip()
            partes_bin = linha_bin.split()
            dados_instancia['bin_largura'] = int(partes_bin[0])
            dados_instancia['bin_altura'] = int(partes_bin[1])

            # --- 3. Lendo os 'n' itens ---
            for i in range(num_itens):
                linha_item = f.readline().strip()
                partes_item = linha_item.split()
                
                item = {
                    'id': i, # Adicionando um ID para referência
                    'largura': int(partes_item[0]), # l_i
                    'altura': int(partes_item[1]),  # c_i
                    'valor': int(partes_item[2])    # v_i (será ignorado pelo solver)
                }
                lista_de_itens.append(item)
            
            dados_instancia['itens'] = lista_de_itens

            # --- 4. Lendo a última linha (nome da instância) ---
            linha_nome = f.readline().strip()
            dados_instancia['nome_instancia'] = linha_nome.split()[0]

        # --- Impressão dos dados lidos ---
        print(f"Nome da Instância: {dados_instancia['nome_instancia']}")
        print(f"Dimensões do Bin (LxA): {dados_instancia['bin_largura']} x {dados_instancia['bin_altura']}")
        print(f"Total de Itens para empacotar: {dados_instancia['total_itens']}")
        print("--- Dados Carregados com Sucesso ---\n")
        return dados_instancia

    except FileNotFoundError:
        print(f"Erro: O arquivo '{nome_do_arquivo}' não foi encontrado.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo: {e}")
        print("Verifique se o formato do arquivo está correto e completo.")
        return None

def solve_2opp_feasibility(L, C, items_list):
    """
    Resolve o Problema de Empacotamento Ortogonal 2D (2OPP)
    O objetivo é verificar se **todos** os itens da lista podem ser 
    empacotados (problema de viabilidade).
    
    :param L: Largura (eixo X) do contêiner
    :param C: Altura (eixo Y) do contêiner
    :param items_list: Lista de dicionários, onde cada dict é
                       {'largura': l_i, 'altura': c_i, ...}
    """

    m = len(items_list)
    item_ids = range(m) # IDs 0, 1, ..., m-1

    # Dicionários para guardar dimensões (l, c)
    l = {i: items_list[i]['largura'] for i in item_ids}
    c = {i: items_list[i]['altura'] for i in item_ids}
    # O 'valor' (v) é ignorado
    
    # --- 1. Definição dos Conjuntos ---
    X = range(L + 1) # {0, 1, ..., L}
    Y = range(C + 1) # {0, 1, ..., C}

    # X_i e Y_i: Posições (p, q) válidas para o canto inferior esquerdo
    X_i = {}
    Y_i = {}
    for i in item_ids:
        X_i[i] = range(L - l[i] + 1) # {0, ..., L - l_i}
        Y_i[i] = range(C - c[i] + 1) # {0, ..., C - c_i}

    # --- 2. Inicializar o Modelo ---
    prob = pl.LpProblem("2OPP_Feasibility", pl.LpMinimize)

    # --- 3. Variáveis de Decisão (Restrição 2.7) ---
    X_ipq = {}
    for i in item_ids:
        X_ipq[i] = {}
        for p in X_i[i]:
            X_ipq[i][p] = pl.LpVariable.dicts(f"X_{i}_{p}", Y_i[i], cat=pl.LpBinary)

    # --- 4. Função Objetivo ---
    # MUDANÇA: Objetivo "dummy" (minimizar 0)
    # Queremos apenas saber se uma solução factível existe.
    prob += 0, "Dummy_Objective"

    # --- 5. Adicionar Restrições ---

    # MUDANÇA (Restrição 2.6): Cada item é empacotado EXATAMENTE uma vez
    # Isso força o modelo a encontrar um lugar para TODOS os itens.
    for i in item_ids:
        prob += pl.lpSum(X_ipq[i][p][q] for p in X_i[i] for q in Y_i[i]) == 1, f"Pack_Item_{i}"

    # Restrição (2.3): Não sobreposição
    for s in X:
        for t in Y:
            soma_cobertura = []
            for i in item_ids:
                valid_p = [p for p in X_i[i] if (s - l[i] + 1) <= p <= s]
                valid_q = [q for q in Y_i[i] if (t - c[i] + 1) <= q <= t]
                soma_cobertura.extend([X_ipq[i][p][q] for p in valid_p for q in valid_q])
            
            if soma_cobertura:
                prob += pl.lpSum(soma_cobertura) <= 1, f"No_Overlap_{s}_{t}"

    # Restrição (2.4): "Corte" Vertical
    for s in X:
        soma_c_i = []
        for i in item_ids:
            valid_p = [p for p in X_i[i] if (s - l[i] + 1) <= p <= s]
            soma_c_i.extend([c[i] * X_ipq[i][p][q] for p in valid_p for q in Y_i[i]])
            
        if soma_c_i:
            prob += pl.lpSum(soma_c_i) <= C, f"Max_Width_Cut_s_{s}"

    # Restrição (2.5): "Corte" Horizontal
    for t in Y:
        soma_l_i = []
        for i in item_ids:
            valid_q = [q for q in Y_i[i] if (t - c[i] + 1) <= q <= t]
            soma_l_i.extend([l[i] * X_ipq[i][p][q] for p in X_i[i] for q in valid_q])
        
        if soma_l_i:
            prob += pl.lpSum(soma_l_i) <= L, f"Max_Length_Cut_t_{t}"

    # --- 6. Resolver o Problema ---
    print("Iniciando o solver (tentando encaixar todos os itens)...")
    prob.solve() 

    # --- 7. Exibir Resultados ---
    status = pl.LpStatus[prob.status]
    print(f"Status da Solução: {status}")

    if status == 'Optimal':
        print("\nSolução encontrada! Todos os itens podem ser empacotados.")
        print("\nPosições dos Itens (canto inferior esquerdo):")
        
        solution = []
        for i in item_ids:
            for p in X_i[i]:
                for q in Y_i[i]:
                    if pl.value(X_ipq[i][p][q]) == 1:
                        # Usamos o 'id' original do item
                        item_id = items_list[i]['id'] 
                        print(f"  Item {item_id} (L={l[i]}, A={c[i]}) -> Posição (p={p}, q={q})")
                        solution.append({'item_id': item_id, 'l': l[i], 'c': c[i], 'p': p, 'q': q})
        return solution
    else:
        print("\nNão foi encontrada uma solução factível.")
        print("Isto significa que não é possível empacotar TODOS os itens da lista no 'bin' fornecido.")
        return None

def visualizar_solucao(L_cont, C_cont, solution):
    """
    Imprime uma visualização simples da grade de empacotamento.
    """
    if not solution:
        return
        
    grid = [["." for _ in range(L_cont)] for _ in range(C_cont)]
    for item in solution:
        for y in range(item['q'], item['q'] + item['c']):
            for x in range(item['p'], item['p'] + item['l']):
                if 0 <= y < C_cont and 0 <= x < L_cont:
                    grid[y][x] = str(item['item_id'] % 10) 
    
    print("\nVisualização do Empacotamento (Y=0 é embaixo):")
    for r in reversed(grid):
        print(" ".join(r))

# --- Bloco Principal de Execução ---
if __name__ == "__main__":

    # 1. Carrega os dados do arquivo
    ## Insira o nome da instância de interesse no campo abaixo, no lugar do "apt18.txt"
    nome_do_arquivo = 'apt18.txt' 
    dados_da_instancia = carregar_instancia(nome_do_arquivo)
    
    if dados_da_instancia:
        # 2. Extrai os dados para passar ao solver
        L_bin = dados_da_instancia['bin_largura']
        C_bin = dados_da_instancia['bin_altura']
        itens_para_solver = dados_da_instancia['itens']
        
        # 3. Resolve o problema de viabilidade
        solucao_final = solve_2opp_feasibility(L_bin, C_bin, itens_para_solver)
        
        # 4. Visualiza a solução se encontrada
        visualizar_solucao(L_bin, C_bin, solucao_final)


        print(f"Status da Solução: {pulp.LpStatus[prob.status]}")
        print(f"Tempo de Execução: {tempo_total:.4f} segundos")