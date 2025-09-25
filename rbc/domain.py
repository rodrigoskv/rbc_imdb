from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CasoFilme:
    """
    Representa um 'caso' na base de filmes.
    - parametros: vetor numérico usado no RBC (ex.: [rating, metascore/10])
    - label: rótulo alvo (neste projeto, o primeiro gênero)
    - titulo, ano, genero_original, imdb_rating, meta_score: metadados úteis
    """
    parametros: List[float]
    label: str
    titulo: Optional[str] = None
    ano: Optional[int] = None
    genero_original: Optional[str] = None
    imdb_rating: Optional[float] = None
    meta_score: Optional[float] = None
