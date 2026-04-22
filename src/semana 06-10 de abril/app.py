import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
import time

# Importando as classes e métodos da lógica original
from RS_BL_Rot import Item, Instance, recozimento_simulado, bottom_left_placement

st.set_page_config(page_title="Otimização 2D - Bin Packing", layout="wide")

def plot_solution_streamlit(container_w, container_h, placed_items, instance_name, area_total):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, container_w)
    ax.set_ylim(0, container_h)
    ax.set_aspect('equal')
    
    rect_container = patches.Rectangle((0, 0), container_w, container_h, linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(rect_container)
    
    for p in placed_items:
        color = [random.random() for _ in range(3)]
        rect = patches.Rectangle((p['x'], p['y']), p['w'], p['h'], linewidth=1, edgecolor='white', facecolor=color, alpha=0.7)
        ax.add_patch(rect)
        ax.text(p['x'] + p['w']/2, p['y'] + p['h']/2, str(p['id']), fontsize=10, ha='center', va='center', color='black', weight='bold')

    plt.title(f"Instância: {instance_name}\nValor Final Otimizado: {area_total}")
    return fig

st.title("📦 Otimizador de Empacotamento 2D (Bin Packing)")
st.markdown("Utiliza **Recozimento Simulado** combinado com **Bottom-Left** e **Rotação de Peças**.")

# --- Sidebar: Parâmetros ---
st.sidebar.header("Parâmetros do Recozimento Simulado")
t0 = st.sidebar.number_input("Temperatura Inicial (T0)", min_value=1.0, value=1000.0, step=10.0)
alpha = st.sidebar.slider("Fator de Resfriamento (Alpha)", min_value=0.80, max_value=0.99, value=0.95, step=0.01)
iter_max = st.sidebar.number_input("Iterações por Passo", min_value=1, value=300, step=10)

# --- Entrada de Itens ---
st.subheader("Carregamento de Instâncias")
st.info("Otimize diversos arquivos de uma só vez. As dimensões de cada contêiner serão lidas automaticamente de dentro dos arquivos!")

# Inicializar o session_state
if "resultados_otimizacao" not in st.session_state:
    st.session_state.resultados_otimizacao = {}
if "nomes_instancias" not in st.session_state:
    st.session_state.nomes_instancias = []

uploaded_files = st.file_uploader("Envie os arquivos de instâncias (.txt)", type=["txt"], accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 Executar Otimização em Lote", type="primary"):
        # Limpar estado anterior
        st.session_state.resultados_otimizacao = {}
        st.session_state.nomes_instancias = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, uploaded_file in enumerate(uploaded_files):
            nome_instancia = uploaded_file.name
            status_text.text(f"Processando {nome_instancia} ({idx+1}/{len(uploaded_files)})...")
            
            content = uploaded_file.getvalue().decode("utf-8").splitlines()
            try:
                lines = [line for line in content if line.strip() and not line.startswith('#')]
                num_items = int(lines[0].split('#')[0].strip())
                file_cont_w, file_cont_h = map(int, lines[1].split('#')[0].strip().split())
                
                items_list = []
                tem_valor_real = False
                for i in range(2, 2 + num_items):
                    parts = list(map(int, lines[i].split()))
                    w, h, v = parts[0], parts[1], parts[2]
                    if v > 0: tem_valor_real = True
                    items_list.append(Item(i-2, w, h, v))
                    
                modo_calculo = "Valor" if tem_valor_real else "Área"
                
                inst = Instance(nome_instancia, file_cont_w, file_cont_h, items_list, modo_calculo)
                
                start_time = time.time()
                best_score, best_order, area_final, valor_final = recozimento_simulado(
                    inst, t0=t0, alpha=alpha, iter_max=iter_max
                )
                _, final_placement, area_final, valor_final = bottom_left_placement(
                    best_order, inst.W, inst.H
                )
                end_time = time.time()
                duracao = end_time - start_time
                
                st.session_state.resultados_otimizacao[nome_instancia] = {
                    "inst": inst,
                    "final_placement": final_placement,
                    "area_final": area_final,
                    "valor_final": valor_final,
                    "duracao": duracao,
                    "modo_calculo": modo_calculo
                }
                st.session_state.nomes_instancias.append(nome_instancia)
                
            except Exception as e:
                st.error(f"Erro ao processar o arquivo {nome_instancia}: {e}")
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
            
        status_text.success("✅ Otimização em Lote Concluída!")
        
# --- Visualização de Resultados ---
if st.session_state.nomes_instancias:
    st.divider()
    st.subheader("Resultados da Otimização")
    
    # st.segmented_control (requer Streamlit 1.40+ ou st.radio horizontal como fallback)
    instancia_selecionada = None
    try:
        instancia_selecionada = st.segmented_control(
            "Selecione a instância para visualizar", 
            st.session_state.nomes_instancias, 
            default=st.session_state.nomes_instancias[0]
        )
    except AttributeError:
        # Fallback caso a versão do Streamlit local não suporte segmented_control
        instancia_selecionada = st.radio(
            "Selecione a instância para visualizar", 
            st.session_state.nomes_instancias, 
            horizontal=True
        )
    
    if instancia_selecionada:
        dados = st.session_state.resultados_otimizacao[instancia_selecionada]
        inst = dados["inst"]
        area_final = dados["area_final"]
        valor_final = dados["valor_final"]
        duracao = dados["duracao"]
        final_placement = dados["final_placement"]
        
        st.write(f"**Dimensões do Contêiner:** {inst.W} x {inst.H} | **Modo de Otimização:** {dados['modo_calculo']}")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Valor/Área Total Otimizado", f"{valor_final}")
        col2.metric("Área Ocupada Fisicamente", f"{area_final} / {inst.area_total_container}")
        
        ocupacao_percentual = (area_final / inst.area_total_container) * 100 if inst.area_total_container > 0 else 0
        col3.metric("Ocupação (%)", f"{ocupacao_percentual:.2f}%")
        col4.metric("Tempo (s)", f"{duracao:.2f}s")
        
        st.progress(min(max(ocupacao_percentual / 100, 0.0), 1.0))
        
        st.subheader(f"Layout do Empacotamento: {instancia_selecionada}")
        fig = plot_solution_streamlit(inst.W, inst.H, final_placement, inst.name, valor_final)
        st.pyplot(fig)
        
        with st.expander("Ver Detalhes do Posicionamento"):
            st.write("Lista das peças acomodadas:")
            st.table(final_placement)
