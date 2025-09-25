"""
Front-end Streamlit para recomendação de filmes baseada em RBC.

Execute:
    streamlit run frontend/streamlit_app.py
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
            if col_poster:
                poster_selecionado = df[df[col_titulo] == filme_selecionado][col_poster].iloc[0] if col_poster in df.columns else None
                if poster_selecionado and pd.notna(poster_selecionado):
                    st.image(poster_selecionado, width=200, caption=filme_selecionado)
            
            # Criar colunas para as recomendações
            cols = st.columns(min(3, len(recomendacoes)))
            
            for i, (distancia, caso) in enumerate(recomendacoes):
                with cols[i % len(cols)]:
                    # Buscar poster do filme recomendado
                    poster_url = None
                    if col_poster and col_poster in df.columns:
                        poster_match = df[df[col_titulo] == caso.titulo]
                        if not poster_match.empty:
                            poster_url = poster_match[col_poster].iloc[0]
                    
                    # Mostrar poster ou placeholder
                    if poster_url and pd.notna(poster_url):
                        st.image(poster_url, width=150, caption=caso.titulo)
                    else:
                        st.write(f"🎬 {caso.titulo}")
                    
                    st.write(f"**{i+1}. {caso.titulo}**")
                    st.write(f"*Gênero:* {caso.label}")
                    st.write(f"*IMDB:* {caso.imdb_rating} | *Meta:* {caso.meta_score}")
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
    
    cols = st.columns(min(3, len(recomendacoes)))
    
    for i, (distancia, caso) in enumerate(recomendacoes):
        with cols[i % len(cols)]:
            # Buscar poster do filme recomendado
            poster_url = None
            if col_poster and col_poster in df.columns:
                poster_match = df[df[col_titulo] == caso.titulo]
                if not poster_match.empty:
                    poster_url = poster_match[col_poster].iloc[0]
            
            # Mostrar poster ou placeholder
            if poster_url and pd.notna(poster_url):
                st.image(poster_url, width=150, caption=caso.titulo)
            else:
                st.write(f"🎬 {caso.titulo}")
            
            st.write(f"**{i+1}. {caso.titulo}**")
            st.write(f"*Gênero:* {caso.label}")
            st.write(f"*IMDB:* {caso.imdb_rating} | *Meta:* {caso.meta_score}")
            st.write("---")

# Visualização da base de dados com posters
st.header("Base de dados completa")

# Se tiver coluna de poster, mostrar visualização com imagens
if col_poster and col_poster in df.columns:
    st.write("Visualização com posters:")
    
    # Filtro por gênero se existir coluna de gênero
    col_genero = next((c for c in df.columns if c.lower() == "genre"), None)
    if col_genero:
        generos = sorted(df[col_genero].dropna().unique().tolist())
        genero_selecionado = st.selectbox("Filtrar por gênero:", ["Todos"] + generos)
        
        if genero_selecionado != "Todos":
            df_filtrado = df[df[col_genero].str.contains(genero_selecionado, na=False)]
        else:
            df_filtrado = df
    else:
        df_filtrado = df
    
    # Mostrar filmes em grid de posters
    num_colunas = 4
    filmes_por_pagina = 12
    
    if len(df_filtrado) > 0:
        # Paginação
        total_paginas = (len(df_filtrado) - 1) // filmes_por_pagina + 1
        pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1)
        
        inicio = (pagina - 1) * filmes_por_pagina
        fim = inicio + filmes_por_pagina
        filmes_pagina = df_filtrado.iloc[inicio:fim]
        
        # Criar grid
        cols = st.columns(num_colunas)
        
        for i, (_, filme) in enumerate(filmes_pagina.iterrows()):
            with cols[i % num_colunas]:
                poster_url = filme[col_poster] if pd.notna(filme[col_poster]) else None
                titulo = filme[col_titulo] if col_titulo else "Título não disponível"
                
                if poster_url:
                    st.image(poster_url, width=120, caption=titulo)
                else:
                    st.write(f"🎬 {titulo}")
                
                if col_genero:
                    st.write(f"*Gênero:* {filme[col_genero]}")
                
                # Mostrar ratings se disponíveis
                col_rating = next((c for c in df.columns if c.lower() in ["imdb_rating", "rating"]), None)
                col_meta = next((c for c in df.columns if c.lower() in ["meta_score", "metascore"]), None)
                
                if col_rating and col_rating in filme and pd.notna(filme[col_rating]):
                    st.write(f"*IMDB:* {filme[col_rating]}")
                if col_meta and col_meta in filme and pd.notna(filme[col_meta]):
                    st.write(f"*Meta:* {filme[col_meta]}")
                
                st.write("---")
        
        st.write(f"Página {pagina} de {total_paginas} - {len(df_filtrado)} filmes no total")
    else:
        st.write("Nenhum filme encontrado com os filtros selecionados.")
else:
    # Fallback: mostrar tabela normal se não tiver posters
    st.dataframe(df, use_container_width=True)