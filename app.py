dados = []

with open('ed1.txt', 'r', encoding='utf=8') as arquivo:
    for linha in arquivo:
        linha_limpa = linha.strip()

        if linha_limpa:
            dados.append(linha_limpa)

print(dados)