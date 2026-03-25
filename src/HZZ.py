def h_zz_compacto(width, height):
    lp = []
    for y in range(height):
        linha = [(x, y) for x in range(width)]
        # Se for ímpar, inverte a lista daquela linha
        if y % 2 != 0:
            linha = linha[::-1]
        lp.extend(linha)
    return lp

pontos = h_zz_compacto(4, 3)
print(pontos)