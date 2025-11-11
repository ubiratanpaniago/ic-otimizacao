import pulp as pl

# Dicionário que vai armazenar todos os dados lidos
dados_instancia = {}
# Lista para guardar os itens
lista_de_itens = []

# Coloque o nome do seu arquivo aqui
nome_do_arquivo = 'ed1.txt' 

try:
    with open(nome_do_arquivo, 'r', encoding='utf-8') as f:
        
        # --- 1. Lendo o número de itens ---
        # f.readline() lê a próxima linha do arquivo
        # .strip() remove espaços em branco e quebras de linha (\n)
        # .split() divide a string por espaços (ex: "5 -> ...")
        # [0] pega o primeiro elemento (o "5")
        linha_n = f.readline().strip()
        num_itens = int(linha_n.split()[0])
        dados_instancia['total_itens'] = num_itens

        # --- 2. Lendo as dimensões do "bin" (contêiner) ---
        linha_bin = f.readline().strip()
        partes_bin = linha_bin.split()
        dados_instancia['bin_largura'] = int(partes_bin[0])
        dados_instancia['bin_altura'] = int(partes_bin[1])

        # --- 3. Lendo os 'n' itens (usando o número lido na linha 1) ---
        # Usamos um loop 'for' para ler exatamente 'num_itens' linhas
        for _ in range(num_itens):
            linha_item = f.readline().strip()
            partes_item = linha_item.split()
            
            # Criamos um dicionário para cada item (mais organizado)
            item = {
                'largura': int(partes_item[0]),
                'altura': int(partes_item[1]),
                'valor': int(partes_item[2])
            }
            lista_de_itens.append(item)
        
        # Adiciona a lista completa ao nosso dicionário principal
        dados_instancia['itens'] = lista_de_itens

        # --- 4. Lendo a última linha (nome da instância) ---
        linha_nome = f.readline().strip()
        dados_instancia['nome_instancia'] = linha_nome.split()[0]


    # --- Impressão dos dados lidos ---
    print("---  Dados Carregados ---")
    print(f"Nome da Instância: {dados_instancia['nome_instancia']}")
    print(f"Dimensões do Bin (LxA): {dados_instancia['bin_largura']} x {dados_instancia['bin_altura']}")
    print(f"Total de Itens: {dados_instancia['total_itens']}")
    print("\n--- Itens ---")
    
    # Exemplo de como usar os dados:
    for i, item in enumerate(dados_instancia['itens']):
        print(f"  Item {i+1}: L={item['largura']}, A={item['altura']}, V={item['valor']}")


except FileNotFoundError:
    print(f"Erro: O arquivo '{nome_do_arquivo}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro ao processar o arquivo: {e}")
    print("Verifique se o formato do arquivo está correto e completo.")

def solve_2opp(L, C, items_list):
    """
    Resolve o Problema de Empacotamento Ortogonal 2D (2OPP)
    usando o modelo de programação inteira de Junqueira et al.

    :param L: Comprimento (eixo X) do contêiner
    :param C: Largura (eixo Y) do contêiner
    :param items_list: Lista de tuplas, onde cada tupla é (l_i, c_i)
                       representando o comprimento e largura do item i.
    """

    m = len(items_list)
    item_ids = range(m) # Nossos IDs de item serão 0, 1, ..., m-1

    # Dicionário para guardar dimensões (l_i, c_i) por ID
    items_data = {i: items_list[i] for i in item_ids}
    
    # --- 1. Definição dos Conjuntos ---
    
    # Coordenadas possíveis no contêiner
    X = range(L + 1) # {0, 1, ..., L}
    Y = range(C + 1) # {0, 1, ..., C}

    # X_i e Y_i: Posições (p, q) válidas para o canto inferior esquerdo do item i
    # (Conforme equações 2.1 e 2.2)
    X_i = {}
    Y_i = {}
    for i in item_ids:
        l_i, c_i = items_data[i]
        X_i[i] = range(L - l_i + 1) # {0, ..., L - l_i}
        Y_i[i] = range(C - c_i + 1) # {0, ..., C - c_i}

    # --- 2. Inicializar o Modelo ---
    # O objetivo é apenas encontrar uma solução (feasibility problem)
    prob = pl.LpProblem("2OPP_Junqueira", pl.LpMinimize)

    # --- 3. Variáveis de Decisão (Restrição 2.7) ---
    # X_ipq = 1 se o item i é colocado em (p, q), 0 caso contrário.
    # Usamos dicionários aninhados para X_ipq[i][p][q]
    X_ipq = {}
    for i in item_ids:
        X_ipq[i] = {}
        for p in X_i[i]:
            # Cria um dicionário de variáveis para cada 'p' válido
            X_ipq[i][p] = pl.LpVariable.dicts(f"X_{i}_{p}", Y_i[i], cat=pl.LpBinary)

    # --- 4. Função Objetivo ---
    # O texto indica que o objetivo é apenas verificar se todos os m itens
    # podem ser arranjados. Usamos um objetivo "dummy" (minimizar 0).
    prob += 0, "Dummy_Objective"

    # --- 5. Adicionar Restrições ---

    # Restrição (2.6): Cada item é empacotado exatamente uma vez
    for i in item_ids:
        prob += pl.lpSum(X_ipq[i][p][q] for p in X_i[i] for q in Y_i[i]) == 1, f"Pack_Item_{i}"

    # Restrição (2.3): Não sobreposição
    # Para cada ponto (s, t) da grade, no máximo um item pode cobri-lo.
    for s in X:
        for t in Y:
            soma_cobertura = []
            for i in item_ids:
                l_i, c_i = items_data[i]
                
                # Encontra (p,q) válidos que fariam o item i cobrir o ponto (s,t)
                # Condição: s-l_i+1 <= p <= s  E  t-c_i+1 <= q <= t
                valid_p = [p for p in X_i[i] if (s - l_i + 1) <= p <= s]
                valid_q = [q for q in Y_i[i] if (t - c_i + 1) <= q <= t]
                
                soma_cobertura.extend([X_ipq[i][p][q] for p in valid_p for q in valid_q])
            
            if soma_cobertura: # Só adiciona a restrição se houver termos
                prob += pl.lpSum(soma_cobertura) <= 1, f"No_Overlap_{s}_{t}"

    # Restrição (2.4): "Corte" Vertical (melhoria de desempenho)
    # Para cada linha vertical 's', a soma das larguras (c_i) dos itens
    # que a cruzam não pode exceder a largura C do contêiner.
    for s in X:
        soma_c_i = []
        for i in item_ids:
            l_i, c_i = items_data[i]
            # Encontra 'p' tal que o item i cruze a linha s
            # Condição: s-l_i+1 <= p <= s
            valid_p = [p for p in X_i[i] if (s - l_i + 1) <= p <= s]
            
            soma_c_i.extend([c_i * X_ipq[i][p][q] for p in valid_p for q in Y_i[i]])
            
        if soma_c_i:
            prob += pl.lpSum(soma_c_i) <= C, f"Max_Width_Cut_s_{s}"

    # Restrição (2.5): "Corte" Horizontal (melhoria de desempenho)
    # Para cada linha horizontal 't', a soma dos comprimentos (l_i) dos itens
    # que a cruzam não pode exceder o comprimento L do contêiner.
    for t in Y:
        soma_l_i = []
        for i in item_ids:
            l_i, c_i = items_data[i]
            # Encontra 'q' tal que o item i cruze a linha t
            # Condição: t-c_i+1 <= q <= t
            valid_q = [q for q in Y_i[i] if (t - c_i + 1) <= q <= t]
            
            soma_l_i.extend([l_i * X_ipq[i][p][q] for p in X_i[i] for q in valid_q])
        
        if soma_l_i:
            prob += pl.lpSum(soma_l_i) <= L, f"Max_Length_Cut_t_{t}"

    # --- 6. Resolver o Problema ---
    print("Iniciando o solver...")
    # Você pode especificar um solver se tiver um instalado (ex: CBC, Gurobi, CPLEX)
    # prob.solve(pl.CPLEX_CMD())
    prob.solve() 

    # --- 7. Exibir Resultados ---
    status = pl.LpStatus[prob.status]
    print(f"Status da Solução: {status}")

    if status == 'Optimal':
        print("\nSolução encontrada! Posições (canto inferior esquerdo):")
        solution = []
        for i in item_ids:
            for p in X_i[i]:
                for q in Y_i[i]:
                    if pl.value(X_ipq[i][p][q]) == 1:
                        l_i, c_i = items_data[i]
                        print(f"  Item {i} (l={l_i}, c={c_i}) -> Posição (p={p}, q={q})")
                        solution.append({'item': i, 'l': l_i, 'c': c_i, 'p': p, 'q': q})
        return solution
    else:
        print("\nNão foi encontrada uma solução factível.")
        return None

# --- Exemplo de Uso ---
if __name__ == "__main__":
    
    # Dimensões do contêiner
    L_cont = 10  # largura
    C_cont = 10  # altura

    # Lista de itens (comprimento, largura)
    # (l_i, c_i)
    itens = [
        (4, 2),
        (2, 3),
        (2, 6),
        (3, 3)
    ]

    # Resolve o problema
    solution = solve_2opp(L_cont, C_cont, itens)

    # (Opcional) Visualizar a solução se encontrada
    if solution:
        # Cria uma "grade" para visualização
        grid = [["." for _ in range(L_cont)] for _ in range(C_cont)]
        for item in solution:
            for y in range(item['q'], item['q'] + item['c']):
                for x in range(item['p'], item['p'] + item['l']):
                    if 0 <= y < C_cont and 0 <= x < L_cont:
                        grid[y][x] = str(item['item'])
        
        print("\nVisualização do Empacotamento:")
        # Imprime a grade invertida (Y=0 é embaixo)
        for r in reversed(grid):
            print(" ".join(r))