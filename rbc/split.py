import random
from typing import List, Tuple, TypeVar

T = TypeVar("T")

def dividir_treino_teste(itens: List[T], proporcao_treino: float = 0.8, seed: int = 42) -> Tuple[List[T], List[T]]:
    """
    Divide a lista em treino/teste de forma reprodutível.
    """
    if not 0.0 < proporcao_treino < 1.0:
        raise ValueError("proporcao_treino deve estar entre 0 e 1 (exclusivo).")
    rnd = random.Random(seed)
    copia = list(itens)
    rnd.shuffle(copia)
    n_train = int(len(copia) * proporcao_treino)
    return copia[:n_train], copia[n_train:]
