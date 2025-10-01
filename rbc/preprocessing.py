from typing import List, Optional

def extrair_primeiro_genero(generos: Optional[str]) -> str:
    if not generos:
        return "Unknown"
    primeiro = generos.split(",")[0].strip()
    return primeiro if primeiro else "Unknown"

def construir_parametros(imdb_rating: Optional[float], meta_score: Optional[float]) -> Optional[List[float]]:
    if imdb_rating is None or meta_score is None:
        return None
    return [float(imdb_rating), float(meta_score) / 10.0]
