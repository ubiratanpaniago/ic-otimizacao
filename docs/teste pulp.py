from pulp import *
#import pulp as p

# Inicializando classe
model = LpProblem("Maximize Bakery Profits", LpMinimize)

# Definindo variaveis de decisão
A =LpVariable('A', lowBound=0)

#B =LpVariable('B', lowBound=0)

# Definindo objetivo da função
model += 4 * A + 2 * B

# Definindo restrições
model += 20 * A + 5 * B >= 60
model += 10 * A + 10 * B >= 40


# Resolvendo
model.solve()
print("Producao de Bolos A e {}". format(A.varValue))
print("Producao de Bolos B e {}". format(B.varValue))