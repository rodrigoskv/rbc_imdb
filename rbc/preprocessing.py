from typing import List, Optional

def extrair_primeiro_genero(generos: Optional[str]) -> str:
    """
    Recebe uma string de gêneros (ex.: "Drama, Romance") e devolve o primeiro gênero ("Drama").
    Retorna "Unknown" se estiver vazio/nulo.
    """
    if not generos:
        return "Unknown"
    # Separação por vírgula, removendo espaços excedentes
    primeiro = generos.split(",")[0].strip()
    return primeiro if primeiro else "Unknown"

def construir_parametros(imdb_rating: Optional[float], meta_score: Optional[float]) -> Optional[List[float]]:
    """
    Monta o vetor de parâmetros do caso.
    - imdb_rating: escala 0..10
    - meta_score: escala 0..100 -> reescalado para 0..10 (dividindo por 10)
    Retorna None se algum dos dois for inválido.
    """
    if imdb_rating is None or meta_score is None:
        return None
    return [float(imdb_rating), float(meta_score) / 10.0]
