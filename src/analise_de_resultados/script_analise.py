import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Mapear os arquivos para seus respectivos Alphas
# Substitua as chaves pelos nomes reais dos seus arquivos txt
arquivos_alpha = {
    'results/teste_T1000_A50_20260226_100927/resulttesteinst.txt': 0.50,
    'results/teste_T1000_A80_20260226_101303/resulttesteinst.txt': 0.80,
    'results/teste_T1000_A90_20260226_101326/resulttesteinst.txt': 0.90,
    'results/teste_T1000_A95_20260226_101356/resulttesteinst.txt': 0.95,
    'results/teste_T1000_A99_20260226_101420/resulttesteinst.txt': 0.99
}

t0_fixo = 1000 # Como a temperatura é fixa, definimos uma vez só
lista_dfs = []

# 2. Loop para ler cada arquivo e "carimbar" o Alpha correspondente
for nome_arquivo, valor_alpha in arquivos_alpha.items():
    try:
        # Lê o arquivo txt atual
        df_temp = pd.read_csv(nome_arquivo, sep=r'\s*\|\s*', engine='python')
        
        # Adiciona as colunas de Alpha e T0 para sabermos de onde vieram
        df_temp['Alpha'] = valor_alpha
        df_temp['T0'] = t0_fixo
        
        # Guarda a tabela temporária na nossa lista
        lista_dfs.append(df_temp)
        print(f"Arquivo {nome_arquivo} lido com sucesso!")
        
    except FileNotFoundError:
        print(f"Aviso: O arquivo {nome_arquivo} não foi encontrado na pasta.")

# 3. Junta todas as tabelas em um único DataFrame (tabela mestra)
df_completo = pd.concat(lista_dfs, ignore_index=True)

# --- Daqui para baixo, a análise continua igual! ---

# Gera a tabela de resumo com médias e melhores resultados
resumo = df_completo.groupby('Alpha').agg(
    Area_Maxima_Media=('Area Maxima', 'mean'),
    Area_Maxima_Melhor=('Area Maxima', 'max'),
    Tempo_Medio_s=('Tempo (s)', 'mean')
).reset_index()

print("\n=== TABELA RESUMO ===")
print(resumo.to_string(index=False))

# 4. Geração dos Gráficos Comparativos
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Gráfico da Área Máxima
sns.barplot(data=df_completo, x='Alpha', y='Area Maxima', ax=axes[0], capsize=.1, errorbar='sd', palette='viridis')
axes[0].set_title(f'Qualidade da Solução (T0 Fixo: {t0_fixo})')
axes[0].set_ylabel('Área Máxima')

# Gráfico do Tempo
sns.barplot(data=df_completo, x='Alpha', y='Tempo (s)', ax=axes[1], capsize=.1, errorbar='sd', palette='magma')
axes[1].set_title('Tempo de Execução')
axes[1].set_ylabel('Tempo (s)')

plt.tight_layout()
plt.savefig('comparacao_5_arquivos.png', dpi=300)