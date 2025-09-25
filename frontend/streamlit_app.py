"""
Front-end Streamlit para recomendação de filmes baseada em RBC.

Execute:
    streamlit run frontend/streamlit_app.py
"""
import os
import io
from typing import List, Optional
import pandas as pd
import streamlit as st
from rbc.config import DEFAULT_DATASET_PATH
import matplotlib.pyplot as plt

from rbc.data_io import carregar_casos_de_csv
from rbc.rbc import RBC
from rbc.split import dividir_treino_teste
from rbc.metrics import acuracia
from rbc.domain import CasoFilme

st.set_page_config(page_title="Sistema de Recomendação de Filmes - RBC", layout="wide")

st.title("🎬 Sistema de Recomendação de Filmes Baseado em RBC")
st.write("Encontre filmes similares com base nas avaliações do IMDB e Metacritic.")

# -------------------------
# Leitura do CSV
# -------------------------
CAMINHO_PADRAO = DEFAULT_DATASET_PATH

def carregar_dataframe(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho)
    cols_lower = {c.lower(): c for c in df.columns}
    faltantes = [c for c in ["genre", "imdb_rating", "meta_score"] if c not in cols_lower]
    if faltantes:
        st.warning(f"Colunas essenciais ausentes no CSV: {faltantes}. O app pode não funcionar corretamente.")
    return df

with st.sidebar:
    st.header("⚙️ Configurações")
    arquivo_up = st.file_uploader("Envie o CSV do IMDB Top 1000", type=["csv"])
    usar_padrao = st.checkbox("Usar dataset incluído no projeto", value=os.path.exists(CAMINHO_PADRAO))
    caminho_csv = None

    if arquivo_up is not None:
        temp_path = "uploaded_imdb.csv"
        with open(temp_path, "wb") as f:
            f.write(arquivo_up.read())
        caminho_csv = temp_path
    elif usar_padrao and os.path.exists(CAMINHO_PADRAO):
        caminho_csv = CAMINHO_PADRAO

    k_vizinhos = st.slider("Número de recomendações (K)", min_value=1, max_value=20, value=5, step=1)

if not caminho_csv:
    st.info("Envie um CSV ou marque 'Usar arquivo padrão do ambiente' (se disponível).")
    st.stop()

# Carrega casos
try:
    casos = carregar_casos_de_csv(caminho_csv)
except Exception as e:
    st.error(f"Erro ao carregar casos do CSV: {e}")
    st.stop()

df = carregar_dataframe(caminho_csv)

# Identifica colunas
col_titulo = next((c for c in df.columns if c.lower() in ["series_title", "title", "series title"]), None)
col_genero = next((c for c in df.columns if c.lower() == "genre"), None)
col_rating = next((c for c in df.columns if c.lower() in ["imdb_rating", "rating", "imdb rating"]), None)
col_metascore = next((c for c in df.columns if c.lower() in ["meta_score", "metascore", "meta score"]), None)

# -------------------------
# Sistema de Recomendação
# -------------------------
st.header("🎯 Sistema de Recomendação")

# Treina o RBC com todos os dados para recomendação
rbc_recomendacao = RBC(k=int(k_vizinhos))
rbc_recomendacao.ajustar(casos)

# Método 1: Selecionar um filme existente para encontrar similares
st.subheader("1. Encontrar filmes similares a um filme específico")

# Criar lista de filmes para seleção
if col_titulo:
    filmes_disponiveis = df[col_titulo].dropna().unique().tolist()
    filme_selecionado = st.selectbox("Selecione um filme:", sorted(filmes_disponiveis))
    
    if filme_selecionado:
        # Encontrar o caso correspondente ao filme selecionado
        caso_filme_selecionado = next((c for c in casos if c.titulo == filme_selecionado), None)
        
        if caso_filme_selecionado:
            if st.button("🔍 Encontrar filmes similares"):
                # Encontrar os vizinhos mais próximos (recomendações)
                recomendacoes = rbc_recomendacao.vizinhos_mais_proximos(caso_filme_selecionado, top_n=int(k_vizinhos)+1)
                
                # Pular o primeiro resultado (que é o próprio filme)
                recomendacoes = recomendacoes[1:]
                
                st.success(f"🎭 Recomendações baseadas em **{filme_selecionado}**:")
                
                # Mostrar recomendações em uma tabela formatada
                dados_recomendacoes = []
                for i, (distancia, caso) in enumerate(recomendacoes, 1):
                    dados_recomendacoes.append({
                        "Posição": i,
                        "Filme": caso.titulo or "N/A",
                        "Gênero": caso.label,
                        "IMDB Rating": caso.imdb_rating or "N/A",
                        "Meta Score": caso.meta_score or "N/A",
                        "Ano": caso.ano or "N/A",
                        "Similaridade": f"{100 - (distancia * 10):.1f}%"
                    })
                
                df_recomendacoes = pd.DataFrame(dados_recomendacoes)
                st.dataframe(df_recomendacoes, use_container_width=True, hide_index=True)

# Método 2: Buscar por características específicas
st.subheader("2. Encontrar filmes por preferências de avaliação")

col1, col2 = st.columns(2)
with col1:
    rating_min = st.slider("IMDB Rating mínimo", 0.0, 10.0, 7.0, 0.1)
with col2:
    meta_min = st.slider("Meta Score mínimo", 0.0, 100.0, 60.0, 1.0)

if st.button("🎯 Buscar filmes por avaliações"):
    # Criar um caso fictício baseado nas preferências
    caso_preferencias = CasoFilme(
        parametros=[rating_min, meta_min/10.0], 
        label="Preferências",
        imdb_rating=rating_min, 
        meta_score=meta_min
    )
    
    # Encontrar filmes similares às preferências
    recomendacoes = rbc_recomendacao.vizinhos_mais_proximos(caso_preferencias, top_n=int(k_vizinhos))
    
    st.success(f"🎭 Filmes recomendados baseados nas suas preferências:")
    
    dados_recomendacoes = []
    for i, (distancia, caso) in enumerate(recomendacoes, 1):
        dados_recomendacoes.append({
            "Posição": i,
            "Filme": caso.titulo or "N/A",
            "Gênero": caso.label,
            "IMDB Rating": caso.imdb_rating or "N/A",
            "Meta Score": caso.meta_score or "N/A",
            "Ano": caso.ano or "N/A",
            "Adequação": f"{100 - (distancia * 10):.1f}%"
        })
    
    df_recomendacoes = pd.DataFrame(dados_recomendacoes)
    st.dataframe(df_recomendacoes, use_container_width=True, hide_index=True)

# -------------------------
# Visualização dos Dados
# -------------------------
st.header("📊 Visualização dos Dados")

# Filtros
with st.sidebar:
    st.header("🔍 Filtros de Visualização")
    if col_genero:
        generos = sorted(df[col_genero].dropna().unique().tolist())
        generos_sel = st.multiselect("Filtrar por gênero:", options=generos, default=[])

# Aplicar filtros
df_filtrado = df.copy()
if col_genero and generos_sel:
    # Filtrar por gênero (usando contains para gêneros múltiplos)
    mask = df_filtrado[col_genero].str.contains('|'.join(generos_sel), na=False)
    df_filtrado = df_filtrado[mask]

st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

# Gráfico de dispersão
if col_rating and col_metascore:
    st.subheader("📈 Dispersão: IMDB Rating vs Meta Score")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Colorir por gênero se disponível
    if col_genero and generos_sel:
        for genero in generos_sel:
            mask = df_filtrado[col_genero].str.contains(genero, na=False)
            df_genero = df_filtrado[mask]
            ax.scatter(df_genero[col_rating], df_genero[col_metascore], label=genero, alpha=0.7)
        ax.legend()
    else:
        ax.scatter(df_filtrado[col_rating], df_filtrado[col_metascore], alpha=0.7)
    
    ax.set_xlabel("IMDB Rating")
    ax.set_ylabel("Meta Score")
    ax.set_title("Relação entre Avaliações do IMDB e Metacritic")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

st.sidebar.markdown("---")
st.sidebar.info("💡 Dica: Use mais recomendações (K maior) para descobrir filmes mais diversos.")