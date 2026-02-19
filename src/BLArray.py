import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- 1. Estrutura de Dados (Vetores) ---
class Item:
    def __init__(self, id, w, h, val=0):
        self.id = id
        self.w = w
        self.h = h
        self.area = w * h

        self.value = val if val > 0 else self.area
        self.x = 0
        self.y = 0
        self.placed = False

# --- 2. O Motor Geométrico (Bottom-Left) ---
def check_collision(new_item, x, y, placed_items, H_MAX, W_MAX):
    if x + new_item.w > W_MAX or y + new_item.h > H_MAX:
        return True
    
    for item in placed_items:
        if (x < item.x + item.w and x + new_item.w > item.x and
            y < item.y + item.h and y + new_item.h > item.y):
            return True
    return False

def bottom_left_algorithm(items, W_CONTAINER, H_CONTAINER):
    placed_items = []
        
    for item in items:
        candidate_points = [(0, 0)]
        for p in placed_items:
            candidate_points.append((p.x + p.w, p.y))
            candidate_points.append((p.x, p.y + p.h))
            
        candidate_points.sort(key=lambda p: (p[1], p[0]))
        
        placed = False
        for x_cand, y_cand in candidate_points:
            if not check_collision(item, x_cand, y_cand, placed_items, H_CONTAINER, W_CONTAINER):
                item.x = x_cand
                item.y = y_cand
                item.placed = True
                placed_items.append(item)
                placed = True
        
        if not placed:
            print(f"Item {item.id} não coube.")

    return placed_items

# --- 3. Execução Simples ---

# Dimensões
W_MAX = 2097
H_MAX = 1713

# Dados
raw_data = [
    (738, 495, 0),   # Item real 1
    (126, 102, 0),   # Fictício
    (117, 273, 0),   # Fictício
    (818, 163, 0),  # Fictício
    (530, 585, 0)    # Fictício
]

# Criar objetos
lista_itens = [Item(i, w, h, v) for i, (w, h, v) in enumerate(raw_data)]

# --- Ordenação ---
# Ordena por Área Decrescente 
lista_itens.sort(key=lambda x: x.area, reverse=True)


itens_alocados = bottom_left_algorithm(lista_itens, W_MAX, H_MAX)

# --- 4. Visualização ---
fig, ax = plt.subplots(1)
ax.set_xlim(0, W_MAX)
ax.set_ylim(0, H_MAX)

rect = patches.Rectangle((0,0), W_MAX, H_MAX, linewidth=2, edgecolor='black', facecolor='none')
ax.add_patch(rect)

colors = ['red', 'green', 'blue', 'orange', 'purple', 'cyan']
for i, item in enumerate(itens_alocados):
    rect = patches.Rectangle((item.x, item.y), item.w, item.h, 
                             linewidth=1, edgecolor='black', facecolor=colors[i % len(colors)], alpha=0.6)
    ax.add_patch(rect)
    ax.text(item.x + item.w/2, item.y + item.h/2, f"ID {item.id}\n{item.w}x{item.h}", 
            ha='center', va='center', fontsize=8, color='white', weight='bold')

plt.gca().set_aspect('equal', adjustable='box')
plt.title(f"Bottom-Left por Área (Itens: {len(itens_alocados)})")
plt.show()