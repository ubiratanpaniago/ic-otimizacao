import math
import random

# ==============================
# Recozimento Simulado Completo
# ==============================

"""
Parâmetros:
F (func): função objetivo F(x)
gerar_vizinho (func): função que gera um X_l na vizinhança de X
X_inicial: solução inicial
T0 (float): temperatura inicial
Tf (float): temperatura final
alpha (float): coeficiente de resfriamento (0 < alpha < 1)
N_iter (int): iterações internas por temperatura
"""

def simulated_annealing(F, gerar_vizinho, X_inicial, T0, Tf, alpha, N_iter):
    X = X_inicial
    T = T0
    X_otimo = X

    while T > Tf:
        I = 0

        while I < N_iter:
            X_l = gerar_vizinho(X)
            deltaF = F(X_l) - F(X)

            if deltaF <= 0:
                X = X_l
            else:
                r = random.random()
                if r < math.exp(-deltaF / T):
                    X = X_l

            if F(X) < F(X_otimo):
                X_otimo = X

            I += 1

        T = alpha * T

    return X_otimo


# ==============================
# Exemplo simples: minimizar f(x) = x²
# ==============================

def F(x): return x**2 + 10*math.sin(x)



def gerar_vizinho(x):
    return x + random.uniform(-1, 1)

# Solução inicial
X_inicial = random.uniform(-10, 10)

# Execução
solucao = simulated_annealing(
    F=F,
    gerar_vizinho=gerar_vizinho,
    X_inicial=X_inicial,
    T0=100,
    Tf=0.001,
    alpha=0.95,
    N_iter=100
)

print("Melhor solução encontrada:", solucao)
print("Valor da função:", F(solucao))
