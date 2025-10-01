from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CasoFilme:
    parametros: List[float]
    label: str
    titulo: Optional[str] = None
    ano: Optional[int] = None
    genero_original: Optional[str] = None
    imdb_rating: Optional[float] = None
    meta_score: Optional[float] = None
