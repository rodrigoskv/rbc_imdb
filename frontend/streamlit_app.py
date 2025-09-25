"""
Front-end Streamlit para filtrar/visualizar dados IMDB e testar RBC.

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

st.set_page_config(page_title="RBC IMDB — Visualização e Filtro", layout="wide")

st.title("RBC IMDB — Visualizador e Filtro")
st.write("Use a barra lateral para carregar o CSV, ajustar filtros e testar previsões.")

# -------------------------
# Leitura do CSV (upload ou caminho padrão)
# -------------------------
CAMINHO_PADRAO = DEFAULT_DATASET_PATH

def carregar_dataframe(caminho: str) -> pd.DataFrame:
    # Usamos pandas aqui apenas para facilitar exibição/filtro na UI
    df = pd.read_csv(caminho)
    # Garante presença das colunas essenciais (case-insensitive)
    cols_lower = {c.lower(): c for c in df.columns}
    faltantes = [c for c in ["genre", "imdb_rating", "meta_score"] if c not in cols_lower]
    if faltantes:
        st.warning(f"Colunas essenciais ausentes no CSV: {faltantes}. O app pode não funcionar corretamente.")
    return df

with st.sidebar:
    st.header("Dados")
    arquivo_up = st.file_uploader("Envie o CSV do IMDB Top 1000", type=["csv"])
    usar_padrao = st.checkbox("Usar dataset incluído no projeto", value=os.path.exists(CAMINHO_PADRAO))
    caminho_csv = None

    if arquivo_up is not None:
        # Salva temporariamente para reutilizar nas funções do pacote
        temp_path = "uploaded_imdb.csv"
        with open(temp_path, "wb") as f:
            f.write(arquivo_up.read())
        caminho_csv = temp_path
    elif usar_padrao and os.path.exists(CAMINHO_PADRAO):
        caminho_csv = CAMINHO_PADRAO

    k_vizinhos = st.number_input("K (vizinhos para RBC)", min_value=1, max_value=50, value=1, step=1)

if not caminho_csv:
    st.info("Envie um CSV ou marque 'Usar arquivo padrão do ambiente' (se disponível).")
    st.stop()

# Carrega casos (para RBC) e também um DataFrame (para UI)
try:
    casos = carregar_casos_de_csv(caminho_csv)
except Exception as e:
    st.error(f"Erro ao carregar casos do CSV: {e}")
    st.stop()

df = carregar_dataframe(caminho_csv)

# Campos auxiliares
col_titulo = next((c for c in df.columns if c.lower() in ["series_title", "title", "series title"]), None)
col_genero = next((c for c in df.columns if c.lower() == "genre"), None)
col_rating = next((c for c in df.columns if c.lower() in ["imdb_rating", "rating", "imdb rating"]), None)
col_metascore = next((c for c in df.columns if c.lower() in ["meta_score", "metascore", "meta score"]), None)

# Cria campo 'primeiro_genero' para filtros
def primeiro_genero(g: Optional[str]) -> str:
    if not isinstance(g, str) or not g:
        return "Unknown"
    return g.split(",")[0].strip()

df["primeiro_genero"] = df[col_genero].apply(primeiro_genero) if col_genero else "Unknown"

# -------------------------
# RBC — treino/teste
# -------------------------
treino, teste = dividir_treino_teste(casos, proporcao_treino=0.8, seed=42)
rbc = RBC(k=int(k_vizinhos))
rbc.ajustar(treino)

y_true = [c.label for c in teste]
y_pred = rbc.prever_lote(teste)
acc = acuracia(y_true, y_pred)

st.subheader("Desempenho (avaliação rápida)")
st.write(f"Acurácia com K={int(k_vizinhos)}: **{acc*100:.2f}%**")

# -------------------------
# Filtros (sidebar)
# -------------------------
with st.sidebar:
    st.header("Filtros")
    generos = sorted(df["primeiro_genero"].dropna().unique().tolist()) if "primeiro_genero" in df else []
    generos_sel = st.multiselect("Gêneros", options=generos, default=generos[:5] if generos else [])

    min_rating = float(df[col_rating].min()) if col_rating else 0.0
    max_rating = float(df[col_rating].max()) if col_rating else 10.0
    faixa_rating = st.slider("IMDB_Rating", min_value=float(min_rating), max_value=float(max_rating),
                             value=(float(min_rating), float(max_rating)))

    min_meta = float(df[col_metascore].min()) if col_metascore else 0.0
    max_meta = float(df[col_metascore].max()) if col_metascore else 100.0
    faixa_meta = st.slider("Meta_score", min_value=float(min_meta), max_value=float(max_meta),
                           value=(float(min_meta), float(max_meta)))

# Aplica filtros
df_filtrado = df.copy()
if generos_sel:
    df_filtrado = df_filtrado[df_filtrado["primeiro_genero"].isin(generos_sel)]
if col_rating:
    df_filtrado = df_filtrado[(df_filtrado[col_rating] >= faixa_rating[0]) & (df_filtrado[col_rating] <= faixa_rating[1])]
if col_metascore:
    df_filtrado = df_filtrado[(df_filtrado[col_metascore] >= faixa_meta[0]) & (df_filtrado[col_metascore] <= faixa_meta[1])]

st.subheader("Tabela filtrada")
st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

# -------------------------
# Visualização: Dispersão (IMDB_Rating vs Meta_score)
# -------------------------
st.subheader("Gráfico de dispersão (IMDB_Rating × Meta_score)")
if col_rating and col_metascore:
    fig, ax = plt.subplots()
    ax.scatter(df_filtrado[col_rating], df_filtrado[col_metascore])
    ax.set_xlabel("IMDB_Rating")
    ax.set_ylabel("Meta_score")
    ax.set_title("Dispersão: Rating × Meta_score (filtrado)")
    st.pyplot(fig)
else:
    st.info("Colunas IMDB_Rating e/ou Meta_score não encontradas para o gráfico.")

# -------------------------
# Teste de Previsão
# -------------------------
st.subheader("Teste uma previsão (gênero)")
col1, col2, col3 = st.columns(3)
with col1:
    rating_in = st.number_input("IMDB_Rating (0..10)", min_value=0.0, max_value=10.0, value=8.0, step=0.1)
with col2:
    meta_in = st.number_input("Meta_score (0..100)", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
with col3:
    st.write(" ")

if st.button("Prever gênero pelo RBC"):
    # Constrói um CasoFilme 'sintético' para consulta
    caso_novo = CasoFilme(parametros=[rating_in, meta_in/10.0], label="(desconhecido)",
                          imdb_rating=rating_in, meta_score=meta_in)
    previsto = rbc.prever(caso_novo)
    st.success(f"Gênero previsto (primeiro gênero): **{previsto}**")

    # Mostra vizinhos mais próximos
    vizinhos = rbc.vizinhos_mais_proximos(caso_novo, top_n=5)
    st.write("Vizinhos mais próximos (distância, gênero, título):")
    linhas = []
    for dist, caso in vizinhos:
        linhas.append({
            "dist": round(dist, 4),
            "genero": caso.label,
            "titulo": caso.titulo,
            "rating": caso.imdb_rating,
            "meta_score": caso.meta_score
        })
    st.dataframe(pd.DataFrame(linhas))

st.caption("Dica: Ajuste **K** na barra lateral para ver como afeta a acurácia e as previsões.")
