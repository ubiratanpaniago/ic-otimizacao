import os
import time
import random
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# --- Estrutura de Dados ---
class Item:
    def __init__(self, id, w, h, v):
        self.id = id
        self.w = w
        self.h = h

        self.area = self.w * self.h

        if v == 0:
            self.v = self.area
        else: 
            self.v = v

        # self.area = w * h

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
    total_valor = 0
    
    for item in permutation:
        candidates = [(0, 0)]
        for p in placed_items:
            candidates.append((p['x'] + p['w'], p['y']))
            candidates.append((p['x'], p['y'] + p['h']))
        
        candidates.sort(key=lambda c: (c[1], c[0]))
        
        placed = False
        for cx, cy in candidates:
            
            # Define as orientações possíveis (usando set para evitar testar 2x se w == h)
            orientacoes = list({
                (item.w, item.h, False), # Orientação Original
                (item.h, item.w, True)   # Orientação Rotacionada (90 graus)
            })
            
            # Testa cada orientação
            for current_w, current_h, is_rotated in orientacoes:
                
                # Verifica se a peça (na orientação atual) não vaza do contêiner
                if cx + current_w <= container_w and cy + current_h <= container_h:
                    overlap = False
                    
                    # Verifica colisão com as peças já posicionadas
                    for p in placed_items:
                        if not (cx + current_w <= p['x'] or cx >= p['x'] + p['w'] or
                                cy + current_h <= p['y'] or cy >= p['y'] + p['h']):
                            overlap = True
                            break
                    
                    # Se couber perfeitamente, registra a peça
                    if not overlap:
                        placed_items.append({
                            'id': item.id, 
                            'x': cx, 
                            'y': cy, 
                            'w': current_w,   # Salva a largura final usada
                            'h': current_h,   # Salva a altura final usada
                            'v': item.v,
                            'rotated': is_rotated # Registra se precisou girar
                        })
                        
                        total_area += item.area
                        total_valor += item.v
                        placed = True
                        break # Peça colocada, quebra o loop de orientações
            
            if placed:
                break # Quebra o loop de candidatos e vai para o próximo item
    
    # Cálculo do score e dispersão (mantido igual ao seu original)
    dispersao = sum(p['x'] + p['w'] + p['y'] + p['h'] for p in placed_items)
    score_avaliacao = total_valor - (dispersao * 0.0001)

    return score_avaliacao, placed_items, total_area

# --- Recozimento Simulado (SA) ---
def recozimento_simulado(instance, t0=1000, alpha=0.95, iter_max=300):
    current_order = list(instance.items)
    # random.shuffle(current_order)
    current_order.sort(key=lambda x: x.area, reverse=True)
    current_eval, _, current_area = bottom_left_placement(current_order, instance.W, instance.H)
    
    best_order = list(current_order)
    best_eval = current_eval
    best_area = current_area # Guarda a melhor área
    
    t = t0
    step = 0
    print(f"  [RS] Iniciando Otimização. Temperatura Inicial: {t0}")

    while t > 1.0:
        for _ in range(iter_max):

            neighbor = list(current_order)

            # Roleta para escolha do operador
            r = random.random()
            
            if r < 0.4:
                # 1. SWAP (40% de chance): Troca dois itens de lugar
                i, j = random.sample(range(len(neighbor)), 2)
                neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                
            elif r < 0.7:
                # 2. INVERSÃO / 2-Opt (30% de chance): Inverte um bloco de itens
                i, j = sorted(random.sample(range(len(neighbor)), 2))
                neighbor[i:j+1] = reversed(neighbor[i:j+1])
                
            else:
                # 3. INSERÇÃO / Shift (30% de chance): Move um item para outra posição
                idx_origem = random.randrange(len(neighbor))
                item_removido = neighbor.pop(idx_origem)
                
                idx_destino = random.randrange(len(neighbor) + 1)
                neighbor.insert(idx_destino, item_removido)
            
            # Avalia o novo vizinho
            neighbor_eval, _, neighbor_area = bottom_left_placement(neighbor, instance.W, instance.H)
            
            delta = neighbor_eval - current_eval
            
            # Critério de aceitação do Recozimento Simulado
            if delta > 0 or (t > 0 and random.random() < math.exp(delta / t)):
                current_order = neighbor
                current_eval = neighbor_eval
                
                if current_eval > best_eval:
                    best_eval = current_eval
                    best_order = list(current_order)
                    best_area = neighbor_area 
        
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
            w = int(parts[0])
            h = int(parts[1])
            v = int(parts[2])
            # w, h = int(parts[0]), int(parts[1])
            items.append(Item(i-2, w, h, v))
    return Instance(os.path.basename(filepath), cont_w, cont_h, items)

# --- Execução Principal ---
def main():
    # 1. Defina um identificador para essa rodada (ex: 'teste_T1000_A90')
    identificador_teste = "RS+BL+Rotacao-3operadores2-02503"

    # 2. Cria a pasta com o identificador + data/hora
    pasta_teste = preparar_pasta(identificador_teste)

    folder_path = './data/ins teste 4.0' 
    results_file = os.path.join(pasta_teste, 'resulttesteinst.txt')

    # Define e cria subpasta de imagens
    pasta_imagens = os.path.join(pasta_teste, 'imagens')
    os.makedirs(pasta_imagens, exist_ok=True)
    
    if not os.path.exists(folder_path):
        print(f"Erro: Pasta {folder_path} não encontrada.")
        return
    
    # Definindo largura de cada coluna (ajustar caso necessario)
    w_nome = 10
    w_dim = 15
    w_itens = 12
    w_area = 15
    w_tempo = 10

    with open(results_file, 'w') as out:
        # Cabeçalho do resultado
        header = (
            f"{'Instancia':<{w_nome}} | "
            f"{'Dimensoes':<{w_dim}} | "
            f"{'Itens (E/T)':<{w_itens}} | "
            f"{'Area Maxima':<{w_area}} | "
            f"{'Tempo (s)':<{w_tempo}}\n"
        )

        separador = "-" * len(header) + "\n"

        out.write(header)
        out.write(separador)
        
        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                print(f"\n>>> Processando: {filename}")
                start_time = time.time()
                
                inst = load_instance(os.path.join(folder_path, filename))
                best_area, best_order = recozimento_simulado(inst)
                
                # Gera o resultado final com a melhor ordem encontrada
                _, final_placement, _ = bottom_left_placement(best_order, inst.W, inst.H)

                # Calcula a quantidade de itens empacotados
                qtd_empacotados = len(final_placement)
                qtd_total = len(inst.items)
                
                end_time = time.time()
                duracao = end_time - start_time

                # Preparando strings complexas
                dimensoes = f"{inst.W}x{inst.H}"
                status_itens = f"{len(final_placement)}/{len(inst.items)}"

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

                # Printa o resultado de cada instancia
                linha = (
                f"{inst.name:<{w_nome}} | "
                f"{dimensoes:<{w_dim}} | "
                f"{status_itens:<{w_itens}} | "
                f"{best_area:<{w_area}} | "
                f"{duracao:<{w_tempo}}\n" 
                )

                out.write(linha)

if __name__ == "__main__":
    main()