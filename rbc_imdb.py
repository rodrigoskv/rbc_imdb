#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBC (Raciocínio Baseado em Casos) para CSV de filmes — apenas biblioteca padrão.

Ajustes nesta versão:
- Mantida a estrutura original (DatasetFilmes, RBCFilmes, Caso, funções auxiliares e CLI).
- O caminho do CSV é OPCIONAL na linha de comando; por padrão, usa a base enviada:
  /mnt/data/imdb_top_1000 (1).csv

Como usar (exemplos):
  1) Usando a base enviada, escolhendo o filme por título (substring), k=7:
     python rbc_movies.py --movie-title "inception" --k 7

  2) Listando uma amostra e escolhendo por índice:
     python rbc_movies.py --list-sample
     # depois, informe o índice quando solicitado

  3) Prevê a coluna 'Certificate' com base nos vizinhos:
     python rbc_movies.py --movie-title "matrix" --predict Certificate

  4) Ajustando pesos por coluna:
     python rbc_movies.py --movie-title "toy story" --weights "IMDB_Rating=2;Genre=1.5;Runtime=0.5"

Observações:
- Usa SOMENTE biblioteca padrão (csv, math, re, argparse, sys, dataclasses, typing).
- Colunas comuns reconhecidas na base do Kaggle:
    NUMÉRICAS: Released_Year, Runtime, IMDB_Rating, Meta_score, No_of_Votes, Gross
    MULTI:     Genre, Genres
    CATEG.:    Certificate, Rated
"""

import argparse
import csv
import math
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Caminho padrão para a base que você enviou
CSV_PADRAO_UPLOAD = "./imdb_top_1000.csv"

# =========================
# Utilidades de parsing
# =========================

def tentar_converter_para_float(texto: Any) -> Optional[float]:
    """Converte strings como '$28.3M', '1,234,567', '142 min' para float. Retorna None se não conseguir."""
    if texto is None:
        return None
    bruto = str(texto).strip()
    if not bruto:
        return None

    # Remove símbolos monetários e espaços; remove vírgulas usadas como separador de milhar
    normalizado = (
        bruto.replace("R$", "").replace("$", "").replace("€", "").replace("£", "").replace(" ", "")
        .replace(",", "")
    )

    multiplicador = 1.0
    # Sufixos K/M/B (mil, milhão, bilhão)
    if normalizado.endswith(("k", "K")):
        multiplicador = 1e3
        normalizado = normalizado[:-1]
    elif normalizado.endswith(("m", "M")):
        multiplicador = 1e6
        normalizado = normalizado[:-1]
    elif normalizado.endswith(("b", "B")):
        multiplicador = 1e9
        normalizado = normalizado[:-1]

    try:
        return float(normalizado) * multiplicador
    except ValueError:
        # Extrai o primeiro número em strings como "142min" ou "142 min"
        encontrado = re.search(r"([-+]?\d+(\.\d+)?)", bruto)
        if encontrado:
            try:
                return float(encontrado.group(1))
            except ValueError:
                return None
        return None


def separar_multivalor(texto: Any) -> List[str]:
    """Divide campos multi-valor por vírgula ou pipe (',', '|')."""
    if texto is None:
        return []
    partes = re.split(r"[,\|]", str(texto))
    return [p.strip() for p in partes if p.strip()]


def e_numero(valor: Any) -> bool:
    try:
        float(valor)
        return True
    except Exception:
        return False


# =========================
# Similaridades (0..1)
# =========================

def similaridade_numerica(valor_a: Optional[float], valor_b: Optional[float], minimo: float, maximo: float) -> float:
    """1 - distância min–max; 0 se faltante."""
    if valor_a is None or valor_b is None:
        return 0.0
    if maximo <= minimo:
        return 1.0  # sem variação na coluna
    distancia = abs(valor_a - valor_b) / (maximo - minimo)
    return 1.0 - max(0.0, min(1.0, distancia))


def similaridade_categorica(valor_a: Optional[str], valor_b: Optional[str]) -> float:
    if valor_a is None or valor_b is None:
        return 0.0
    return 1.0 if str(valor_a).strip().lower() == str(valor_b).strip().lower() else 0.0


def similaridade_multivalor(lista_a: List[str], lista_b: List[str]) -> float:
    """Jaccard: |A∩B| / |A∪B|."""
    conjunto_a = {x.lower() for x in lista_a if x}
    conjunto_b = {x.lower() for x in lista_b if x}
    if not conjunto_a and not conjunto_b:
        return 1.0
    if not conjunto_a or not conjunto_b:
        return 0.0
    intersecao = len(conjunto_a & conjunto_b)
    uniao = len(conjunto_a | conjunto_b)
    return intersecao / uniao if uniao > 0 else 0.0


# =========================
# Dataset / Casos
# =========================

NUMERICAS_COMUNS = ["Released_Year", "Runtime", "IMDB_Rating", "Meta_score", "No_of_Votes", "Gross"]
MULTIVALOR_COMUNS = ["Genre", "Genres"]
CATEGORICAS_COMUNS = ["Certificate", "Rated"]
TITULO_POSSIVEIS = ["Series_Title", "Title", "Movie", "Name"]

@dataclass
class Caso:
    """Um caso (filme) é representado como um dicionário coluna->valor já pré-processado."""
    atributos: Dict[str, Any]


class DatasetFilmes:
    """Carrega e prepara o CSV, detectando colunas e faixas numéricas."""

    def __init__(self, caminho_csv: str):
        self.caminho_csv = caminho_csv
        self.casos: List[Caso] = []
        self.colunas: List[str] = []
        self.colunas_numericas: List[str] = []
        self.colunas_multivalor: List[str] = []
        self.colunas_categoricas: List[str] = []
        self.estatisticas_min_max: Dict[str, Tuple[float, float]] = {}
        self.chave_titulo: Optional[str] = None

    def carregar(self) -> None:
        with open(self.caminho_csv, "r", encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            linhas = [dict(l) for l in leitor]

        if not linhas:
            print("CSV vazio.")
            sys.exit(1)

        self.colunas = list(linhas[0].keys())
        self.colunas_numericas = [c for c in NUMERICAS_COMUNS if c in self.colunas]
        self.colunas_multivalor = [c for c in MULTIVALOR_COMUNS if c in self.colunas]
        self.colunas_categoricas = [c for c in CATEGORICAS_COMUNS if c in self.colunas]

        # Detecta coluna de título, se houver
        for candidato in TITULO_POSSIVEIS:
            if candidato in self.colunas:
                self.chave_titulo = candidato
                break

        # Pré-processa: numéricos e multi-valor
        for linha in linhas:
            atributos: Dict[str, Any] = dict(linha)  # cópia

            for coluna in self.colunas_numericas:
                atributos[coluna] = tentar_converter_para_float(atributos.get(coluna))

            for coluna in self.colunas_multivalor:
                atributos[coluna] = separar_multivalor(atributos.get(coluna))

            self.casos.append(Caso(atributos=atributos))

        # Min/max por coluna numérica (para normalização min–max)
        self.estatisticas_min_max = self._calcular_min_max()

    def _calcular_min_max(self) -> Dict[str, Tuple[float, float]]:
        estatisticas: Dict[str, Tuple[float, float]] = {}
        for coluna in self.colunas_numericas:
            valores = [
                caso.atributos.get(coluna)
                for caso in self.casos
                if caso.atributos.get(coluna) is not None and not math.isnan(caso.atributos.get(coluna))
            ]
            estatisticas[coluna] = (min(valores), max(valores)) if valores else (0.0, 1.0)
        return estatisticas

    def listar_amostra(self, tamanho: int = 25) -> None:
        """Mostra os primeiros 'tamanho' filmes com índice para ajudar na escolha."""
        print("\nAmostra de filmes (índice -> título):")
        for indice, caso in enumerate(self.casos[:max(1, tamanho)]):
            titulo = self.obter_titulo(caso)
            print(f"{indice:>4}  {titulo}")

    def obter_titulo(self, caso: Caso) -> str:
        if self.chave_titulo is None:
            return "(sem título)"
        return str(caso.atributos.get(self.chave_titulo) or "(sem título)")

    def selecionar_por_indice(self, indice: int) -> Caso:
        if indice < 0 or indice >= len(self.casos):
            raise IndexError("Índice fora do intervalo da base.")
        return self.casos[indice]

    def selecionar_por_titulo(self, termo: str) -> Caso:
        """Seleciona o primeiro filme cujo título contenha o termo (case-insensitive)."""
        termo_normalizado = termo.strip().lower()
        for caso in self.casos:
            if termo_normalizado in self.obter_titulo(caso).lower():
                return caso
        raise ValueError(f"Nenhum filme contendo '{termo}' foi encontrado.")


# =========================
# Motor RBC
# =========================

class RBCFilmes:
    """Implementa cálculo de similaridade, recuperação de vizinhos e predição."""

    def __init__(self, dataset: DatasetFilmes, pesos_por_coluna: Optional[Dict[str, float]] = None):
        self.dataset = dataset
        self.pesos = pesos_por_coluna or {}

    def _similaridade_caso(self, consulta: Caso, candidato: Caso, coluna_alvo: Optional[str]) -> float:
        """Similaridade média ponderada (0..1) agregando cada coluna relevante."""
        soma_ponderada = 0.0
        soma_pesos = 0.0

        # Numéricas
        for coluna in self.dataset.colunas_numericas:
            if coluna == coluna_alvo:
                continue  # evita "vazar" informação do alvo
            peso = self.pesos.get(coluna, 1.0)
            if peso <= 0:
                continue
            valor_a = consulta.atributos.get(coluna)
            valor_b = candidato.atributos.get(coluna)
            minimo, maximo = self.dataset.estatisticas_min_max.get(coluna, (0.0, 1.0))
            s = similaridade_numerica(valor_a, valor_b, minimo, maximo)
            soma_ponderada += peso * s
            soma_pesos += peso

        # Multivalor
        for coluna in self.dataset.colunas_multivalor:
            if coluna == coluna_alvo:
                continue
            peso = self.pesos.get(coluna, 1.0)
            if peso <= 0:
                continue
            lista_a = consulta.atributos.get(coluna, [])
            lista_b = candidato.atributos.get(coluna, [])
            s = similaridade_multivalor(lista_a, lista_b)
            soma_ponderada += peso * s
            soma_pesos += peso

        # Categóricas: por padrão peso 0 (a menos que o usuário configure)
        for coluna in self.dataset.colunas_categoricas:
            if coluna == coluna_alvo:
                continue
            peso = self.pesos.get(coluna, 0.0)
            if peso <= 0:
                continue
            s = similaridade_categorica(consulta.atributos.get(coluna), candidato.atributos.get(coluna))
            soma_ponderada += peso * s
            soma_pesos += peso

        return (soma_ponderada / soma_pesos) if soma_pesos > 0 else 0.0

    def recuperar_vizinhos(self, consulta: Caso, k: int, coluna_alvo: Optional[str]) -> List[Tuple[float, Caso]]:
        """Ordena todos os casos por similaridade decrescente e retorna os k melhores (excluindo a própria consulta)."""
        resultados: List[Tuple[float, Caso]] = []
        for caso in self.dataset.casos:
            if caso is consulta:
                continue  # leave-one-out
            sim = self._similaridade_caso(consulta, caso, coluna_alvo)
            resultados.append((sim, caso))
        resultados.sort(key=lambda par: par[0], reverse=True)
        return resultados[:max(1, k)]

    def predizer(self, vizinhos: List[Tuple[float, Caso]], coluna_alvo: str) -> Tuple[Any, Dict[str, float]]:
        """
        Se a coluna-alvo parece numérica => média ponderada.
        Se categórica => voto ponderado.
        Retorna (predicao, detalhes_por_valor).
        """
        tipo_numerico = self._alvo_parece_numerico(vizinhos, coluna_alvo)
        if tipo_numerico is None:
            return None, {}

        if tipo_numerico:
            numerador = 0.0
            denominador = 0.0
            for similaridade, caso in vizinhos:
                valor = caso.atributos.get(coluna_alvo)
                if valor is None:
                    continue
                valor = float(valor)
                peso = max(1e-9, similaridade)
                numerador += peso * valor
                denominador += peso
            return (numerador / denominador) if denominador > 0 else None, {}

        # categórico: voto ponderado
        acumulador: Dict[str, float] = {}
        for similaridade, caso in vizinhos:
            valor = str(caso.atributos.get(coluna_alvo) or "").strip()
            if not valor:
                continue
            acumulador[valor] = acumulador.get(valor, 0.0) + max(1e-9, similaridade)
        if not acumulador:
            return None, {}
        vencedor = max(acumulador.items(), key=lambda item: item[1])[0]
        return vencedor, acumulador

    @staticmethod
    def _alvo_parece_numerico(vizinhos: List[Tuple[float, Caso]], coluna_alvo: str) -> Optional[bool]:
        """Inspeciona vizinhos para inferir tipo do alvo."""
        for _, caso in vizinhos:
            valor = caso.atributos.get(coluna_alvo)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                continue
            if isinstance(valor, (int, float)) or e_numero(valor):
                return True
            else:
                return False
        return None


# =========================
# CLI / Orquestração
# =========================

def interpretar_pesos(texto: Optional[str]) -> Dict[str, float]:
    """Converte 'IMDB_Rating=2;Genre=1.5;Runtime=0.5' em dict {'IMDB_Rating':2.0,...}."""
    if not texto:
        return {}
    resultado: Dict[str, float] = {}
    for parte in texto.split(";"):
        if "=" in parte:
            chave, valor = parte.split("=", 1)
            try:
                resultado[chave.strip()] = float(valor.strip())
            except ValueError:
                pass
    return resultado


def escolher_filme(dataset: DatasetFilmes,
                   titulo_substring: Optional[str],
                   indice: Optional[int],
                   listar_amostra: bool) -> Caso:
    """Escolhe o filme que servirá de CONSULTA."""
    if listar_amostra:
        dataset.listar_amostra()

    if indice is not None:
        return dataset.selecionar_por_indice(indice)

    if titulo_substring:
        return dataset.selecionar_por_titulo(titulo_substring)

    # Se nada foi fornecido, mostre amostra e peça um índice interativamente.
    dataset.listar_amostra()
    entrada = input("\nDigite o índice do filme que deseja usar como consulta: ").strip()
    if not entrada.isdigit():
        raise ValueError("Índice inválido.")
    return dataset.selecionar_por_indice(int(entrada))


def exibir_vizinhos(dataset: DatasetFilmes, vizinhos: List[Tuple[float, Caso]]) -> None:
    print("\n=== k casos mais similares ===")
    for posicao, (similaridade, caso) in enumerate(vizinhos, start=1):
        titulo = dataset.obter_titulo(caso)
        certificado = caso.atributos.get("Certificate", caso.atributos.get("Rated", ""))
        generos = caso.atributos.get("Genre") or caso.atributos.get("Genres") or []
        generos_str = ", ".join(generos) if isinstance(generos, list) else str(generos)
        ano = caso.atributos.get("Released_Year")
        print(f"{posicao:>2}. sim={similaridade*100:5.1f}% | {titulo} | Ano={ano} | Cert={certificado} | Gêneros={generos_str}")


def exibir_resultado_predicao(predicao: Any, distribuicao: Dict[str, float]) -> None:
    print("\n=== Predição ===")
    if predicao is None:
        print("Não foi possível estimar o alvo com os vizinhos atuais.")
        return
    if isinstance(predicao, (int, float)):
        print(f"Estimativa (média ponderada): {predicao:.3f}")
    else:
        print(f"Classe prevista (voto ponderado): {predicao}")
        if distribuicao:
            peso_total = sum(distribuicao.values()) or 1.0
            print("Distribuição (peso relativo):")
            for valor, peso in sorted(distribuicao.items(), key=lambda item: item[1], reverse=True):
                percentual = 100.0 * peso / peso_total
                print(f"  - {valor}: {percentual:5.1f}%")


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="RBC para CSV de filmes — escolhe um filme da base e encontra os k mais parecidos."
    )
    # Torna o caminho do CSV opcional; por padrão usa a base enviada
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=CSV_PADRAO_UPLOAD,
        help=f"Caminho para o CSV de filmes (padrão: '{CSV_PADRAO_UPLOAD}')."
    )
    parser.add_argument("--k", type=int, default=5, help="Número de vizinhos a recuperar.")
    parser.add_argument("--movie-title", type=str, default=None,
                        help="Substring (case-insensitive) do título do filme a usar como CONSULTA.")
    parser.add_argument("--movie-index", type=int, default=None,
                        help="Índice do filme (veja --list-sample).")
    parser.add_argument("--predict", type=str, default=None,
                        help="Coluna alvo para prever (ex.: Certificate, IMDB_Rating).")
    parser.add_argument("--weights", type=str, default=None,
                        help='Pesos por coluna, ex.: "IMDB_Rating=2;Genre=1.5;Runtime=0.5"')
    parser.add_argument("--list-sample", action="store_true",
                        help="Exibe uma amostra (primeiros 25) para auxiliar na escolha do filme.")
    return parser


def main() -> None:
    argumentos = construir_parser().parse_args()

    # 1) Carregar dataset (usa o CSV padrão do upload se nenhum caminho for informado)
    dataset = DatasetFilmes(argumentos.csv_path)
    dataset.carregar()

    # 2) Interpretar pesos opcionais
    pesos = interpretar_pesos(argumentos.weights)

    # 3) Escolher filme de consulta (da própria base)
    consulta = escolher_filme(
        dataset=dataset,
        titulo_substring=argumentos.movie_title,
        indice=argumentos.movie_index,
        listar_amostra=argumentos.list_sample,
    )

    # 4) Executar RBC
    motor = RBCFilmes(dataset=dataset, pesos_por_coluna=pesos)
    coluna_alvo = argumentos.predict  # pode ser None
    vizinhos = motor.recuperar_vizinhos(consulta=consulta, k=argumentos.k, coluna_alvo=coluna_alvo)

    # 5) Mostrar resultados
    titulo_consulta = dataset.obter_titulo(consulta)
    print(f"\nFilme de CONSULTA: {titulo_consulta}")
    exibir_vizinhos(dataset, vizinhos)

    # 6) Predição (opcional)
    if coluna_alvo:
        predicao, distribuicao = motor.predizer(vizinhos=vizinhos, coluna_alvo=coluna_alvo)
        exibir_resultado_predicao(predicao, distribuicao)

    # 7) Dica de pesos
    if not argumentos.weights:
        print("\n[Dica] Ajuste pesos com --weights, por exemplo: --weights \"IMDB_Rating=2;Genre=1.5;Runtime=0.5\"")


if __name__ == "__main__":
    main()
