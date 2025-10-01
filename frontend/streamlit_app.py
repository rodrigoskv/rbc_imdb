"""
    pip install matplotlib
    pip install pandas
    pip install streamlit
    python -m streamlit run frontend/streamlit_app.py
"""
import pandas as pd
import streamlit as st

from rbc.config import DEFAULT_DATASET_PATH
from rbc.data_io import carregar_casos_de_csv, resolver_colunas, get_poster_url
from rbc.rbc import RBC
from rbc.domain import CasoFilme

st.set_page_config(page_title="Recomenda Filmes", layout="wide")

st.title("Recomendação de Filmes")
st.write("Encontre filmes similares baseados na base IMDB TOP 1000")

CAMINHO_PADRAO = DEFAULT_DATASET_PATH

try:
    casos = carregar_casos_de_csv(CAMINHO_PADRAO)
    df = pd.read_csv(CAMINHO_PADRAO)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

with st.sidebar:
    st.header("Configurações")
    k_vizinhos = st.slider("Número de recomendações", min_value=1, max_value=10, value=3)

rbc = RBC(k=k_vizinhos)
rbc.ajustar(casos)

col_titulo, col_poster = resolver_colunas(df)

st.header("Encontrar filmes similares")
if col_titulo:
    filmes_disponiveis = df[col_titulo].dropna().unique().tolist()
    filme_selecionado = st.selectbox("Selecione um filme:", sorted(filmes_disponiveis))

    if filme_selecionado and st.button("Buscar similares"):
        caso_selecionado = next((c for c in casos if c.titulo == filme_selecionado), None)
        if caso_selecionado:
            poster_sel = get_poster_url(df, col_titulo, col_poster, filme_selecionado)
            if poster_sel:
                st.image(poster_sel, width=200, caption=filme_selecionado)

            recomendacoes = rbc.recomendar_filmes_similares(caso_selecionado, top_k=k_vizinhos)

            st.subheader(f"Filmes similares a {filme_selecionado}:")
            if not recomendacoes:
                st.write("Nenhuma recomendação encontrada.")
            else:
                cols = st.columns(min(3, len(recomendacoes)))
                for i, (dist, caso) in enumerate(recomendacoes):
                    with cols[i % len(cols)]:
                        poster_url = get_poster_url(df, col_titulo, col_poster, caso.titulo)
                        if poster_url:
                            st.image(poster_url, width=150, caption=caso.titulo)
                        st.write(f"**{i+1}. {caso.titulo}**")
                        st.write(f"*Gênero:* {caso.label}")
                        st.write(f"*IMDB:* {caso.imdb_rating or 'N/A'} | *Meta:* {caso.meta_score or 'N/A'}")
                        st.write(f"*Similaridade:* {RBC.score_por_distancia_public(dist):.1f}%")
                        st.write("---")
else:
    st.warning("Coluna de título não encontrada na base.")

st.header("Buscar por avaliações")
col1, col2 = st.columns(2)
with col1:
    rating_min = st.slider("Rating IMDB mínimo", 0.0, 10.0, 7.0, 0.1)
with col2:
    meta_min = st.slider("Meta Score mínimo", 0, 100, 60)

if st.button("Buscar por avaliações"):
    caso_preferencias = CasoFilme(parametros=[rating_min, meta_min / 10.0], label="Preferências")
    brutos = rbc.vizinhos_mais_proximos(caso_preferencias, top_n=k_vizinhos)
    recomendacoes = RBC.unique_by_title(brutos)

    st.subheader("Recomendações baseadas nas suas preferências:")
    if not recomendacoes:
        st.write("Nenhuma recomendação encontrada.")
    else:
        cols = st.columns(min(3, len(recomendacoes)))
        for i, (dist, caso) in enumerate(recomendacoes):
            with cols[i % len(cols)]:
                poster_url = get_poster_url(df, col_titulo, col_poster, caso.titulo)
                if poster_url:
                    st.image(poster_url, width=150, caption=caso.titulo)
                st.write(f"**{i+1}. {caso.titulo}**")
                st.write(f"*Gênero:* {caso.label}")
                st.write(f"*IMDB:* {caso.imdb_rating or 'N/A'} | *Meta:* {caso.meta_score or 'N/A'}")
                st.write(f"*Adequação:* {RBC.score_por_distancia_public(dist):.1f}%")
                st.write("---")

st.header("Base de dados")
st.dataframe(df, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.header("Sobre")
st.sidebar.write(
    "Os métodos de comparação são: Rating, Meta Score e Gênero.\n\n"
    "Base de dados: [IMDB Top 1000]"
    "(https://www.kaggle.com/datasets/harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows)."
)
