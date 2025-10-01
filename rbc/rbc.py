import math
from typing import List, Tuple
from collections import Counter
from .domain import CasoFilme

def _unique_by_title(recs: List[Tuple[float, "CasoFilme"]]) -> List[Tuple[float, "CasoFilme"]]:
    vistos = set()
    out: List[Tuple[float, "CasoFilme"]] = []
    for dist, caso in recs:
        if caso.titulo not in vistos:
            vistos.add(caso.titulo)
            out.append((dist, caso))
    return out

def _score_por_distancia(dist: float) -> float:
    return max(0.0, 100.0 - (dist * 10.0))

class RBC:
    def __init__(self, k: int = 1):
        if k <= 0:
            raise ValueError("k deve ser >= 1")
        self.k = k
        self._base: List[CasoFilme] = []
        self._input_size: int = 0

    def ajustar(self, casos: List[CasoFilme]) -> None:
        self._base = [c for c in casos if c.parametros is not None]
        if not self._base:
            raise ValueError("Base de casos vazia.")
        self._input_size = len(self._base[0].parametros)

    def _distancia_euclidiana(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            raise ValueError("Vetores de tamanhos diferentes.")
        soma = 0.0
        for ai, bi in zip(a, b):
            diff = ai - bi
            soma += diff * diff
        return math.sqrt(soma)

    def prever(self, caso_novo: CasoFilme) -> str:
        if not self._base:
            raise RuntimeError("Chame ajustar(casos) antes de prever.")
        dists = [(self._distancia_euclidiana(c.parametros, caso_novo.parametros), c.label) for c in self._base]
        dists.sort(key=lambda x: x[0])
        k_vizinhos = dists[:self.k]

        contagem = Counter([lab for _, lab in k_vizinhos])
        mais_comuns = contagem.most_common()
        if not mais_comuns:
            raise RuntimeError("Nenhum vizinho encontrado.")

        top_freq = mais_comuns[0][1]
        empatados = [lab for lab, freq in mais_comuns if freq == top_freq]

        if len(empatados) == 1:
            return empatados[0]
        for dist, lab in k_vizinhos:
            if lab in empatados:
                return lab
        return k_vizinhos[0][1]

    def prever_lote(self, casos: List[CasoFilme]) -> List[str]:
        return [self.prever(c) for c in casos]

    def vizinhos_mais_proximos(self, caso_novo: CasoFilme, top_n: int = 5) -> List[Tuple[float, CasoFilme]]:
        if not self._base:
            raise RuntimeError("Base não ajustada. Chame ajustar(casos) antes.")
        dists = [(self._distancia_euclidiana(c.parametros, caso_novo.parametros), c) for c in self._base]
        dists.sort(key=lambda x: x[0])
        return dists[:max(1, top_n)]

    @staticmethod
    def unique_by_title(recs: List[Tuple[float, "CasoFilme"]]) -> List[Tuple[float, "CasoFilme"]]:
        return _unique_by_title(recs)

    @staticmethod
    def score_por_distancia_public(dist: float) -> float:
        return _score_por_distancia(dist)

    def recomendar_filmes_similares(self, filme_alvo: CasoFilme, top_k: int = 5) -> List[Tuple[float, CasoFilme]]:

        brutos = self.vizinhos_mais_proximos(filme_alvo, top_n=max(1, top_k + 3))
        filtrados = [(d, c) for (d, c) in brutos if c.titulo != filme_alvo.titulo]
        return _unique_by_title(filtrados)[:top_k]
