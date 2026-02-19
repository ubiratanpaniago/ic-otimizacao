'''
lanche = ['pizza','chocolate']
lanche[1]='picole'
lanche.append('cookie')
lanche.insert(0,'hotdog')
print(lanche[0])
print(lanche[1])
print(lanche[2])
'''

'''
valores = []
for cont in range(0,4):
    valores.append(int(input('Digite um valo: ')))

for c, v in enumerate(valores):
    print(f'Na posição {c} encontrei o valor {v} !')
print('Cheguei no final paizao')
'''
'''
a = [2, 3, 7, 9]
b = a[:] # recebendo copia dos valores de a
#b = a # foi criada uma ligação entre as listas
b[2]= 8
print(f'lista a = {a}')
print(f'lista b = {b}')
'''

lista = []
mai = 0
men = 0
for c in range(0, 5):
    lista.append(int(input(f'Digite um valor para a Posição {c}:')))
    if c == 0:
        mai = men = lista[c]
    else:
        if lista[c] > mai:
            mai = lista[c]
        if lista[c] < men:
            men = lista[c]


print('=-' * 30)
print(f'Você digitou os seguintes valores {lista}')
print(f'O maior valor digitado foi {mai}')
print(f'O menor valor digitado foi {men}')