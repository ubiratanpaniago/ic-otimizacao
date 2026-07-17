import sys
import time
from DataType import DataType_t, Piece_t, Container_t, Point_t, RealPoint_t, Discrete_t, Nofit_t, Recfit_t, DEGREES_RADIANS, rotationX, rotationY
from Vns import Vns

# ==============================================================================
# DICIONÁRIO DE AMBIENTE GLOBAL 
# ==============================================================================
env = {
    'areaT': 0.0,       # Área total somada de todos os itens demandados
    'posC': [],         # Mapeamento do índice do item físico para o seu tipo conceitual
    'LA': 0.0,          # Limite Inferior de Ocupação Ideal (Lower Bound)
    'tempoExe': 1800.0, # Tempo máximo permitido para a execução do algoritmo (30 min padrão)
    'startt': 0.0,      # Carimbo de tempo do momento exato do início da execução
    'BKS': 0.0,         # Melhor solução conhecida da literatura (Best Known Solution)
    'nn': 0,            # Quantidade de espaços ou atrasos virtuais permitidos no sequenciamento
    'hf': {},           # Tabela Hash de memorização para cache de soluções avaliadas (Cache)
    'bSOL': []          # Armazena os dados físicos de posicionamento da melhor solução final
}

def get_tokens(filepath: str):
    """
    Função Geradora (Generator) Auxiliar.
    Abre um arquivo específico, limpa linhas de comentários (que começam com '#' ou '//')
    e entrega palavra por palavra (ou número por número) sob demanda usando o 'yield'.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                # Remove o texto que estiver após os marcadores de comentário '#' ou '//'
                clean_line = line.split('#')[0].split('//')[0]
                # Divide a linha limpa por espaços e entrega cada token individualmente
                for token in clean_line.split():
                    yield token
    except FileNotFoundError:
        print(f"Erro Crítico: O arquivo obrigatório '{filepath}' não foi encontrado.")
        sys.exit(-1)

# ==============================================================================
# OPERAÇÕES DE CONFIGURAÇÃO E EXECUÇÃO DO PROBLEMA
# ==============================================================================

def createMap(dt: DataType_t):
    """
    Cria e configura dinamicamente as matrizes 4D dos Mapas de posicionamento (Inner-Fit).
    """
    dt.M = dt.C
    dt.maps = [Map_t() for _ in range(dt.M)]
    
    for c in range(dt.C):
        dt.maps[c].I = dt.containers[c].matrix.I
        dt.maps[c].J = dt.containers[c].matrix.J
        dt.maps[c].R = dt.pieces[0].R if dt.pieces else 0
        
        P = dt.P
        R = dt.maps[c].R
        I = dt.maps[c].I
        J = dt.maps[c].J
        
        # ==============================================================================
        # Cria uma matriz 4D preenchida com o valor '1' (Representando indisponibilidade inicial)
        # ==============================================================================
        dt.maps[c].m_prij = [[[[1 for _ in range(J)] for _ in range(I)] for _ in range(R)] for _ in range(P)]
        
        # Define as caixas limítrofes operacionais da peça como livres (Valor 0)
        for p in range(dt.P):
            for r in range(dt.maps[c].R):
                # Calcula os limites de folga máxima para a movimentação
                delta_I = dt.containers[c].matrix.I - dt.pieces[p].maxBox_r[r].i + 1
                delta_J = dt.containers[c].matrix.J - dt.pieces[p].maxBox_r[r].j + 1
                for i in range(delta_I):
                    for j in range(delta_J):
                        dt.maps[c].m_prij[p][r][i][j] = 0  # 0 significa posição viável livre
                        
        dt.maps[c].currSize = dt.maps[c].J + 1

def readData(dt: DataType_t, fPiece: str, grupo: str):
    """
    Lê sequencialmente todos os arquivos que compõem a instância do problema:
    1. general_data.in (Dados gerais, demandas e rotações das peças)
    2. pieces.in       (Vértices geométricos e matrizes discretas de cada peça)
    3. container.in    (Dimensões físicas e malha de ocupação do container)
    4. nfp.in          (Grides de No-Fit Polygon para detecção de colisões)
    """
    # Define a pasta base da instância
    base_path = f"../STRIP/{fPiece}"
    
    # ==========================================================================
    # 1. LEITURA DO ARQUIVO: general_data.in
    # ==========================================================================
    tokens_gen = get_tokens(f"{base_path}/general_data.in")
    
    try:
        # Lê o fator de escala e a quantidade de tipos de peças (P)
        dt.scale = float(next(tokens_gen))
        dt.P = int(next(tokens_gen))
        
        # Aloca a lista de objetos das peças
        dt.pieces = [Piece_t() for _ in range(dt.P)]
        
        # Loop para ler os dados de cabeçalho de cada tipo de peça
        for p in range(dt.P):
            dt.pieces[p].id = int(next(tokens_gen))
            dt.pieces[p].D = int(next(tokens_gen))   # Demanda da peça
            flip = int(next(tokens_gen))             # Dado de espelhamento (se houver)
            dt.pieces[p].R = int(next(tokens_gen))   # Número de rotações permitidas
            dt.PR += dt.pieces[p].R                  # Acumulador global de rotações
            
            # Inicializa as listas internas que dependem da quantidade de rotações (R)
            dt.pieces[p].rotation_r = [float(next(tokens_gen)) for _ in range(dt.pieces[p].R)]
            dt.pieces[p].maxBox_r = [Point_t() for _ in range(dt.pieces[p].R)]
            dt.pieces[p].pref_r = [RealPoint_t() for _ in range(dt.pieces[p].R)]
            dt.pieces[p].rfr_r = []  # Será preenchida no próximo arquivo

        # Lê a quantidade de containers disponíveis
        dt.C = int(next(tokens_gen))
        dt.containers = [Container_t() for _ in range(dt.C)]
        
        # Lê os identificadores de cópias de cada container
        for c in range(dt.C):
            dt.containers[c].id = int(next(tokens_gen))
            copy = int(next(tokens_gen))
            
    except StopIteration:
        print("Erro: O arquivo 'general_data.in' terminou antes do esperado.")
        return

    # ==========================================================================
    # 2. LEITURA DO ARQUIVO: pieces.in (Vértices e Matrizes de Raster das Peças)
    # ==========================================================================
    tokens_pieces = get_tokens(f"{base_path}/pieces.in")
    
    try:
        for p in range(dt.P):
            # Lê a quantidade de vértices reais da peça e armazena suas coordenadas contínuas
            dt.pieces[p].V = int(next(tokens_pieces))
            dt.pieces[p].vertex_v = []
            for _ in range(dt.pieces[p].V):
                vx = float(next(tokens_pieces))
                vy = float(next(tokens_pieces))
                dt.pieces[p].vertex_v.append(RealPoint_t(vx, vy))
            
            # Para cada rotação permitida da peça, lê a sua respectiva matriz de pontos (Grid Raster)
            for r in range(dt.pieces[p].R):
                rows_I = int(next(tokens_pieces))
                cols_J = int(next(tokens_pieces))
                
                # Monta a matriz binária 2D usando compreensão de lista (List Comprehension)
                matrix_2d = [[int(next(tokens_pieces)) for _ in range(cols_J)] for _ in range(rows_I)]
                
                # Instancia o objeto de ajuste retangular e adiciona à peça
                discrete_geo = Discrete_t(rows_I, cols_J, matrix_2d)
                dt.pieces[p].rfr_r.append(Recfit_t(refFix=Point_t(0, 0), matrix=discrete_geo, scale=dt.scale))
                
    except StopIteration:
        print("Erro: O arquivo 'pieces.in' terminou antes de ler todas as geometrias.")
        return


    calculateBox(dt)  # Calcula as caixas envolventes e pontos de referência para cada peça e rotação
    # ==========================================================================
    # 3. LEITURA DO ARQUIVO: container.in (Dimensões e Matriz do Container)
    # ==========================================================================
    tokens_container = get_tokens(f"{base_path}/container.in")
    
    try:
        for c in range(dt.C):
            # Lê a altura (H) e a largura (W) reais do recipiente
            dt.containers[c].H = float(next(tokens_container))
            dt.containers[c].W = float(next(tokens_container))
            
            # Lê as dimensões da grade discreta do container
            rows_I = int(next(tokens_container))
            cols_J = int(next(tokens_container))
            
            # Carrega a matriz binária de ocupação inicial do container
            matrix_2d = [[int(next(tokens_container)) for _ in range(cols_J)] for _ in range(rows_I)]
            dt.containers[c].matrix = Discrete_t(rows_I, cols_J, matrix_2d)
            
    except StopIteration:
        print("Erro: O arquivo 'container.in' terminou inesperadamente.")
        return

    # ==========================================================================
    # 4. LEITURA DO ARQUIVO: nfp.in (Grides de No-Fit Polygons para Colisões)
    # ==========================================================================
    tokens_nfp = get_tokens(f"{base_path}/nfp.in")
    
    try:
        for p1 in range(dt.P):
            # Inicializa a estrutura da matriz 3D vazia para os NFPs da peça atual:
            # [id_rotacao_p1][id_outra_peca_p2][id_rotacao_p2]
            dt.pieces[p1].nfpGrid_rpr = [
                [[None for _ in range(dt.pieces[p2].R)] for p2 in range(dt.P)] 
                for _ in range(dt.pieces[p1].R)
            ]
            
            # Varre todas as combinações possíveis de rotações e peças concorrentes
            for r1 in range(dt.pieces[p1].R):
                for p2 in range(dt.P):
                    for r2 in range(dt.pieces[p2].R):
                        # Lê os pontos de referência de acoplamento fixo (i, j) do NFP
                        ref_i = int(next(tokens_nfp))
                        ref_j = int(next(tokens_nfp))
                        
                        # Lê o tamanho da matriz do NFP correspondente a esse par
                        nfp_rows = int(next(tokens_nfp))
                        nfp_cols = int(next(tokens_nfp))
                        
                        # Constrói a matriz de colisão 2D
                        matrix_2d = [[int(next(tokens_nfp)) for _ in range(nfp_cols)] for _ in range(nfp_rows)]
                        
                        # Vincula o NFP calculado ao espaço tridimensional indexado da peça
                        nfp_discrete = Discrete_t(nfp_rows, nfp_cols, matrix_2d)
                        dt.pieces[p1].nfpGrid_rpr[r1][p2][r2] = Nofit_t(refFix=Point_t(ref_i, ref_j), matrix=nfp_discrete)
                        
    except StopIteration:
        print("Erro: O arquivo 'nfp.in' terminou antes de mapear todas as combinações de colisão.")
        return

    print("-> Sucesso: Todos os arquivos da instância foram lidos e processados corretamente!")


def new_polygon(vertices: list, rotation_degrees: float, flip: int) -> list:
    """
    Recebe os vértices originais de uma peça e gera uma nova lista de vértices
    aplicando espelhamento (flip) e rotação trigonométrica.
    """
    new_vertices = []
    # Converte o ângulo de graus para radianos (necessário para o math.cos e math.sin)
    theta = DEGREES_RADIANS(rotation_degrees)
    
    for v in vertices:
        x = v.x
        y = v.y
        
        # Aplica o espelhamento (Flip) invertendo o eixo X
        if flip == 1:
            x = -x
            
        # Calcula as novas coordenadas usando as matrizes de rotação 2D
        nx = rotationX(x, y, theta)
        ny = rotationY(x, y, theta)
        
        # Arredonda para 6 casas decimais para evitar lixo de memória do ponto flutuante 
        # Exemplo: evitar que um 0.0 vire 0.00000000000000012
        nx = round(nx, 6)
        ny = round(ny, 6)
        
        # Cria um novo ponto real e adiciona à lista
        new_vertices.append(RealPoint_t(nx, ny))
        
    return new_vertices


def calculateBox(dt: DataType_t):
    """
    Calcula a 'Envoltória Retangular' (Bounding Box - maxBox_r) de todas as peças 
    para cada uma de suas rotações permitidas. Também encontra o vértice de 
    referência (pref_r), que é o ponto mais abaixo e à esquerda.
    """
    for p in range(dt.P):
        # A propriedade flip precisa estar na classe Piece_t (ou ser extraída, aqui assumimos 0 se não salva)
        # Se você não salvou o flip no readData, assumiremos 0 como padrão de corte simples.
        flip = 0 
        
        for r in range(dt.pieces[p].R):
            # 1. Pega o ângulo de rotação específico desta iteração
            rot_angle = dt.pieces[p].rotation_r[r]
            
            # 2. Gera os vértices rotacionados baseados nos vértices contínuos originais
            aux = new_polygon(dt.pieces[p].vertex_v, rot_angle, flip)
            
            # Inicializa os limites com infinito para garantir que sejam sobrescritos
            minX, minY = float('inf'), float('inf')
            maxX, maxY = float('-inf'), float('-inf')
            
            # Inicializa as referências do menor ponto
            pref_x, pref_y = float('inf'), float('inf')
            
            # 3. Varre os vértices rotacionados para descobrir os extremos (Bounding Box)
            for v in aux:
                # Atualiza limites da caixa
                if v.x < minX: minX = v.x
                if v.x > maxX: maxX = v.x
                if v.y < minY: minY = v.y
                if v.y > maxY: maxY = v.y
                
                # Atualiza o Ponto de Referência: regra do 'Menor Y, em caso de empate, menor X'
                if v.y < pref_y:
                    pref_y = v.y
                    pref_x = v.x
                # Verifica empate no Y usando uma pequena tolerância (1e-6) para lidar com floats
                elif abs(v.y - pref_y) < 1e-6:
                    if v.x < pref_x:
                        pref_x = v.x
                        
            # 4. Salva a largura (j) e altura (i) discreta da envoltória retangular
            # O cast para 'int' com 'round' garante que caiba no grid (m_prij) perfeitamente
            dt.pieces[p].maxBox_r[r].j = int(round(maxX - minX))
            dt.pieces[p].maxBox_r[r].i = int(round(maxY - minY))
            
            # 5. Salva o ponto de referência calculado
            dt.pieces[p].pref_r[r].x = pref_x
            dt.pieces[p].pref_r[r].y = pref_y


# ==============================================================================
# FUNÇÃO PRINCIPAL DE INICIALIZAÇÃO (Ponto de entrada do script)
# ==============================================================================

def main():
    # Validação mínima de argumentos via linha de comando
    #print("Exemplo: python Main.py\n")

    #nome da instancia
    instancia = 'fu'
    
    print(f"--------- Processando Instância: {instancia} ---------")
    
    dt = DataType_t()
    
    # Faz a leitura da instância e criação dos mapas operacionais
    readData(dt, instancia)
    createMap(dt)
    
    # Organiza a listagem física sequencial de itens com base em suas demandas D
    num = 0
    for p in range(dt.P):
        num += dt.pieces[p].D
        for _ in range(dt.pieces[p].D):
            env['posC'].append(p)
            
    C = dt.C - 1
    
    # Calcula a soma total de área de todas as peças do problema
    for i in range(dt.P):
        env['areaT'] += dt.pieces[i].area * dt.pieces[i].D
        
    # Calcula a ocupação limite teórica ideal (Lower Bound)
    if dt.containers and dt.containers[C].H > 0:
        env['LA'] = env['areaT'] / (dt.containers[C].H * dt.containers[C].W)
    else:
        env['LA'] = 0.5  # Valor padrão de contingência para testes rápidos
    
    # Inicializa o resolvedor Metaheurístico VNS
    alg = Vns(dt, num, env)
    
    iSEM = 150       # Critério de estagnação (iterações sem melhorias)
    NG = 5000        # Número máximo total de gerações permitidas
    iter_count = 0   # Contador de gerações corrente
    bestG = 0        # Geração em que ocorreu a última melhoria real
    icon = 0         # Contador corrente de estagnação
    
    # Inicia o cronômetro preciso de execução do Python
    env['startt'] = time.monotonic()
    
    alg.start()
    print("-> Geração da Solução Inicial Concluída com Sucesso.")
    
    alg.K = 2  # Define o limite operacional de vizinhanças ativas
    
    # Loop de execução principal do ciclo evolutivo do VNS
    while icon <= iSEM and iter_count <= NG and not alg.stop():
        k = 1
        while k <= alg.K and not alg.stop():
            csol = list(alg.order)  # Salva um backup da sequência atual
            cSOL = alg.cSol         # Salva o custo associado atual
            
            alg.shake(k)            # Aplica perturbação na solução (Chacoalhada)
            alg.VND()               # Dispara a busca refinada local (VND)
            
            if alg.cSol >= cSOL:
                # Se a mudança não trouxe ganhos reais, desfaz a alteração e avança a vizinhança
                alg.order = list(csol)
                alg.cSol = cSOL
                k += 1
                icon += 1
            else:
                # Se encontrou melhoria, imprime o feedback e reseta para a vizinhança k=1
                print(f" -> [Melhoria Detectada] Alcançada na vizinhança k: {k}")
                k = 1
                bestG = iter_count
                icon = 0
                
        iter_count += 1

    # Registra o tempo final decorrido
    TT = time.monotonic() - env['startt']
    
    print("\n=================== RESULTADOS FINAIS ===================")
    print(f"Melhor Eficiência de Ocupação Obtida: {-alg.bestSol * 100:.2f}%")
    print(f"Iteração da melhor solução: {bestG}")
    print(f"Tempo Total Consumido: {TT:.4f} segundos")
    print("=========================================================\n")

if __name__ == "__main__":
    main()