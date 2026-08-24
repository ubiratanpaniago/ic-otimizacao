import os
import time
import random
import math
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# --- Estrutura de Dados ---

class Item:
    def __init__(self, id, demanda, rotacoes, rfr_matrizes, vertices):
        self.id = id
        self.demanda = demanda  # Quantidade de cópias necessarias desse item
        self.rotacoes = rotacoes  # ex [0, 90, 180 ,270]
        self.rfr_matrizes = rfr_matrizes # lista com as matrizes discretas de cada rotação

        self.num_rotations = len(rotacoes) # quantidade de rotações permitidas
        self.vertices = vertices

        # Guarde a Bounding Box (largura e comprimento máximos) para cada rotação
        # No código anterior: l é X (comprimento) e w é Y (largura fixa)
        self.max_box_r = []

        # Calcula a Bounding Box na Escala 1 (baseado apenas nos vértices)
        for angulo in rotacoes:
            if not vertices:
                # Prevenção caso falhe a leitura dos vértices
                self.max_box_r.append({'w': 1, 'l': 1})
                continue

            rad = graus_para_radianos(angulo)
            v_rot = []
            
            for vx, vy in vertices:
                nx = (vx * math.cos(rad)) - (vy * math.sin(rad))
                ny = (vx * math.sin(rad)) + (vy * math.cos(rad))
                v_rot.append((nx, ny))
            
            min_x = min(v[0] for v in v_rot)
            max_x = max(v[0] for v in v_rot)
            min_y = min(v[1] for v in v_rot)
            max_y = max(v[1] for v in v_rot)
            
            # math.ceil garante que a caixa cubra o limite decimal no grid
            w = math.ceil(max_y - min_y)
            l = math.ceil(max_x - min_x)
            
            # Prevenção: nunca deixa a altura/comprimento ser 0
            self.max_box_r.append({'w': max(1, w), 'l': max(1, l)})
            
        # Calcula a área real geométrica (Escala 1) usando a Fórmula de Shoelace
        area_calc = 0
        if vertices:
            for i in range(len(vertices)):
                x1, y1 = vertices[i]
                x2, y2 = vertices[(i + 1) % len(vertices)]
                area_calc += (x1 * y2 - x2 * y1)
        self.area = abs(area_calc) / 2.0

class Instance:
    def __init__(self, name, container_w, container_grid, items, nfp_map):
        self.name = name
        self.w = container_w # largura fixa do container
        self.grid = container_grid # matriz inicial do container
        self.items = items # lista de itens
        self.nfp_map = nfp_map #dicionário do nfp da instancia

# --- Funções para a visualização ---
def graus_para_radianos(angulo: float) -> float:
    return (angulo / 180.0) * 3.14159265359

def rotacionar_ponto(x: float, y: float, angulo_graus: float) -> tuple:
    """Rotaciona um ponto bidimensional em torno da origem (0,0)."""
    rad = graus_para_radianos(angulo_graus)
    nx = (x * math.cos(rad)) - (y * math.sin(rad))
    ny = (x * math.sin(rad)) + (y * math.cos(rad))
    return round(nx, 6), round(ny, 6)
# ------------------------------

# --- Função de leitura ---
def get_tokens(filepath: str):
    """
    Função Geradora (Generator).
    Abre o arquivo, limpa as linhas removendo o texto após '#' ou '//',
    e entrega palavra por palavra (ou número por número) sob demanda.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:

                clean_line = line.split('#')[0].split('//')[0]
                
                for token in clean_line.split():
                    yield token
    except FileNotFoundError:
        print(f"Erro Crítico: O arquivo obrigatório '{filepath}' não foi encontrado.")
        sys.exit(-1)

# --- Função de Visualização --- ---(ARRUMAR)---
def plot_solution(container_w, final_l, placed_items, items_originais, scale, instance_name, caminho_salvamento, taxa_ocupacao, total_items):
    fig, ax = plt.subplots(1)
    ax.set_xlim(0, final_l)
    ax.set_ylim(0, container_w)
    ax.set_aspect('equal')
    
    # Desenha o limite do container (faixa)
    rect_container = patches.Rectangle((0, 0), final_l, container_w, linewidth=2, edgecolor='black', facecolor='none', linestyle='--')
    ax.add_patch(rect_container)

    # Print temporário para depuração no terminal
    print(f"DEBUG PLOT - Container W: {container_w} | Final L: {final_l:.2f}")
    print(f"DEBUG PLOT - Quantidade de itens posicionados para desenhar: {len(placed_items)}")
    
    # Cria um dicionário para busca rápida dos itens por ID
    dict_itens = {item.id: item for item in items_originais}
    
    for p in placed_items:
        item_original = dict_itens[p['id']]
        vertices_originais = item_original.vertices  # Lista de tuplas (x, y) lida da pasta 'items'
        
        if not vertices_originais:
            color = [random.random() for _ in range(3)]
            rect = patches.Rectangle((p['x'], p['y']), p['l'], p['w'], linewidth=1, edgecolor='white', facecolor=color, alpha=0.7)
            ax.add_patch(rect)
            continue
            
        # 1. Rotaciona os vértices de acordo com a rotação aplicada na solução
        # Rotações estão em graus (0, 90, 180, 270)
        angulo_graus = item_original.rotacoes[p['rot']]

        vertices_escalados = [(vx * scale, vy * scale) for vx, vy in vertices_originais]
        vertices_rotacionados = [rotacionar_ponto(vx, vy, angulo_graus) for vx, vy in vertices_escalados]
        
        # Encontra o menor ponto após a rotação para fazer o alinhamento correto 
        min_x_rot = min(vx for vx, vy in vertices_rotacionados)
        min_y_rot = min(vy for vx, vy in vertices_rotacionados)
        
        # 2. Desloca os vértices para a posição (cx, cy) decidida pelo Bottom-Left
        vertices_finais = []
        for vx, vy in vertices_rotacionados:
            # Subtrair min_x/min_y para garantir que o objeto se alinhe no (0,0) e depois soma a posição final do container
            tx = (vx - min_x_rot) + p['x']
            ty = (vy - min_y_rot) + p['y']
            vertices_finais.append((tx, ty))
            
        # 3. Desenha o polígono irregular na tela
        color = [random.random() for _ in range(3)]
        poligono_patch = patches.Polygon(vertices_finais, closed=True, linewidth=1, edgecolor='white', facecolor=color, alpha=0.7)
        ax.add_patch(poligono_patch)

    qtd_empacotados = len(placed_items)

    plt.title(f"Instância: {instance_name}\n"
              f"Largura Fixa (W): {container_w} | Comprimento Min. (L): {final_l:.2f}\n"
              f"Taxa de Ocupação: {taxa_ocupacao:.2f}% | Itens Empacotados: {qtd_empacotados}/{total_items}")
    plt.savefig(caminho_salvamento, bbox_inches='tight')
    plt.close()

# --- Geração de pontos baseado na instância ---
def gerar_pontos_normais(valores_itens, limite_maximo):
    """
    Gera todas as combinações lineares inteiras possíveis dos tamanhos dos itens
    que sejam menores ou iguais ao limite máximo (Teoria de Normal Patterns).
    """
    pontos = {0}
    # Força uma ordenação para construir as combinações de forma crescente
    for val in sorted(valores_itens):
        novos_pontos = set()
        for p in pontos:
            k = 1
            while p + k * val <= limite_maximo:
                novos_pontos.add(p + k * val)
                k += 1
        pontos.update(novos_pontos)
    return sorted(list(pontos))

# --- Bottom-Left (BL) - Minimizar L ---
def bottom_left_placement(permutation, instance):
    placed_items = []
    max_l_reached = 0
    container_w = instance.w

    eixo_y_discreto = list(range(container_w))

    limite_l_estimado = sum(
    max(rot['l'] for rot in item.max_box_r) for item in permutation
)
    eixo_x_discreto = list(range(limite_l_estimado))

    candidates = []
    for cx in eixo_x_discreto:
        for cy in eixo_y_discreto:
            candidates.append((cx, cy))

    for item in permutation:
        placed = False

        # --- PRINT DE DEPURAÇÃO ---
        # Pega a altura (W) da primeira rotação da peça para comparar com o container
        altura_peca = item.max_box_r[0]['w']
        print(f"[TESTE PECA {item.id}] Altura da Peca (W): {altura_peca} | Largura do Container (container_w): {container_w}")
        # -------------------------------
        
        # Para cada peça, podemos definir uma rotação padrão para testar.
        for rot_idx in range(item.num_rotations):
            if placed:
                break
                
            # Pega a caixa envolvente do item para a rotação testada
            box = item.max_box_r[rot_idx]
            
            for cx, cy in candidates:
                # 1. Validação física: a caixa envolvente cabe dentro da largura limite do container?
                if cy + box['w'] <= container_w:
                    overlap = False
                    
                    # 2. Varre todos os itens já colocados para testar colisão via NFP
                    for p in placed_items:
                        # nfp_map indexa por [id_da_peça_A][rot_A][id_da_peça_B][rot_B]
                        nfp = instance.nfp_map[p['id']][p['rot']][item.id][rot_idx]
                        
                        ref_i, ref_j = nfp['ref']
                        matriz_nfp = nfp['matrix']
                        
                        # Calcula a posição relativa no grid de colisão
                        # y_relativo = ref_i - (cy - p['y'])
                        # x_relativo = (cx - p['x']) + ref_j
                        
                        y_relativo = cy - p['y'] + ref_i
                        x_relativo = cx - p['x'] + ref_j
                        
                        # Checa se o ponto relativo cai dentro das dimensões da matriz NFP
                        if 0 <= y_relativo < len(matriz_nfp) and 0 <= x_relativo < len(matriz_nfp[0]):
                            # Se na matriz NFP o valor for > 0, há colisão física!
                            if matriz_nfp[y_relativo][x_relativo] > 0:
                                overlap = True
                                break # Não precisa testar outras peças já colocadas, este ponto falhou
                                
                    # 3. Se passou por todas as peças sem colidir, posiciona a peça
                    if not overlap:
                        placed_items.append({
                            'id': item.id,
                            'rot': rot_idx,
                            'x': cx,
                            'y': cy,
                            'w': box['w'],
                            'l': box['l']
                        })
                        
                        # Atualiza o comprimento máximo L atingido na faixa
                        if cx + box['l'] > max_l_reached:
                            max_l_reached = cx + box['l']
                            
                        placed = True
                        break # Peça posicionada com sucesso, pula para a próxima do sequenciamento
                        
        if not placed:
            print(f"  [REJEITADA -> FALLBACK] Peca ID {item.id} não coube no grid NFP! Forçando em X={max_l_reached}") #print temporario para debug

            rot_seguranca = 0
            box_seguranca = item.max_box_r[rot_seguranca]
            pos_x = max_l_reached
            placed_items.append({
                'id': item.id,
                'rot': rot_seguranca,
                'x': max_l_reached,
                'y': 0,
                'w': box_seguranca['w'],
                'l': box_seguranca['l']
            })
            max_l_reached = pos_x + box_seguranca['l']

    # Retorna o score negativo (para o SA maximizar), a lista de peças posicionadas e o L final
    return -max_l_reached, placed_items, max_l_reached
   

# --- Recozimento Simulado (SA) ---
def recozimento_simulado(instance, t0=1000, alpha=0.98, iter_max=100):
    current_order = list(instance.items)
    # Heurística inicial: itens mais compridos (L) primeiro costumam ajudar no encaixe
    current_order.sort(key=lambda x: x.area, reverse=True)
    
    current_score, _, current_l = bottom_left_placement(current_order, instance)
    
    best_order = list(current_order)
    best_score = current_score
    best_l = current_l
    
    t = t0
    step = 0
    
    while t > 0.1:
        for _ in range(iter_max):
            neighbor = list(current_order)
            i, j = random.sample(range(len(neighbor)), 2)
            
            # Operador de Swap
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]

            new_score, _, new_l = bottom_left_placement(neighbor, instance)
            delta = new_score - current_score 
            
            if delta > 0 or random.random() < math.exp(delta / t):
                current_order = neighbor
                current_score = new_score
                
                if current_score > best_score:
                    best_score = new_score
                    best_order = list(neighbor)
                    best_l = new_l
        
        t *= alpha
        step += 1
        if step % 20 == 0:
            print(f"Passo {step} | Temp: {t:.2f} | Melhor L: {best_l:.2f}")
            
    return best_order, best_l

# --- Leitura ---
def read_modular_instance(instancia_path: str):
    """
    Lê a instância estruturada em subpastas: bins, items, rfr e nfr.
    """
    dados = {
        "scale": 1.0,
        "num_pecas": 0,
        "pieces": [],
        "num_bins": 0,
        "bins": [],
        "nfp": {}
    }
    
    # --------------------------------------------------------------------------
    # 1. LEITURA: general_data.in
    # --------------------------------------------------------------------------
    gen_file = os.path.join(instancia_path, "general_data.in")
    tokens_gen = get_tokens(gen_file)
    
    try:
        dados["scale"] = float(next(tokens_gen))
        dados["num_pecas"] = int(next(tokens_gen))
        
        for p in range(dados["num_pecas"]):
            p_id = int(next(tokens_gen))
            demand = int(next(tokens_gen))
            flip = int(next(tokens_gen))
            num_rot = int(next(tokens_gen))
            
            # Lê as rotações especificadas (ex: 0, 90, 180, 270)
            rotations = [float(next(tokens_gen)) for _ in range(num_rot)]
            
            dados["pieces"].append({
                "id": p_id,
                "demand": demand,
                "flip": flip,
                "num_rotations": num_rot,
                "rotations": rotations,
                "vertices": [],          # Preenchido via pasta 'items'
                "rfr_matrices": []       # Preenchido via pasta 'rfr'
            })
            
        dados["num_bins"] = int(next(tokens_gen))
        for c in range(dados["num_bins"]):
            b_id = int(next(tokens_gen))
            copies = int(next(tokens_gen))
            dados["bins"].append({
                "id": b_id,
                "copies": copies,
                "H": 0.0,            # Preenchido via pasta 'bins'
                "W": 0.0,            # Preenchido via pasta 'bins'
                "matrix": []         # Preenchido via pasta 'bins'
            })
            
    except StopIteration:
        print("Erro: O arquivo general_data.in terminou antes do esperado.")
        return None

    # --------------------------------------------------------------------------
    # 2. LEITURA: pasta 'items' (Coordenadas Reais/Geometria)
    # --------------------------------------------------------------------------
    for p_idx, piece in enumerate(dados["pieces"]):
        item_file = os.path.join(instancia_path, "items", f"item_{piece['id']}.in")
        tokens_item = get_tokens(item_file)
        
        try:
            # O arquivo declara o número de polígonos (1) e depois os vértices (6)
            num_poligonos = int(next(tokens_item)) 
            num_vertices = int(next(tokens_item))
            
            vertices = []
            for _ in range(num_vertices):
                vx = float(next(tokens_item))
                vy = float(next(tokens_item))
                vertices.append((vx, vy))
            piece["vertices"] = vertices
        except StopIteration:
            print(f"Erro ao ler os vértices de items/item_{piece['id']}.in")

# --------------------------------------------------------------------------
    # 3. LEITURA: pasta 'rfr' (Representações das Peças)
    # --------------------------------------------------------------------------
    # Abre um arquivo específico para cada rotação da peça
    for p_idx, piece in enumerate(dados["pieces"]):
        for r in range(piece["num_rotations"]):
            # Pega o ângulo correspondente (ex: 0, 90, 180, 270)
            # Converte para int para remover o ".0" do float (ex: 90.0 vira 90)
            angle = int(piece["rotations"][r]) 
            
            rfr_file = os.path.join(instancia_path, "rfr", f"item_{piece['id']}_{angle}.in")
            tokens_rfr = get_tokens(rfr_file)
            
            try:
                _ = next(tokens_rfr)

                rows_I = int(next(tokens_rfr))
                cols_J = int(next(tokens_rfr))

                _ = next(tokens_rfr)
                _ = next(tokens_rfr)
                
                matrix_2d = [[int(next(tokens_rfr)) for _ in range(cols_J)] for _ in range(rows_I)]
                piece["rfr_matrices"].append(matrix_2d)
            except StopIteration:
                print(f"Erro ao ler a matriz discreta de {rfr_file}")

    # --------------------------------------------------------------------------
    # 4. LEITURA: pasta 'bins' (Especificações do Container)
    # --------------------------------------------------------------------------
    for c_idx, bin_info in enumerate(dados["bins"]):
        bin_file = os.path.join(instancia_path, "bins", f"bin_{bin_info['id']}.in")
        tokens_bin = get_tokens(bin_file)
        
        try:
            
            dim1 = float(next(tokens_bin))
            dim2 = float(next(tokens_bin))
            
            # Lê o número de defeitos (atualmente 0 no exemplo inicial (blasz2))
            num_defects = int(next(tokens_bin))
            
            # Atribui as dimensões físicas ao container
            bin_info["H"] = dim1
            bin_info["W"] = dim2
            
            # Como a matriz de ocupação não vem no arquivo, cria uma matriz 
            # de zeros (completamente livre) usando as dimensões lidas.
            # O tamanho discreto do grid será baseado nas dimensões inteiras
            rows_I = int(dim1)
            cols_J = int(dim2)
            
            # Gera a matriz de zeros (0 = espaço livre para posicionar itens)
            matrix_2d = [[0 for _ in range(cols_J)] for _ in range(rows_I)]
            
            # Caso houvesse defeitos listados no arquivo, as coordenadas iam ser 
            # identificadas aqui para marcar como '1' (bloqueado) na matriz.
            
            bin_info["matrix"] = matrix_2d
            
        except StopIteration:
            print(f"Erro ao ler o arquivo de bins/bin_{bin_info['id']}.in")

# --------------------------------------------------------------------------
    # 5. LEITURA: pasta 'nfr' (Matrizes de No-Fit Polygon - Grid de Colisão)
    # --------------------------------------------------------------------------
    dados["nfp"] = {}
    for p1_idx, piece1 in enumerate(dados["pieces"]):
        p1_id = piece1["id"]
        dados["nfp"][p1_id] = {}
        
        for r1 in range(piece1["num_rotations"]):
            dados["nfp"][p1_id][r1] = {}
            rot_1_angle = int(piece1["rotations"][r1])  # Ângulo da rotação da peça 1
            
            for p2_idx, piece2 in enumerate(dados["pieces"]):
                p2_id = piece2["id"]
                dados["nfp"][p1_id][r1][p2_id] = {}
                
                for r2 in range(piece2["num_rotations"]):
                    rot_2_angle = int(piece2["rotations"][r2])  # Ângulo da rotação da peça 2
                    
                    # Monta o nome dinâmico baseado nas duas peças e suas respectivas rotações
                    # Padrão: nfr/1_0_1_90.in
                    nfr_filename = f"{p1_id}_{rot_1_angle}_{p2_id}_{rot_2_angle}.in"
                    nfr_file = os.path.join(instancia_path, "nfr", nfr_filename)
                    
                    tokens_nfr = get_tokens(nfr_file)
                    
                    try:
                        nfp_rows = int(next(tokens_nfr))
                        nfp_cols = int(next(tokens_nfr))

                        v2 = piece2["vertices"] 
                        ref_i = math.ceil(max(v[1] for v in v2) - min(v[1] for v in v2))
                        ref_j = math.ceil(max(v[0] for v in v2) - min(v[0] for v in v2))
                        # --------------------------
                        
                        matrix_2d = [[int(next(tokens_nfr)) for _ in range(nfp_cols)] for _ in range(nfp_rows)]
                        
                        dados["nfp"][p1_id][r1][p2_id][r2] = {
                            "ref": (ref_i, ref_j),
                            "matrix": matrix_2d
                        }
                    except StopIteration:
                        print(f"Erro ao ler a matriz NFP do arquivo: {nfr_file}")

    return dados

# --- Execução Principal ---
def main():
    # ==========================================================================
    # Configuração De Parametrização De Teste
    # ==========================================================================
    # Altere para True para testar apenas uma instância específica.
    # Altere para False para processar todas as instâncias da pasta STRIP.
    RODAR_APENAS_UMA = False  
    
    # Nome da instância única para teste (usada se RODAR_APENAS_UMA for True)
    instancia_unica = "blazewicz1"
    
    # Caminho base do diretório que contém as instâncias
    folder_path = r"C:\Users\ubira\ic-otimizacao\data\STRIP" #usar no windows
    # folder_path = r"/home/ubiratanfilho/Documentos/Projetos/ic-otimizacao/data/STRIP" # usar no linux
    # ==========================================================================

    # 1. Identificador e Pastas de Resultados
    identificador = "Teste_Instancias_Aleatorias"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if not os.path.exists("results"):
        os.makedirs("results")

    pasta_raiz = os.path.join("results/agosto", f"{identificador}_{timestamp}")
    pasta_imagens = os.path.join(pasta_raiz, "imagens")
    os.makedirs(pasta_imagens, exist_ok=True)

    if not os.path.exists(folder_path):
        print(f"ERRO: A pasta de entrada '{folder_path}' NÃO EXISTE. Verifique o caminho.")
        return

    # 2. Definição do lote de execução com base na sua escolha
    if RODAR_APENAS_UMA:
        instancias_para_rodar = [instancia_unica]
        print(f"--- Modo de Teste Único Ativo. Instância selecionada: {instancia_unica}")
    else:
        # Busca todas as subpastas dentro do diretório STRIP
        instancias_para_rodar = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
        print(f"--- Modo Lote Ativo. Encontradas {len(instancias_para_rodar)} instâncias para processar.")

    if not instancias_para_rodar:
        print(f"AVISO: Nenhuma instância encontrada para processamento no caminho '{folder_path}'.")
        return

    # 3. Loop de Processamento 
    for inst_nome in instancias_para_rodar:
        print(f"\n>>> Otimizando L para a instância irregular: {inst_nome}")
        try:
            caminho_instancia = os.path.join(folder_path, inst_nome)
            
            # Carrega a instância
            dados_crus = read_modular_instance(caminho_instancia)
            if not dados_crus:
                continue

            # Criar os objetos de Otimização baseado no que foi lido
            itens_disponiveis = []
            for p_info in dados_crus["pieces"]:
                itens_disponiveis.append(
                    Item(
                        id=p_info["id"],
                        demanda=p_info["demand"],
                        rotacoes=p_info["rotations"],
                        rfr_matrizes=p_info["rfr_matrices"],
                        vertices=p_info["vertices"]
                    )
                )
                
            # Instancia o primeiro Container (bin)
            bin_principal = dados_crus["bins"][0]

            #fator_discreto = 10.0
            
            # fator_discreto = dados_crus["scale"] if dados_crus["scale"] > 1.0 else 10.0
            # largura_discreta = int(bin_principal["H"] * fator_discreto)

            # largura_discreta = int(bin_principal["H"] * dados_crus["scale"])

            # largura_discreta_container = int(bin_principal["W"] * dados_crus["scale"])
            
            # Monta o objeto Instance completo com o mapa de colisões NFP
            inst = Instance(
                name=inst_nome,
                container_w=int(bin_principal["H"]), 
                container_grid=bin_principal["matrix"],
                items=itens_disponiveis,
                nfp_map=dados_crus["nfp"]
            )
            
            # Multiplica os itens conforme a demanda real para o Simulated Annealing
            pecas_para_otimizar = []
            for item in inst.items:
                for _ in range(item.demanda):
                    pecas_para_otimizar.append(item)
            
            # Atualiza a lista de itens da instância com as peças físicas reais duplicadas
            inst.items = pecas_para_otimizar
            area_total_itens = sum(item.area for item in pecas_para_otimizar)

            # Executa a Otimização com o SA
            start_time = time.time()
            best_order, final_l = recozimento_simulado(inst, t0=100, alpha=0.9, iter_max=300)
            _, final_placement, _ = bottom_left_placement(best_order, inst)
            duracao = time.time() - start_time

            # Calcula a taxa de ocupação física ---(ARRUMAR)---
            area_container_usada = inst.w * final_l
            taxa_ocupacao = (area_total_itens / area_container_usada) * 100 if area_container_usada > 0 else 0

            print(f"    [OK] L final: {final_l:.2f} | Ocupacao: {taxa_ocupacao:.2f}% | Tempo: {duracao:.2f}s")

            total_itens = len(pecas_para_otimizar)
            qtd_empacotados = len(final_placement)

            # Salva o resultado
            caminho_img = os.path.join(pasta_imagens, f"layout_{inst.name}.png")
            plot_solution(
                container_w=inst.w, 
                final_l=final_l, 
                placed_items=final_placement, 
                items_originais=itens_disponiveis, 
                scale=1.0,
                instance_name=inst.name, 
                caminho_salvamento=caminho_img, 
                taxa_ocupacao=taxa_ocupacao, 
                total_items=total_itens
            )
            print(f"    [IMG] Salva em: {caminho_img}")
            
            with open(os.path.join(pasta_raiz, "resultados.txt"), "a") as log:
                log.write(f"{inst_nome}: L={final_l:.2f}, Taxa de Ocupacao={taxa_ocupacao:.2f}%, "
                          f"Itens Empacotados={qtd_empacotados}/{total_itens}, Tempo={duracao:.2f}s\n")

        except Exception as e:
            print(f"    [ERRO] Falha ao processar a instância {inst_nome}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n--- Processo finalizado. Verifique a pasta: {pasta_raiz}")

if __name__ == "__main__":
    main()