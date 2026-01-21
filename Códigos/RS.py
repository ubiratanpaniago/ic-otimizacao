import math
import random

def recozimento_simulado(funcao_objetivo, gerar_vizinho, solucao_inicial, alpha, n_iter, t0, tf):
    
    x_atual = solucao_inicial
    t_atual = t0

    x_otimo = x_atual
    f_x_otimo = funcao_objetivo(x_otimo)

    while t_atual > tf:

        i=0

        while i < n_iter:

            x1 = gerar_vizinho(x_atual)

            f_x_atual = funcao_objetivo(x_atual)
            f_x1 = funcao_objetivo(x1)
            
            delta_f = f_x1 - f_x_atual
            
            aceitou = False
            
            if delta_f <= 0:
                x_atual = x1
                aceitou = True
                
                if f_x1 < f_x_otimo:
                    x_otimo = x1
                    f_x_otimo = f_x1
            
            else:
                r = random.random() # Gera número aleatório entre 0 e 1
                probabilidade = math.exp(-delta_f / t_atual)
                
                if r < probabilidade:
                    x_atual = x1 # Linha 13
                    aceitou = True
            
            i += 1
            
        t_atual = t_atual * alpha
        
        # Opcional: Imprimir progresso
        # print(f"Temp: {t_atual:.4f} | Melhor Custo: {f_x_otimo:.4f}")

    return x_otimo

# --- EXEMPLO DE USO ---

# 1. Definir o problema: Minimizar a função f(x) = x^2 (O ótimo é 0)
# Vamos usar x^2 + uma perturbação para criar ótimos locais, simulando um problema real.
# Função: f(x) = x^2 - 10*cos(2*pi*x) 
def minha_funcao_objetivo(x):
    return (x**2) - 10 * math.cos(2 * math.pi * x)

# 2. Definir como gerar vizinhos (andar um pouco para a esquerda ou direita)
def gerar_vizinho(x):
    passo = random.uniform(-0.5, 0.5) # Tamanho do passo aleatório
    return x + passo

# 3. Parâmetros de entrada 
t0 = 100.0      # Temperatura alta inicial
tf = 0.001      # Temperatura final
alpha = 0.95    # Resfriamento lento (perto de 1)
n_iter = 50     # Iterações por temperatura
solucao_inicial = 10.0 # Começamos longe do zero

# Executar
resultado = recozimento_simulado(
    minha_funcao_objetivo, 
    gerar_vizinho, 
    solucao_inicial, 
    alpha, 
    n_iter, 
    t0, 
    tf
)

print(f"Solução Inicial: {solucao_inicial}")
print(f"Resultado Otimizado: {resultado:.5f}")
print(f"Valor da Função no Resultado: {minha_funcao_objetivo(resultado):.5f}")