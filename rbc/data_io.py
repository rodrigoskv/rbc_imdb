import csv
from typing import List, Dict, Optional, Tuple
from .domain import CasoFilme
from .preprocessing import extrair_primeiro_genero, construir_parametros

# Nomes usuais de colunas no IMDB Top 1000 (Kaggle). Usaremos mapeamento case-insensitive.
POSSIVEIS_COLUNAS = {
    "series_title": ["series_title", "title", "series title"],
    "released_year": ["released_year", "year", "released year"],
    "genre": ["genre"],
    "imdb_rating": ["imdb_rating", "rating", "imdb rating"],
    "meta_score": ["meta_score", "metascore", "meta score"],
}

def _normalizar_nome_coluna(nome: str) -> str:
    return nome.strip().lower().replace(" ", "_")

def _mapear_indices_cabecalho(header: List[str]) -> Dict[str, int]:
    """
    Dado o cabeçalho, encontra o índice de cada coluna de interesse.
    Faz busca case-insensitive, permitindo pequenas variações.
    Levanta ValueError se campos essenciais não forem encontrados.
    """
    normalizados = [_normalizar_nome_coluna(h) for h in header]
    idx_map: Dict[str, int] = {}

    for chave_logica, aliases in POSSIVEIS_COLUNAS.items():
        encontrado = -1
        for i, nome in enumerate(normalizados):
            if nome in aliases:
                encontrado = i
                break
        if encontrado < 0:
            # Alguns campos são essenciais
            if chave_logica in ("genre", "imdb_rating", "meta_score"):
                raise ValueError(f"Coluna essencial não encontrada: {chave_logica} (aliases: {aliases})")
            # Outros (como titulo/ano) são opcionais
        idx_map[chave_logica] = encontrado
    return idx_map

def _parse_float(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None

def _parse_int(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        # Alguns datasets trazem anos como "1994(I)" — remove não dígitos
        import re
        digitos = "".join(re.findall(r"\d+", s))
        if digitos:
            try:
                return int(digitos)
            except ValueError:
                return None
        return None

def carregar_casos_de_csv(caminho_csv: str) -> List[CasoFilme]:
    """
    Lê o CSV do IMDB Top 1000 e constrói a lista de `CasoFilme` prontos para uso.
    Ignora linhas sem `IMDB_Rating` ou `Meta_score`.
    """
    casos: List[CasoFilme] = []
    with open(caminho_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV vazio: sem cabeçalho.")

        idx = _mapear_indices_cabecalho(header)

        for row in reader:
            # Protege contra linhas curtas
            if len(row) < len(header):
                continue

            titulo = row[idx["series_title"]] if idx["series_title"] >= 0 else None
            ano = _parse_int(row[idx["released_year"]]) if idx["released_year"] >= 0 else None
            genero_original = row[idx["genre"]] if idx["genre"] >= 0 else None
            imdb_rating = _parse_float(row[idx["imdb_rating"]]) if idx["imdb_rating"] >= 0 else None
            meta_score = _parse_float(row[idx["meta_score"]]) if idx["meta_score"] >= 0 else None

            # Constrói rótulo (primeiro gênero) e vetor de parâmetros
            label = extrair_primeiro_genero(genero_original)
            params = construir_parametros(imdb_rating, meta_score)

            # Ignora registros inválidos
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
