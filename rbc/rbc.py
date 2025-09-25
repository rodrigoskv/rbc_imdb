import math
from typing import List, Tuple
from collections import Counter
from .domain import CasoFilme

class RBC:
    """
    Implementação simples de RBC (k-NN) para classificação.
    - k: número de vizinhos. k=1 resulta no clássico 1-NN (muito comum no RBC introdutório).
    """
    def __init__(self, k: int = 1):
        if k <= 0:
            raise ValueError("k deve ser >= 1")
        self.k = k
        self._base: List[CasoFilme] = []
        self._input_size: int = 0

    # ------------------------
    # Treino / Base de Casos
    # ------------------------
    def ajustar(self, casos: List[CasoFilme]) -> None:
        """
        'Ajusta' o RBC carregando a base de casos (não há treinamento paramétrico).
        """
        self._base = [c for c in casos if c.parametros is not None]
        if not self._base:
            raise ValueError("Base de casos vazia.")
        self._input_size = len(self._base[0].parametros)

    # ------------------------
    # Distância
    # ------------------------
    def _distancia_euclidiana(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            raise ValueError("Vetores de tamanhos diferentes.")
        soma = 0.0
        for ai, bi in zip(a, b):
            diff = ai - bi
            soma += diff * diff
        return math.sqrt(soma)

    # ------------------------
    # Predição
    # ------------------------
    def prever(self, caso_novo: CasoFilme) -> str:
        """
        Retorna o rótulo previsto com base nos k vizinhos mais próximos.
        Em empate de votação, usa o vizinho mais próximo dentre os empatados.
        """
        if not self._base:
            raise RuntimeError("Chame ajustar(casos) antes de prever.")
        dists = [(self._distancia_euclidiana(c.parametros, caso_novo.parametros), c.label) for c in self._base]
        dists.sort(key=lambda x: x[0])
        k_vizinhos = dists[:self.k]

        contagem = Counter([lab for _, lab in k_vizinhos])
        mais_comuns = contagem.most_common()
        if len(mais_comuns) == 0:
            raise RuntimeError("Nenhum vizinho encontrado.")

        # Frequência máxima
        top_freq = mais_comuns[0][1]
        empatados = [lab for lab, freq in mais_comuns if freq == top_freq]

        if len(empatados) == 1:
            return empatados[0]
        # Desempate: pega o rótulo do vizinho mais próximo entre os empatados
        for dist, lab in k_vizinhos:
            if lab in empatados:
                return lab
        # fallback (não deveria acontecer)
        return k_vizinhos[0][1]

    def prever_lote(self, casos: List[CasoFilme]) -> List[str]:
        return [self.prever(c) for c in casos]

    # ------------------------
    # Explicabilidade
    # ------------------------
    def vizinhos_mais_proximos(self, caso_novo: CasoFilme, top_n: int = 5) -> List[Tuple[float, CasoFilme]]:
        """
        Retorna os 'top_n' vizinhos (distância, caso) mais próximos, ordenados por distância.
        Útil para explicabilidade no front-end.
        """
        dists = [(self._distancia_euclidiana(c.parametros, caso_novo.parametros), c) for c in self._base]
        dists.sort(key=lambda x: x[0])
        return dists[:max(1, top_n)]
