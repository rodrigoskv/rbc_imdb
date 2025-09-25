"""
    pip install matplotlib
    pip install pandas   
    pip install streamlit
    python -m streamlit run frontend/streamlit_app.py
"""

import os
import pandas as pd
import streamlit as st
from rbc.config import DEFAULT_DATASET_PATH

from rbc.data_io import carregar_casos_de_csv
from rbc.rbc import RBC
from rbc.domain import CasoFilme

st.set_page_config(page_title="Recomenda Filmes", layout="wide")

st.title("Recomendação de Filmes")
st.write("Encontre filmes similares baseados na base IMDB TOP 1000")

CAMINHO_PADRAO = DEFAULT_DATASET_PATH

# Carrega dados
try:
    casos = carregar_casos_de_csv(CAMINHO_PADRAO)
    df = pd.read_csv(CAMINHO_PADRAO)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Configurações
with st.sidebar:
    st.header("Configurações")
    k_vizinhos = st.slider("Número de recomendações", min_value=1, max_value=10, value=3)

# Treina o RBC
rbc = RBC(k=k_vizinhos)
rbc.ajustar(casos)

# Identifica colunas
col_titulo = next((c for c in df.columns if c.lower() in ["series_title", "title"]), None)
col_poster = next((c for c in df.columns if c.lower() in ["poster", "poster_link", "poster_url"]), None)

# Busca por filme específico
st.header("Encontrar filmes similares")

if col_titulo:
    filmes_disponiveis = df[col_titulo].dropna().unique().tolist()
    filme_selecionado = st.selectbox("Selecione um filme:", sorted(filmes_disponiveis))
    
    if filme_selecionado and st.button("Buscar similares"):
        caso_selecionado = next((c for c in casos if c.titulo == filme_selecionado), None)
        
        if caso_selecionado:
            recomendacoes = rbc.vizinhos_mais_proximos(caso_selecionado, top_n=k_vizinhos+1)
            recomendacoes = recomendacoes[1:]  # Remove o próprio filme
            
            st.subheader(f"Filmes similares a {filme_selecionado}:")
            
            # Mostrar poster do filme selecionado
            if col_poster and col_poster in df.columns:
                poster_selecionado = df[df[col_titulo] == filme_selecionado][col_poster].iloc[0] if not df[df[col_titulo] == filme_selecionado].empty else None
                if poster_selecionado and pd.notna(poster_selecionado) and isinstance(poster_selecionado, str) and poster_selecionado.startswith('http'):
                    st.image(poster_selecionado, width=200, caption=filme_selecionado)
            
            # Criar colunas para as recomendações
            num_cols = min(3, len(recomendacoes))
            if num_cols > 0:
                cols = st.columns(num_cols)
                
                for i, (distancia, caso) in enumerate(recomendacoes):
                    with cols[i % num_cols]:
                        # Buscar poster do filme recomendado
                        poster_url = None
                        if col_poster and col_poster in df.columns:
                            poster_match = df[df[col_titulo] == caso.titulo]
                            if not poster_match.empty:
                                poster_url = poster_match[col_poster].iloc[0]
                        
                        # Mostrar poster se for uma URL válida
                        if poster_url and pd.notna(poster_url) and isinstance(poster_url, str) and poster_url.startswith('http'):
                            st.image(poster_url, width=150, caption=caso.titulo)
                        
                        st.write(f"**{i+1}. {caso.titulo}**")
                        st.write(f"*Gênero:* {caso.label}")
                        st.write(f"*IMDB:* {caso.imdb_rating or 'N/A'} | *Meta:* {caso.meta_score or 'N/A'}")
                        similaridade = max(0, 100 - (distancia * 10))
                        st.write(f"*Similaridade:* {similaridade:.1f}%")
                        st.write("---")

# Busca por preferências
st.header("Buscar por avaliações")

col1, col2 = st.columns(2)
with col1:
    rating_min = st.slider("Rating IMDB mínimo", 0.0, 10.0, 7.0, 0.1)
with col2:
    meta_min = st.slider("Meta Score mínimo", 0, 100, 60)

if st.button("Buscar por avaliações"):
    caso_preferencias = CasoFilme(
        parametros=[rating_min, meta_min/10.0], 
        label="Preferências"
    )
    
    recomendacoes = rbc.vizinhos_mais_proximos(caso_preferencias, top_n=k_vizinhos)
    
    st.subheader("Recomendações baseadas nas suas preferências:")
    
    if recomendacoes:
        num_cols = min(3, len(recomendacoes))
        cols = st.columns(num_cols)
        
        for i, (distancia, caso) in enumerate(recomendacoes):
            with cols[i % num_cols]:
                # Buscar poster do filme recomendado
                poster_url = None
                if col_poster and col_poster in df.columns:
                    poster_match = df[df[col_titulo] == caso.titulo]
                    if not poster_match.empty:
                        poster_url = poster_match[col_poster].iloc[0]
                
                # Mostrar poster se for uma URL válida
                if poster_url and pd.notna(poster_url) and isinstance(poster_url, str) and poster_url.startswith('http'):
                    st.image(poster_url, width=150, caption=caso.titulo)
                
                st.write(f"**{i+1}. {caso.titulo}**")
                st.write(f"*Gênero:* {caso.label}")
                st.write(f"*IMDB:* {caso.imdb_rating or 'N/A'} | *Meta:* {caso.meta_score or 'N/A'}")
                adequacao = max(0, 100 - (distancia * 10))
                st.write(f"*Adequação:* {adequacao:.1f}%")
                st.write("---")
    else:
        st.write("Nenhuma recomendação encontrada.")

# Visualização da base de dados (mantida como tabela CSV)
st.header("Base de dados")
st.dataframe(df, use_container_width=True)

# Informações sobre a base
st.sidebar.markdown("---")
st.sidebar.header("Sobre")
st.sidebar.info(f"Total de filmes: {len(df)}")
if col_poster and col_poster in df.columns:
    posters_disponiveis = df[col_poster].apply(lambda x: isinstance(x, str) and x.startswith('http')).sum()
    st.sidebar.info(f"Posters disponíveis: {posters_disponiveis}/{len(df)}")