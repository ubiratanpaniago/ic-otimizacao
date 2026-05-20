import os
import time
import random
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# --- Estrutura de Dados ---

class Item:
    def __init__(self, id, w, l):
        self.id = id
        self.w = w  # Largura fixa (eixo Y)
        self.l = l  # Comprimento variável (eixo X)
        self.area = w * l

class Instance:
    def __init__(self, name, container_w, items):
        self.name = name
        self.w = container_w
        self.items = items

# --- Função de Visualização ---
def plot_solution(container_w, final_l, placed_items, instance_name, caminho_salvamento, taxa_ocupacao):
    fig, ax = plt.subplots(1)
    # X é o comprimento (L) atingido, Y é a largura (W) fixa
    ax.set_xlim(0, final_l)
    ax.set_ylim(0, container_w)
    ax.set_aspect('equal')
    
    # Desenha o container (faixa)
    rect_container = patches.Rectangle((0, 0), final_l, container_w, linewidth=2, edgecolor='black', facecolor='none', linestyle='--')
    ax.add_patch(rect_container)
    
    for p in placed_items:
        color = [random.random() for _ in range(3)]
        # p['l'] é o comprimento no eixo x, p['w'] é a largura no eixo y
        rect = patches.Rectangle((p['x'], p['y']), p['l'], p['w'], linewidth=1, edgecolor='white', facecolor=color, alpha=0.7)
        ax.add_patch(rect)

    plt.title(f"Instância: {instance_name}\nLargura Fixa (W): {container_w} | Comprimento Min. (L): {final_l:.2f}\nTaxa de Ocupação: {taxa_ocupacao:.2f}%")
    plt.savefig(caminho_salvamento)
    plt.close() 

# --- Vertical Zig-Zag (VZZ) - Minimizar L ---
def vertical_zig_zag_placement(permutation, container_w):
    placed_items = []
    current_x = 0        # Início da coluna atual no eixo X
    current_y = 0        # Posição atual de empilhamento no eixo Y
    next_col_x = 0       # Onde a próxima coluna deve começar (o maior X alcançado na coluna atual)
    max_l_reached = 0    # Comprimento total do container

    for item in permutation:
        # Se o item não cabe verticalmente na coluna atual, fecha a coluna e vai para a próxima
        if current_y + item.w > container_w:
            current_x = next_col_x
            current_y = 0

        # Posiciona o item na coordenada atual
        placed_items.append({
            'id': item.id, 
            'x': current_x, 
            'y': current_y, 
            'w': item.w, 
            'l': item.l
        })

        # Atualiza o avanço vertical da coluna atual
        current_y += item.w
        
        # Monitora a "frente" da coluna atual para saber onde a próxima começará
        if current_x + item.l > next_col_x:
            next_col_x = current_x + item.l
            
        # Monitora o comprimento total do container
        if current_x + item.l > max_l_reached:
            max_l_reached = current_x + item.l
    
    # Score negativo pois o SA busca o maior valor (minimizar L = maximizar -L)
    return -max_l_reached, placed_items, max_l_reached

# --- Recozimento Simulado (SA) ---
def recozimento_simulado(instance, t0=1000, alpha=0.98, iter_max=100):
    current_order = list(instance.items)
    current_order.sort(key=lambda x: x.l, reverse=True)
    
    current_score, _, current_l = vertical_zig_zag_placement(current_order, instance.w)
    
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

            new_score, _, new_l = vertical_zig_zag_placement(neighbor, instance.w)
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
def load_instance(filepath):

    with open(filepath, 'r') as f:
        lines = [line for line in f.readlines() if line.strip()]
        num_items = int(lines[0].split()[0])
        cont_w = int(lines[1].split()[0]) # Largura fixa
        
        items = []
        for i in range(2, 2 + num_items):
            parts = list(map(int, lines[i].split()))
            # parts[0]=w, parts[1]=l
            items.append(Item(i-2, parts[0], parts[1]))
    return Instance(os.path.basename(filepath), cont_w, items)

# --- Execução Principal ---
def main():
    # 1. Identificador e Pastas
    identificador = "StripPacking_Min_L_VZZ"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Garante que a pasta 'results' existe antes de criar a subpasta
    if not os.path.exists("results"):
        os.makedirs("results")
        print("--- Pasta 'results' criada.")

    pasta_raiz = os.path.join("results", f"{identificador}_{timestamp}")
    pasta_imagens = os.path.join(pasta_raiz, "imagens")
    os.makedirs(pasta_imagens, exist_ok=True)

    # 2. Caminho dos Dados (VERIFICAR!)
    folder_path = './data/ins teste 4.0' 
    
    if not os.path.exists(folder_path):
        print(f"ERRO: A pasta de entrada '{folder_path}' NÃO EXISTE. Verifique o caminho.")
        return

    arquivos = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    if not arquivos:
        print(f"AVISO: Nenhum arquivo .txt encontrado em '{folder_path}'.")
        return

    print(f"--- Encontrados {len(arquivos)} arquivos. Iniciando processamento...")

    for filename in arquivos:
        print(f"\n>>> Otimizando L para: {filename}")
        try:
            filepath = os.path.join(folder_path, filename)
            inst = load_instance(filepath)
            
            area_total_itens = sum(item.area for item in inst.items)

            start_time = time.time()
            best_order, final_l = recozimento_simulado(inst)
            _, final_placement, _ = vertical_zig_zag_placement(best_order, inst.w)
            duracao = time.time() - start_time

            area_container = inst.w * final_l
            taxa_ocupacao = (area_total_itens / area_container) * 100 if area_container > 0 else 0

            print(f"    [OK] L final: {final_l:.2f} | Ocupação: {taxa_ocupacao:.2f}% | Tempo: {duracao:.2f}s")

            # Salva a imagem
            caminho_img = os.path.join(pasta_imagens, f"layout_{inst.name}.png")
            plot_solution(inst.w, final_l, final_placement, inst.name, caminho_img, taxa_ocupacao)
            print(f"    [IMG] Salva em: {caminho_img}")
            
            # (Opcional) Salvar um log de texto dentro da pasta
            with open(os.path.join(pasta_raiz, "resultados.txt"), "a") as log:
                log.write(f"{filename}: L={final_l:.2f}, Taxa de Ocupação={taxa_ocupacao:.2f}, Tempo={duracao:.2f}s\n")

        except Exception as e:
            print(f"    [ERRO] Falha ao processar {filename}: {e}")

    print(f"\n--- Processo finalizado. Verifique a pasta: {pasta_raiz}")

if __name__ == "__main__":
    main()