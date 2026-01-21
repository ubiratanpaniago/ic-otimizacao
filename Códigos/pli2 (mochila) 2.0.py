import pulp as pl
import glob
import os
import time

# --- Configurações ---
PASTA_ENTRADA = 'instancias-testes'  # Confirme se o nome da pasta está correto
ARQUIVO_SAIDA = 'resultado_final_bateria.txt'
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
    Resolve o Problema da Mochila 2D (Maximizar Valor dentro do Bin).    
    """
    inicio_construcao = time.time()
    
    m = len(items_list)
    item_ids = range(m)
    l = {i: items_list[i]['largura'] for i in item_ids}
    c = {i: items_list[i]['altura'] for i in item_ids}
    
    # --- LÓGICA DE VALOR ---
    # Se o arquivo traz valor 0, usamos a Área (LxA) como valor.
    v = {}
    for i in item_ids:
        valor_arquivo = items_list[i]['valor']
        if valor_arquivo > 0:
            v[i] = valor_arquivo
        else:
            v[i] = l[i] * c[i] # Valor = Área
    
    X = range(L + 1)
    Y = range(C + 1)
    X_i = {i: range(L - l[i] + 1) for i in item_ids}
    Y_i = {i: range(C - c[i] + 1) for i in item_ids}

    prob = pl.LpProblem("2OPP_Mochila", pl.LpMaximize)

    # --- 1. CRIANDO VARIÁVEIS (Pode demorar) ---
    X_ipq = {}
    for i in item_ids:
        # Checagem de tempo
        if time.time() - inicio_construcao > time_limit: return "Time Limit (Building Vars)", 0, None
        X_ipq[i] = {}
        for p in X_i[i]:
            X_ipq[i][p] = pl.LpVariable.dicts(f"X_{i}_{p}", Y_i[i], cat=pl.LpBinary)

    # Função Objetivo (Maximizar Valor Total)
    # Soma de (Valor do item * Se ele foi escolhido)
    obj_func = []
    for i in item_ids:
        for p in X_i[i]:
            for q in Y_i[i]:
                obj_func.append(v[i] * X_ipq[i][p][q])
    
    prob += pl.lpSum(obj_func), "Maximizar_Valor_Total"

    # Restrição de escolha (<= 1)
    # O item pode ser empacotado (1) ou deixado de fora (0)
    for i in item_ids:
        prob += pl.lpSum(X_ipq[i][p][q] for p in X_i[i] for q in Y_i[i]) <= 1, f"Knapsack_Item_{i}"

    # Restrição: Não Sobreposição (Mantém igual)
    for s in X:
        if time.time() - inicio_construcao > time_limit: return "Time Limit (Constraints)", 0, None
        for t in Y:
            soma_cobertura = []
            for i in item_ids:
                valid_p = [p for p in X_i[i] if (s - l[i] + 1) <= p <= s]
                valid_q = [q for q in Y_i[i] if (t - c[i] + 1) <= q <= t]
                soma_cobertura.extend([X_ipq[i][p][q] for p in valid_p for q in valid_q])
            
            if soma_cobertura:
                prob += pl.lpSum(soma_cobertura) <= 1

    # Cortes 
    for s in X:
        if time.time() - inicio_construcao > time_limit: return "Time Limit (Cuts)", 0, None
        soma_c_i = []
        for i in item_ids:
            valid_p = [p for p in X_i[i] if (s - l[i] + 1) <= p <= s]
            soma_c_i.extend([c[i] * X_ipq[i][p][q] for p in valid_p for q in Y_i[i]])
        if soma_c_i:
            prob += pl.lpSum(soma_c_i) <= C

    for t in Y:
        if time.time() - inicio_construcao > time_limit: return "Time Limit (Cuts)", 0, None
        soma_l_i = []
        for i in item_ids:
            valid_q = [q for q in Y_i[i] if (t - c[i] + 1) <= q <= t]
            soma_l_i.extend([l[i] * X_ipq[i][p][q] for p in X_i[i] for q in valid_q])
        if soma_l_i:
            prob += pl.lpSum(soma_l_i) <= L

    # --- 3. RESOLUÇÃO ---
    
    tempo_gasto_construcao = time.time() - inicio_construcao
    tempo_restante = time_limit - tempo_gasto_construcao
    
    if tempo_restante <= 0:
        return "Time Limit (Before Solve)", 0, None

    prob.solve(pl.PULP_CBC_CMD(msg=False, timeLimit=tempo_restante)) 

    status = pl.LpStatus[prob.status]
    
    valor_total_obtido = pl.value(prob.objective) # Pega o valor maximizado
    
    solution = []
    if status == 'Optimal':
        for i in item_ids:
            item_escolhido = False
            for p in X_i[i]:
                for q in Y_i[i]:
                    if pl.value(X_ipq[i][p][q]) == 1:
                        item_id = items_list[i]['id'] 
                        solution.append({'item_id': item_id, 'l': l[i], 'c': c[i], 'p': p, 'q': q, 'v': v[i]})
                        item_escolhido = True
        
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