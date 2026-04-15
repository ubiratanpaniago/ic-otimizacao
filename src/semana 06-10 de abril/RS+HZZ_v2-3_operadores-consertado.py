import os
import time
import random
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# --- Estrutura de Dados ---
class Item:
    def __init__(self, id, w, h, v_input):
        self.id = id
        self.w = w
        self.h = h

        self.area = w * h
        # self.area = self.w * self.h

        # se v for 0, o valor do objetivo vira área, se não vira o valor real
        self.v = self.area if v_input == 0 else v_input

class Instance:
    def __init__(self, name, container_w, container_h, items, modo_calculo):
        self.name = name
        self.W = container_w
        self.H = container_h
        self.items = items
        self.area_total_container = container_w * container_h
        self.modo_calculo = modo_calculo # guarda se é no modo Área ou Valor

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

# --- Horizontal-Zig-Zag (HZZ) ---
def horizontal_zig_zag_placement(permutation, container_w, container_h):
    placed_items = []

    total_area_ocupada = 0 # rastreia a área física
    total_valor_objeto = 0 # rastreia o valor (objetivo)

    for item in permutation:
        candidates = [(0, 0)]
        for p in placed_items:
            candidates.append((p['x'] + p['w'], p['y']))
            candidates.append((p['x'], p['y'] + p['h']))
        
        candidates.sort(key=lambda c: (c[1], c[0] if int(c[1]) % 2 == 0 else -c[0]))
        
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
                    placed_items.append({'id': item.id, 'x': cx, 'y': cy, 'w': item.w, 'h': item.h, 'v': item.v})

                    total_area_ocupada += item.area # sempre será <= área do container
                    total_valor_objeto += item.v # pode ser > que o container se o modo for valor


                    placed = True
                    break
    
    # Calcula quão longe as peças estão da origem (x=0, y=0)
    # Somamos a coordenada do topo-direito (x + w, y + h) de cada peça colocada
    dispersao = sum(p['x'] + p['w'] + p['y'] + p['h'] for p in placed_items)
    
    # Adicionamos a área total (que é o peso principal) 
    # E subtraímos um valor BEM PEQUENO da dispersão para servir apenas de desempate
    # Multiplicamos por 0.0001 para garantir que a área sempre seja mais importante que a compactação
    score_avaliacao = total_valor_objeto - (dispersao * 0.0001)

    # retorna 4 valores: score, itens colocados, área fisica e valor 
    return score_avaliacao, placed_items, total_area_ocupada, total_valor_objeto

# --- Recozimento Simulado (SA) ---
def recozimento_simulado(instance, t0=1000, alpha=0.95, iter_max=300):
    current_order = list(instance.items)
    # random.shuffle(current_order)
    current_order.sort(key=lambda x: x.area, reverse=True)
    current_eval, _, cur_area, cur_val = horizontal_zig_zag_placement(current_order, instance.W, instance.H)
    
    best_order = list(current_order)
    best_eval = current_eval

    best_area = cur_area # Guarda a melhor área física
    best_val = cur_val # guarda o melhor valor bruto

    
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
            nev, _, narea, nval = horizontal_zig_zag_placement(neighbor, instance.W, instance.H)
            
            delta = nev - current_eval
            
            # Critério de aceitação do Recozimento Simulado
            if delta > 0 or (t > 0 and random.random() < math.exp(delta / t)):
                current_order = neighbor
                current_eval = nev
                
                if current_eval > best_eval:

                    best_eval = nev
                    best_order = list(neighbor)
                    best_area = narea # <--- Atualiza com a área da melhor solução
                    best_val = nval   # <--- Atualiza com o valor da melhor solução
        
        if step % 5 == 0: # Printa a cada 5 reduções de temperatura
            print(f"    Passo {step} | Temp: {t:.2f} | Melhor Área: {best_eval}")
        
        t *= alpha
        step += 1
        
    return best_eval, best_order, best_area, best_val

# --- Leitura ---
def load_instance(filepath):

    with open(filepath, 'r') as f:
        lines = [line for line in f.readlines() if line.strip() and not line.startswith('#')]
        num_items = int(lines[0].split('#')[0].strip())
        cont_w, cont_h = map(int, lines[1].split('#')[0].strip().split())
        items = []
        tem_valor_real = False 

        
        for i in range(2, 2 + num_items):

            parts = list(map(int, lines[i].split()))
            w, h, v = parts[0], parts[1], parts[2]
            
            if v > 0: tem_valor_real = True # Se houver qualquer valor > 0, muda o modo

            items.append(Item(i-2, w, h, v))

            
    modo = "Valor" if tem_valor_real else "Área" # Define o rótulo baseado na detecção
    return Instance(os.path.basename(filepath), cont_w, cont_h, items, modo)

# --- Execução Principal ---
def main():
    # 1. Defina um identificador para essa rodada (ex: 'teste_T1000_A90')
    identificador_teste = "RS+HZZ-comparacao_geral"

    # 2. Cria a pasta com o identificador + data/hora
    pasta_teste = preparar_pasta(identificador_teste)

    # 3. Defina o caminho onde estão as instancias
    folder_path = './data/ins teste 4.0' 
    results_file = os.path.join(pasta_teste, 'resultsHzz.txt')

    # Define e cria subpasta de imagens
    pasta_imagens = os.path.join(pasta_teste, 'imagens')
    os.makedirs(pasta_imagens, exist_ok=True)
    
    if not os.path.exists(folder_path):
        print(f"Erro: Pasta {folder_path} não encontrada.")
        return
    
    # Definindo largura de cada coluna (ajustar caso necessario)
    w_nome = 13
    w_modo = 10
    w_dim = 14
    w_itens = 12
    w_obj = 15
    w_ocup = 19
    w_tempo = 10

    with open(results_file, 'w') as out:
        # Cabeçalho do resultado
        header = (
            f"{'Instancia':<{w_nome}} | "
            f"{'Tipo Valor':<{w_modo}} | "
            f"{'Dimensoes':<{w_dim}} | "
            f"{'Itens (E/T)':<{w_itens}} | "
            f"{'Valor Obj.':<{w_obj}} | "
            f"{'Ocupação':<{w_ocup}} | "
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
                best_score, best_order, area_final, valor_final = recozimento_simulado(inst)
                
                # Gera o resultado final com a melhor ordem encontrada
                _, final_placement, area_final, valor_final = horizontal_zig_zag_placement(best_order, inst.W, inst.H)

                # Calcula a quantidade de itens empacotados
                qtd_empacotados = len(final_placement)
                qtd_total = len(inst.items)
                
                end_time = time.time()
                duracao = end_time - start_time

                # Preparando strings complexas
                dimensoes = f"{inst.W}x{inst.H}"
                status_itens = f"{len(final_placement)}/{len(inst.items)}"

                                # Cálculo da string de ocupação: ex "145/150 (96.67%)"
                ocup_str = f"{area_final}/{inst.area_total_container}"
                ocup_perc = (area_final / inst.area_total_container) * 100
                ocup_full = f"{ocup_str} ({ocup_perc:.2f}%)"

                # --- Verificação/Depuração ---
                print(f"  [OK] Finalizado. Área: {valor_final} em {duracao:.2f}s")
                print(f"  [INFO] Lista de posições gerada pelo Bottom-Left (Top 5):")
                for p in final_placement[:5]:
                    print(f"    Item {p['id']}: pos({p['x']}, {p['y']}) dim({p['w']}x{p['h']})")

                # Define o caminho do salvamento da imagem
                caminho_img = os.path.join(pasta_imagens, f"layout_{inst.name}.png")
                
                # Gera imagem do resultado
                plot_solution(inst.W, inst.H, final_placement, inst.name, valor_final, caminho_img)
                print(f"  [IMG] Gráfico salvo como 'layout_{caminho_img}.png'")

                # Printa o resultado de cada instancia
                linha = (
                f"{inst.name:<{w_nome}} | "
                f"{inst.modo_calculo:<{w_modo}} | "
                f"{dimensoes:<{w_dim}} | "
                f"{status_itens:<{w_itens}} | "
                f"{valor_final:<{w_obj}} | "
                f"{ocup_full:<{w_ocup}} | "
                f"{duracao:<{w_tempo}}\n" 
                )

                out.write(linha)

if __name__ == "__main__":
    main()