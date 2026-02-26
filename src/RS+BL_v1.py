import os
import time
import random
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# --- Estrutura de Dados ---
class Item:
    def __init__(self, id, w, h):
        self.id = id
        self.w = w
        self.h = h
        self.area = w * h

class Instance:
    def __init__(self, name, container_w, container_h, items):
        self.name = name
        self.W = container_w
        self.H = container_h
        self.items = items

# --- Função de Visualização ---
def plot_solution(container_w, container_h, placed_items, instance_name, area_total, caminho_salvamento):
    fig, ax = plt.subplots(1)
    ax.set_xlim(0, container_w)
    ax.set_ylim(0, container_h)
    ax.set_aspect('equal')
    
    # Desenha o container
    rect_container = patches.Rectangle((0, 0), container_w, container_h, linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(rect_container)
    
    # Desenha cada item
    for p in placed_items:
        # Cor aleatória para diferenciar itens
        color = [random.random() for _ in range(3)]
        rect = patches.Rectangle((p['x'], p['y']), p['w'], p['h'], linewidth=1, edgecolor='white', facecolor=color, alpha=0.7)
        ax.add_patch(rect)
        # Opcional: colocar o ID do item
        # plt.text(p['x'] + p['w']/2, p['y'] + p['h']/2, str(p['id']), fontsize=8, ha='center')

    plt.title(f"Instância: {instance_name}\nÁrea Total: {area_total}")
    plt.savefig(caminho_salvamento)
    plt.close() 

def preparar_pasta(nome_teste):
    # Cria um nome de pasta descritivo: ex: "SA_T1000_A95_20260219"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_pasta = f"{nome_teste}_{timestamp}"
    
    # Caminho completo dentro da pasta 'results'
    caminho_completo = os.path.join("results", nome_pasta)
    
    if not os.path.exists(caminho_completo):
        os.makedirs(caminho_completo)
    
    return caminho_completo

# --- Bottom-Left (BL) ---
def bottom_left_placement(permutation, container_w, container_h):
    placed_items = []
    total_area = 0
    
    for item in permutation:
        candidates = [(0, 0)]
        for p in placed_items:
            candidates.append((p['x'] + p['w'], p['y']))
            candidates.append((p['x'], p['y'] + p['h']))
        
        candidates.sort(key=lambda c: (c[1], c[0]))
        
        placed = False
        for cx, cy in candidates:
            if cx + item.w <= container_w and cy + item.h <= container_h:
                overlap = False
                for p in placed_items:
                    if not (cx + item.w <= p['x'] or cx >= p['x'] + p['w'] or
                            cy + item.h <= p['y'] or cy >= p['y'] + p['h']):
                        overlap = True
                        break
                
                if not overlap:
                    placed_items.append({'id': item.id, 'x': cx, 'y': cy, 'w': item.w, 'h': item.h})
                    total_area += item.area
                    placed = True
                    break
    
    return total_area, placed_items

# --- Recozimento Simulado (SA) ---
def recozimento_simulado(instance, t0=1000, alpha=0.99, iter_max=50):
    current_order = list(instance.items)
    random.shuffle(current_order)
    current_eval, _ = bottom_left_placement(current_order, instance.W, instance.H)
    
    best_order = list(current_order)
    best_eval = current_eval
    
    t = t0
    step = 0
    print(f"  [RS] Iniciando Otimização. Temperatura Inicial: {t0}")

    while t > 1.0:
        improved = False
        for _ in range(iter_max):
            neighbor = list(current_order)
            i, j = random.sample(range(len(neighbor)), 2)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            
            neighbor_eval, _ = bottom_left_placement(neighbor, instance.W, instance.H)
            
            delta = neighbor_eval - current_eval
            if delta > 0 or (t > 0 and random.random() < math.exp(delta / t)):
                current_order = neighbor
                current_eval = neighbor_eval
                
                if current_eval > best_eval:
                    best_eval = current_eval
                    best_order = list(current_order)
                    improved = True
        
        if step % 5 == 0: # Printa a cada 5 reduções de temperatura
            print(f"    Passo {step} | Temp: {t:.2f} | Melhor Área: {best_eval}")
        
        t *= alpha
        step += 1
        
    return best_eval, best_order

# --- Leitura ---
def load_instance(filepath):
    # (Mesma lógica do código anterior)
    with open(filepath, 'r') as f:
        lines = [line for line in f.readlines() if line.strip() and not line.startswith('#')]
        num_items = int(lines[0].split('#')[0].strip())
        cont_w, cont_h = map(int, lines[1].split('#')[0].strip().split())
        items = []
        for i in range(2, 2 + num_items):
            parts = lines[i].split()
            w, h = int(parts[0]), int(parts[1])
            items.append(Item(i-2, w, h))
    return Instance(os.path.basename(filepath), cont_w, cont_h, items)

# --- Execução Principal ---
def main():
    # 1. Defina um identificador para essa rodada (ex: 'teste_T1000_A90')
    # Pode ser algo que você muda manualmente aqui antes de dar o "play"
    identificador_teste = "teste_T1000_A95"

    # 2. Cria a pasta com o identificador + data/hora
    pasta_teste = preparar_pasta(identificador_teste)

    folder_path = './data/instancia teste 3.0' 
    results_file = os.path.join(pasta_teste, 'resulttesteinst.txt')

    # Define e cria subpasta de imagens
    pasta_imagens = os.path.join(pasta_teste, 'imagens')
    os.makedirs(pasta_imagens, exist_ok=True)
    
    if not os.path.exists(folder_path):
        print(f"Erro: Pasta {folder_path} não encontrada.")
        return

    with open(results_file, 'w') as out:
        out.write("Instancia | Area Maxima | Tempo (s)\n")
        
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                print(f"\n>>> Processando: {filename}")
                start_time = time.time()
                
                inst = load_instance(os.path.join(folder_path, filename))
                best_area, best_order = recozimento_simulado(inst)
                
                # Gera o resultado final com a melhor ordem encontrada
                _, final_placement = bottom_left_placement(best_order, inst.W, inst.H)
                
                end_time = time.time()
                duracao = end_time - start_time

                # --- Verificação/Depuração ---
                print(f"  [OK] Finalizado. Área: {best_area} em {duracao:.2f}s")
                print(f"  [INFO] Lista de posições gerada pelo Bottom-Left (Top 5):")
                for p in final_placement[:5]:
                    print(f"    Item {p['id']}: pos({p['x']}, {p['y']}) dim({p['w']}x{p['h']})")

                # Define o caminho do salvamento da imagem
                caminho_img = os.path.join(pasta_imagens, f"layout_{inst.name}.png")
                
                # Gera imagem do resultado
                plot_solution(inst.W, inst.H, final_placement, inst.name, best_area, caminho_img)
                print(f"  [IMG] Gráfico salvo como 'layout_{caminho_img}.png'")

                out.write(f"{inst.name} | {best_area} | {duracao:.4f}\n")

if __name__ == "__main__":
    main()