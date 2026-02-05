import os
import time
import random
import math

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

# --- Heurística Bottom-Left (BL) ---
def bottom_left_placement(permutation, container_w, container_h):
    placed_items = []
    total_area = 0
    
    for item in permutation:
        # Tenta encontrar a posição (x, y) mais baixa e depois mais à esquerda
        # Para simplificar, testamos posições baseadas nos cantos dos itens já colocados
        best_x, best_y = None, None
        
        # Pontos candidatos (cantos superiores e direitos de itens já posicionados + (0,0))
        candidates = [(0, 0)]
        for p in placed_items:
            candidates.append((p['x'] + p['w'], p['y']))
            candidates.append((p['x'], p['y'] + p['h']))
        
        # Ordena candidatos por Y e depois por X (essência do Bottom-Left)
        candidates.sort(key=lambda c: (c[1], c[0]))
        
        for cx, cy in candidates:
            if cx + item.w <= container_w and cy + item.h <= container_h:
                # Verifica sobreposição com itens já colocados
                overlap = False
                for p in placed_items:
                    if not (cx + item.w <= p['x'] or cx >= p['x'] + p['w'] or
                            cy + item.h <= p['y'] or cy >= p['y'] + p['h']):
                        overlap = True
                        break
                
                if not overlap:
                    best_x, best_y = cx, cy
                    break # Encontrou a posição BL para este item
        
        if best_x is not None:
            placed_items.append({'x': best_x, 'y': best_y, 'w': item.w, 'h': item.h})
            total_area += item.area
            
    return total_area, placed_items

# --- Simulated Annealing (SA) ---
def simulated_annealing(instance, t0=1000, alpha=0.95, iter_max=100):
    # Solução inicial: ordem original dos itens
    current_order = list(instance.items)
    random.shuffle(current_order)
    current_eval, _ = bottom_left_placement(current_order, instance.W, instance.H)
    
    best_order = list(current_order)
    best_eval = current_eval
    
    t = t0
    while t > 0.1:
        for _ in range(iter_max):
            # Gera vizinho trocando dois itens de lugar
            neighbor = list(current_order)
            i, j = random.sample(range(len(neighbor)), 2)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            
            neighbor_eval, _ = bottom_left_placement(neighbor, instance.W, instance.H)
            
            # Critério de aceitação de Metropolis
            delta = neighbor_eval - current_eval # Maximizar area -> delta positivo é bom
            if delta > 0 or random.random() < math.exp(delta / t):
                current_order = neighbor
                current_eval = neighbor_eval
                
                if current_eval > best_eval:
                    best_eval = current_eval
                    best_order = list(current_order)
        
        t *= alpha # Resfriamento
        
    return best_eval, best_order

# --- IO e Execução ---
def load_instance(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        num_items = int(lines[0].split('#')[0].strip())
        cont_w, cont_h = map(int, lines[1].split('#')[0].strip().split())
        items = []
        for i in range(2, 2 + num_items):
            w, h, _ = map(int, lines[i].split('#')[0].strip().split())
            items.append(Item(i-2, w, h))
    return Instance(os.path.basename(filepath), cont_w, cont_h, items)

def main():
    folder_path = './testeinst' # Caminho da sua pasta
    results_file = 'resultados_otimizacao_teste.txt'
    
    with open(results_file, 'w') as out:
        out.write("Instancia | Valor Solucao (Area) | Tempo (s)\n")
        out.write("-" * 50 + "\n")
        
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                start_time = time.time()
                inst = load_instance(os.path.join(folder_path, filename))
                
                print(f"Resolvendo {inst.name}...")
                best_area, _ = simulated_annealing(inst)
                
                end_time = time.time()
                total_time = end_time - start_time
                
                out.write(f"{inst.name} | {best_area} | {total_time:.4f}\n")

if __name__ == "__main__":
    main()