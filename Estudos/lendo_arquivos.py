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