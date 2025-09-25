import random
from typing import List, Tuple, TypeVar

T = TypeVar("T")

def dividir_treino_teste(itens: List[T], proporcao_treino: float = 0.8, seed: int = 42) -> Tuple[List[T], List[T]]:
    """
    Divide a lista em treino/teste de forma reprodutível.
    """
    
    rnd = random.Random(seed)
    copia = list(itens)
    rnd.shuffle(copia)
    n_train = int(len(copia) * proporcao_treino)
    return copia[:n_train], copia[n_train:]
