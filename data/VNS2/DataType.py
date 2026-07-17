import math
from typing import List

# ==============================================================================
# CONSTANTES GLOBAIS
# ==============================================================================
BILLION = 1000000000.0  # Usado para conversão de tempo ou valores grandes
SHUFFLES = 1            # Número padrão de embaralhamentos
PI = 3.14159265359      # Valor de Pi para cálculos trigonométricos
ZERO = 0.00000001       # Uma quantidade infinitesimal para evitar divisões por zero

# ==============================================================================
# FUNÇÕES UTILITÁRIAS 
# ==============================================================================

def DEGREES_RADIANS(angle: float) -> float:
    """Converte um ângulo de graus para radianos."""
    return (angle / 180.0) * PI

def rotationX(x1: float, y1: float, radians: float) -> float:
    """Calcula a nova coordenada X de um ponto após uma rotação em radianos."""
    return (x1 * math.cos(radians)) - (y1 * math.sin(radians))

def rotationY(x1: float, y1: float, radians: float) -> float:
    """Calcula a nova coordenada Y de um ponto após uma rotação em radianos."""
    return (x1 * math.sin(radians)) + (y1 * math.cos(radians))


# ==============================================================================
# ESTRUTURAS DE DADOS (Classes)
# ==============================================================================

class Point_t:
    """Representa um ponto discreto (inteiro) em uma matriz (Linha e Coluna)."""
    def __init__(self, i: int = 0, j: int = 0):
        self.i = i  # Índice da Linha (Row)
        self.j = j  # Índice da Coluna (Column)

class RealPoint_t:
    """Representa um ponto contínuo (ponto flutuante) no espaço bidimensional (X e Y)."""
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x  # Coordenada X
        self.y = y  # Coordenada Y

class Discrete_t:
    """Representa uma matriz discreta 2D de inteiros representando a geometria de um item."""
    def __init__(self, I: int = 0, J: int = 0, m: List[List[int]] = None):
        self.I = I  # Número total de linhas
        self.J = J  # Número total de colunas
        # Se nenhuma matriz for passada, inicializa uma lista vazia
        self.m = m if m is not None else []

class Polygon_t:
    """Representa um polígono geométrico através da quantidade e lista de seus vértices."""
    def __init__(self, V: int = 0, vertex_v: List[Point_t] = None):
        self.V = V  # Quantidade de vértices
        self.vertex_v = vertex_v if vertex_v is not None else []

class Nofit_t:
    """Estrutura para armazenar o No-Fit Polygon (NFP) entre duas peças."""
    def __init__(self, refFix: Point_t = None, matrix: Discrete_t = None):
        self.refFix = refFix  # Ponto de referência de fixação
        self.matrix = matrix  # Matriz discreta representando a área de colisão (NFP)

class Recfit_t:
    """Representa o ajuste retangular minimalista (inner fit raster) de uma peça."""
    def __init__(self, refFix: Point_t = None, matrix: Discrete_t = None, scale: float = 0.0):
        self.refFix = refFix
        self.matrix = matrix
        self.scale = scale

class Piece_t:
    """Representa um tipo de peça (item) a ser acomodada no problema de corte/empacotamento."""
    def __init__(self):
        self.id: int = 0             # Identificador único da peça
        self.D: int = 0              # Demanda (quantidade de cópias necessárias desta peça)
        self.area: float = 0.0       # Área total da peça
        self.R: int = 0              # Quantidade de rotações permitidas para esta peça
        self.rotation_r: List[float] = []  # Lista com os ângulos de rotação permitidos (em graus)
        self.maxBox_r: List[Point_t] = []  # Caixa envolvente (bounding box) para cada rotação
        self.V: int = 0              # Número de vértices do polígono real
        self.vertex_v: List[RealPoint_t] = []  # Vértices da peça no formato contínuo
        self.pref_r: List[RealPoint_t] = []    # Vértice de referência para cada rotação
        self.rfr_r: List[Recfit_t] = []        # Ajuste retangular para cada rotação
        
        # Matriz 3D que armazena os NFPs (Grid de colisão) em relação a outras peças e rotações
        # nfpGrid_rpr[rotacao_da_peca_atual][id_da_outra_peca][rotacao_da_outra_peca] -> Nofit_t
        self.nfpGrid_rpr: List[List[List[Nofit_t]]] = []

class Container_t:
    """Representa o objeto recipiente (placa) onde as peças serão inseridas/cortadas."""
    def __init__(self):
        self.id: int = 0             # Identificador único do container
        self.H: float = 0.0          # Altura real do container (L)
        self.W: float = 0.0          # Largura real do container (C)
        self.matrix: Discrete_t = None # Representação em grade discreta do espaço do container

class Map_t:
    """Representa a grade de viabilidade (Inner-Fit) para posicionamento de cada peça."""
    def __init__(self):
        self.I: int = 0              # Dimensão de linhas da grade
        self.J: int = 0              # Dimensão de colunas da grade
        self.R: int = 0              # Número de rotações tratadas
        self.currSize: int = 0       # Tamanho corrente utilizado na lógica de posicionamento
        
        # Matriz 4D
        # m_prij[id_peca][id_rotacao][linha_i][coluna_j] -> 0 se livre/válido, 1 se ocupado/colisão
        self.m_prij: List[List[List[List[int]]]] = []

class DataType_t:
    """Classe centralizadora que armazena todos os dados lidos da instância do problema."""
    def __init__(self):
        self.PR: int = 0                  # Somatório de todas as rotações de todas as peças
        self.P: int = 0                   # Quantidade total de tipos de peças diferentes
        self.pieces: List[Piece_t] = []   # Lista contendo todas as definições de peças
        self.C: int = 0                   # Quantidade total de containers disponíveis
        self.containers: List[Container_t] = [] # Lista contendo os containers
        self.scale: float = 0.0           # Fator de escala da instância
        self.M: int = 0                   # Quantidade de mapas de viabilidade
        self.maps: List[Map_t] = []       # Lista contendo os mapas de posicionamento