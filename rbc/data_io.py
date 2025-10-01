
import csv
from typing import List, Dict, Optional, Tuple
import pandas as pd

from .domain import CasoFilme
from .preprocessing import extrair_primeiro_genero, construir_parametros


POSSIVEIS_COLUNAS = {
    "series_title": ["series_title", "title", "series title"],
    "released_year": ["released_year", "year", "released year"],
    "genre": ["genre", "genres"],
    "imdb_rating": ["imdb_rating", "rating", "imdb rating", "imdb"],
    "meta_score": ["meta_score", "metascore", "meta score"],
}


POSSIVEIS_TITULO = ["series_title", "title", "series title"]
POSSIVEIS_POSTER = ["poster", "poster_link", "poster_url", "poster url"]

def _normalizar_nome_coluna(nome: str) -> str:
    return nome.strip().lower().replace(" ", "_")

def _mapear_indices_cabecalho(header: List[str]) -> Dict[str, int]:
    normalizados = [_normalizar_nome_coluna(h) for h in header]
    idx_map: Dict[str, int] = {}
    for chave_logica, aliases in POSSIVEIS_COLUNAS.items():
        encontrado = -1
        for i, nome in enumerate(normalizados):
            if nome in aliases:
                encontrado = i
                break
        if encontrado < 0 and chave_logica in ("genre", "imdb_rating", "meta_score"):
            raise ValueError(f"Coluna essencial não encontrada: {chave_logica} (aliases: {aliases})")
        idx_map[chave_logica] = encontrado
    return idx_map


def _coerce_number(s: Optional[str], to=float) -> Optional[float]:
    if s is None:
        return None
    s = str(s).strip().replace(",", "")
    if s == "":
        return None
    try:
        return to(s)
    except Exception:
        import re
        digs = "".join(re.findall(r"\d+", s))
        if not digs:
            return None
        try:
            return to(digs)
        except Exception:
            return None

def _parse_float(s: Optional[str]) -> Optional[float]:
    return _coerce_number(s, to=float)

def _parse_int(s: Optional[str]) -> Optional[int]:
    return _coerce_number(s, to=int)


def resolver_colunas(df: pd.DataFrame,
                     candidatos_titulo = POSSIVEIS_TITULO,
                     candidatos_poster = POSSIVEIS_POSTER) -> Tuple[Optional[str], Optional[str]]:
    
    lower_to_real = {c.lower(): c for c in df.columns}
    col_titulo = next((lower_to_real[c] for c in candidatos_titulo if c in lower_to_real), None)
    col_poster = next((lower_to_real[c] for c in candidatos_poster if c in lower_to_real), None)
    return col_titulo, col_poster

def get_poster_url(df: pd.DataFrame,
                   col_titulo: Optional[str],
                   col_poster: Optional[str],
                   titulo: str) -> Optional[str]:

    if not col_titulo or not col_poster:
        return None
    if col_titulo not in df.columns or col_poster not in df.columns:
        return None
    row = df[df[col_titulo] == titulo]
    if row.empty:
        return None
    url = row[col_poster].iloc[0]
    return url if isinstance(url, str) and url.strip().lower().startswith("http") else None


def carregar_casos_de_csv(caminho_csv: str) -> List[CasoFilme]:
    casos: List[CasoFilme] = []
    with open(caminho_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV vazio: sem cabeçalho.")

        idx = _mapear_indices_cabecalho(header)

        for row in reader:
            if len(row) < len(header):
                continue

            titulo = row[idx["series_title"]] if idx["series_title"] >= 0 else None
            ano = _parse_int(row[idx["released_year"]]) if idx["released_year"] >= 0 else None
            genero_original = row[idx["genre"]] if idx["genre"] >= 0 else None
            imdb_rating = _parse_float(row[idx["imdb_rating"]]) if idx["imdb_rating"] >= 0 else None
            meta_score = _parse_float(row[idx["meta_score"]]) if idx["meta_score"] >= 0 else None

            label = extrair_primeiro_genero(genero_original)
            params = construir_parametros(imdb_rating, meta_score)
            if params is None:
                continue

            casos.append(CasoFilme(
                parametros=params,
                label=label,
                titulo=titulo,
                ano=ano,
                genero_original=genero_original,
                imdb_rating=imdb_rating,
                meta_score=meta_score
            ))

    if not casos:
        raise ValueError("Nenhum caso válido construído. Verifique se IMDB_Rating/Meta_score existem no CSV.")
    return casos
