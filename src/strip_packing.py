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
def plot_solution(container_w, final_l, placed_items, instance_name, caminho_salvamento, taxa_ocupacao, total_items):
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

    qtd_empacotados = len(placed_items)

    plt.title(f"Instância: {instance_name}\n"
              f"Largura Fixa (W): {container_w} | Comprimento Min. (L): {final_l:.2f}\n"
              f"Taxa de Ocupação: {taxa_ocupacao:.2f}% | Itens Empacotados: {qtd_empacotados}/{total_items}")
    plt.savefig(caminho_salvamento, bbox_inches='tight')
    plt.close() 

# --- Bottom-Left (BL) - Minimizar L ---
def bottom_left_placement(permutation, container_w):
    placed_items = []
    max_l_reached = 0 # Minimizar esse cara

    for item in permutation:
        # Pontos candidatos (X, Y) -> (Comprimento, Largura)
        candidates = [(0, 0)]
        for p in placed_items:
            candidates.append((p['x'] + p['l'], p['y']))
            candidates.append((p['x'], p['y'] + p['w']))
        
        # Ordena para priorizar o "mais à esquerda" (X menor) e depois "mais abaixo" (Y menor)
        candidates.sort(key=lambda c: (c[0], c[1]))
        
        for cx, cy in candidates:
            # Verifica se não ultrapassa a LARGURA fixa no eixo Y
            if cy + item.w <= container_w:
                overlap = False
                for p in placed_items:
                    if not (cx + item.l <= p['x'] or cx >= p['x'] + p['l'] or
                            cy + item.w <= p['y'] or cy >= p['y'] + p['w']):
                        overlap = True
                        break
                
                if not overlap:
                    placed_items.append({'id': item.id, 'x': cx, 'y': cy, 'w': item.w, 'l': item.l})
                    # Atualiza o comprimento máximo (L) alcançado no eixo X
                    if cx + item.l > max_l_reached:
                        max_l_reached = cx + item.l
                    break
    
    # Score negativo pois o SA busca o maior valor (minimizar L = maximizar -L)
    return -max_l_reached, placed_items, max_l_reached

# --- Recozimento Simulado (SA) ---
def recozimento_simulado(instance, t0=1000, alpha=0.98, iter_max=100):
    current_order = list(instance.items)
    # Heurística inicial: itens mais compridos (L) primeiro costumam ajudar no encaixe
    current_order.sort(key=lambda x: x.l, reverse=True)
    
    current_score, _, current_l = bottom_left_placement(current_order, instance.w)
    
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

            new_score, _, new_l = bottom_left_placement(neighbor, instance.w)
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
    identificador = "StripPacking_Min_L_Itens-Compridos-Primeiro"
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
            _, final_placement, _ = bottom_left_placement(best_order, inst.w)
            duracao = time.time() - start_time

            area_container = inst.w * final_l
            taxa_ocupacao = (area_total_itens / area_container) * 100 if area_container > 0 else 0

            print(f"    [OK] L final: {final_l:.2f} | Ocupação: {taxa_ocupacao:.2f}% | Tempo: {duracao:.2f}s")

            total_itens = len(inst.items)
            qtd_empacotados = len(final_placement)

            # Salva a imagem
            caminho_img = os.path.join(pasta_imagens, f"layout_{inst.name}.png")
            plot_solution(inst.w, final_l, final_placement, inst.name, caminho_img, taxa_ocupacao, total_itens)
            print(f"    [IMG] Salva em: {caminho_img}")
            
            # (Opcional) Salvar um log de texto dentro da pasta
            with open(os.path.join(pasta_raiz, "resultados.txt"), "a") as log:
                log.write(f"{filename}: L={final_l:.2f}, Taxa de Ocupação={taxa_ocupacao:.2f}%, "
                          f"Itens Empacotados={qtd_empacotados}/{total_itens}, Tempo={duracao:.2f}s\n")

        except Exception as e:
            print(f"    [ERRO] Falha ao processar {filename}: {e}")

    print(f"\n--- Processo finalizado. Verifique a pasta: {pasta_raiz}")

if __name__ == "__main__":
    main()