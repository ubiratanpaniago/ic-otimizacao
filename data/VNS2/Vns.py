import time
import math
import random
from DataType import DataType_t, Piece_t, Point_t, RealPoint_t

class Vns:
    """
    Classe que implementa o algoritmo Metaheurístico VNS (Variable Neighborhood Search)
    integrado com regras de posicionamento heurístico para o problema de empacotamento.
    """
    def __init__(self, data: DataType_t, num: int, env_globals: dict):
        """
        Construtor da classe VNS.
        :param data: Objeto DataType_t com os dados da instância.
        :param num: Quantidade total de peças considerando suas demandas.
        :param env_globals: Dicionário compartilhado representando as variáveis globais.
        """
        self.dt = data
        self.c = 0              # Índice do container atual que está sendo preenchido
        self.env = env_globals  # Armazena a referência para o dicionário global

        # Coleta as dimensões do mapa para simplificar a legibilidade
        P = self.dt.P
        R = self.dt.maps[self.c].R if self.dt.maps else 0
        I = self.dt.maps[self.c].I if self.dt.maps else 0
        J = self.dt.maps[self.c].J if self.dt.maps else 0

        # ==============================================================================
        # Criação de uma matriz 4D (Lista de listas de listas de listas) cheia de zeros.
        # Estrutura: map_prij[peca][rotacao][linha][coluna]
        # ==============================================================================
        self.map_prij = [[[[0 for _ in range(J)] for _ in range(I)] for _ in range(R)] for _ in range(P)]
        
        # Parâmetros de controle e estatísticas da busca do VNS
        self.numPieces = num          # Número total de itens físicos reais
        self.wMax = 15                # Tentativas máximas de perturbação em uma vizinhança
        self.bestSol = 0.0            # Valor da melhor solução encontrada (fração de ocupação negativa)
        self.bestAT = 0.0             # Área total combinada das peças empacotadas na melhor solução
        self.it = 0                   # Contador de iterações gerais
        self.bestHH = -1              # Índice da melhor heurística de posicionamento encontrada
        self.bestIT = 0               # Quantidade de itens acomodados na melhor solução
        self.bestTime = 0.0           # Tempo em segundos em que a melhor solução foi encontrada
        
        self.hitH = [0, 0, 0]         # Contador de sucesso de cada uma das 3 heurísticas de posicionamento
        self.K = 4                    # Quantidade máxima de estruturas de vizinhança (Neighborhoods)
        self.order = []               # Cromossomo/Vetor de permutação que dita a ordem de empacotamento das peças
        self.cSol = 0.0               # Valor da função objetivo para a solução corrente

    def start(self):
        """Gera uma solução inicial aleatória para o VNS."""
        # Cria a lista sequencial contendo os índices das peças e espaços fictícios (nn)
        self.order = list(range(self.numPieces))
        random.shuffle(self.order)  # Embaralha aleatoriamente a sequência
        self.decode()               # Avalia a qualidade dessa sequência aleatória

    def stop(self) -> bool:
        """Verifica se os critérios de parada do algoritmo foram atingidos (Tempo limite ou Meta alcançada)."""
        TT = time.monotonic() - self.env['startt']
        # Retorna True se o algoritmo deve parar (estourou o tempo de execução)
        return not (TT <= self.env['tempoExe'])

    def decode(self):
        """
        Decodifica a permutação atual (self.order) em uma solução real de empacotamento.
        Executa a posicionamento baseadas em grades (Bottom left).
        """
        c = self.c
        maxOpc = 0.0
        nItems = 0
        heur = 1  # Define a heurística de posicionamento a ser utilizada (1 = Bottom-Left)

        # Restaura a matriz de viabilidade de trabalho a partir do mapa original limpo
        for p in range(self.dt.P):
            for r in range(self.dt.maps[c].R):
                for i in range(self.dt.maps[c].I):
                    for j in range(self.dt.maps[c].J):
                        self.map_prij[p][r][i][j] = self.dt.maps[c].m_prij[p][r][i][j]
                        
        sol = []
        
        # Varre a sequência de peças 
        for k in range(len(self.order)):
                
            p = self.order[k]  # Recupera o tipo da peça
            rot = k % self.dt.maps[c].R          # Define uma rotação inicial padrão
            i_pos, j_pos, r_pos = -1, -1, -1
            
            # --------------------------------------------------------------------------
            # DIRETRIZ HEURÍSTICA 1: Bottom-Left (BL) Rule
            # Procura a primeira posição livre de baixo para cima, da esquerda para a direita
            # --------------------------------------------------------------------------
            if heur == 1:
                minL = self.dt.maps[c].J;
                for b in range(self.dt.maps[c].J):
                    for a in range(self.dt.maps[c].I):
                        for e in range(self.dt.maps[c].R):
                            ROT = (rot + e) % self.dt.maps[c].R
                            if self.map_prij[p][ROT][a][b] == 0:  # Encontrou espaço válido (0 = Livre)
                                end = self.dt.pieces[p].maxBox_r[ROT].j
                                if minL > j + end:
                                    minL = j + end
                                    r_pos, i_pos, j_pos = ROT, a, b
            
            # Se uma posição válida foi encontrada, acomoda a peça e atualiza as grades de colisão
            if i_pos >= 0 and j_pos >= 0:
                sol.append((p, r_pos, j_pos, i_pos))
                maxOpc += self.dt.pieces[p].area
                nItems += 1
                
                end = self.dt.pieces[p].maxBox_r[r_pos].j
                if maxL < j + end:
                    maxL = j + end

                # Atualiza a matriz 4D aplicando o No-Fit Polygon (NFP) para interditar posições sobrepostas
                for p2 in range(self.dt.P):
                    for r2 in range(self.dt.pieces[p2].R):
                        nfp = self.dt.pieces[p].nfpGrid_rpr[r_pos][p2][r2]
                        start_a = max(0, -nfp.refFix.i + i_pos)
                        end_a = nfp.matrix.I + (-nfp.refFix.i + i_pos)
                        for a in range(start_a, end_a):
                            start_b = max(0, -nfp.refFix.j + j_pos)
                            end_b = nfp.matrix.J + (-nfp.refFix.j + j_pos)
                            for b in range(start_b, end_b):
                                # Se o grid do NFP indicar colisão (> 0), marca a posição como inválida (1)
                                if nfp.matrix.m[a + nfp.refFix.i - i_pos][b + nfp.refFix.j - j_pos] > 0:
                                    if a < self.dt.maps[c].I and b < self.dt.maps[c].J:
                                        self.map_prij[p2][r2][a][b] = 1
            else:
                # Se a peça
                maxL += maxL
        
        # Se encontrou um novo recorde global de melhor preenchimento, salva a solução
        if self.bestSol > maxL:
            self.bestSol = maxL
            self.bestAT = maxOpc/(self.dt.containers[c].H * maxL)
            self.bestIT = nItems
            
            TT = time.monotonic() - self.env['startt']
            self.bestTime = TT
                
            print(f"Nova Melhor Solução: {self.bestSol} | Tempo: {TT:.2f}s")
            self.env['bSOL'] = sol
        
        self.cSol = maxL  # Guarda a melhor largura 

    # ==============================================================================
    # ESTRUTURAS DE VIZINHANÇA (Movimentos de Perturbação / Shake)
    # ==============================================================================

    def nb1(self) -> bool:
        """Vizinhança 1 (Swap): Sorteia duas posições do vetor de ordem e inverte seus valores."""
        j1 = random.randint(0, len(self.order) - 1)
        j2 = random.randint(0, len(self.order) - 1)
        if j1 == j2: 
            return True  # Movimento redundante inválido
        self.order[j1], self.order[j2] = self.order[j2], self.order[j1]
        return False

    def nb2(self) -> bool:
        """Vizinhança 2 (Insert): Remove uma peça de uma posição e a insere em outra posição aleatória."""
        j1 = random.randint(0, len(self.order) - 1)
        j2 = random.randint(0, len(self.order) - 1)
        if j1 == j2: 
            return True
        if j1 + 1 == j2:
            self.order[j1], self.order[j2] = self.order[j2], self.order[j1]
            return False
            
        jj = self.order.pop(j1)  # Remove do índice j1
        if j1 < j2:
            self.order.insert(j2 - 1, jj)
        else:
            self.order.insert(j2, jj)
        return False

    def shake(self, k: int):
        """Aplica uma perturbação vigorosa dependendo do nível de vizinhança atual (k)."""
        cc = 0
        if k == 1:
            while self.nb1() and cc < self.wMax: 
                cc += 1
        elif k == 2:
            while self.nb2() and cc < self.wMax: 
                cc += 1
        self.decode()  # Recalcula e avalia o impacto da mudança provocada

    def VND(self):
        """Algoritmo de Descida em Vizinhança Variável (Variable Neighborhood Descent)."""
        k = 1
        while k <= self.K:
            cS = self.cSol
            self.localVND(k)
            if self.cSol < cS:
                k = 1  # Se melhorou a solução, retorna para a primeira vizinhança básica
            else:
                k += 1 # Caso contrário, tenta uma vizinhança mais agressiva
            if self.stop(): 
                return

    def localVND(self, k: int):
        """Direciona qual busca local executar com base em k."""
        if k == 1: self.nb1LS()
        elif k == 2: self.nb2LS()

    def nb1LS(self):
        """Busca Local de varredura completa usando trocas posicionais (Swap Local Search)."""
        csol = list(self.order)
        cS = self.cSol
        flag, bS = False, self.cSol
        bj1, bj2 = 0, 0
        
        for j1 in range(len(self.order)):
            for j2 in range(len(self.order)):
                if j1 != j2:
                    self.order[j1], self.order[j2] = self.order[j2], self.order[j1]
                    self.decode()
                    if self.cSol < bS:
                        flag, bj1, bj2, bS = True, j1, j2, self.cSol
                    self.order = list(csol)  # Desfaz o movimento para continuar testando
                    self.cSol = cS
                    if self.stop(): return
                    
        if flag:
            self.order[bj1], self.order[bj2] = self.order[bj2], self.order[bj1]
            self.cSol = bS

    def nb2LS(self):
        """Busca Local baseada em inserção (Insert Local Search)."""
        pass  # Implementação análoga estruturada sob fatiamentos (pop/insert)