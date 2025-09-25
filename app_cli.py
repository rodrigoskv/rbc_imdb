"""
Aplicação CLI para treinar/testar o RBC com a base IMDB Top 1000.

- Usa /mnt/data/imdb_top_1000.csv se existir (ambiente ChatGPT).
- Caso contrário, ajuste a constante `CAMINHO_CSV` para o seu arquivo local.

Execute:
    python app_cli.py
"""
import os
from rbc.data_io import carregar_casos_de_csv
from rbc.split import dividir_treino_teste
from rbc.rbc import RBC
from rbc.metrics import acuracia
from rbc.domain import CasoFilme

# Tenta o caminho padrão do ambiente do ChatGPT; ajuste se necessário
from rbc.config import DEFAULT_DATASET_PATH
CAMINHO_PADRAO = DEFAULT_DATASET_PATH
FALLBACK_CHATGPT = "/mnt/data/imdb_top_1000.csv"
CAMINHO_CSV = CAMINHO_PADRAO if os.path.exists(CAMINHO_PADRAO) else (FALLBACK_CHATGPT if os.path.exists(FALLBACK_CHATGPT) else "imdb_top_1000.csv")

def main():
    print(f"Carregando CSV: {CAMINHO_CSV!r}")
    casos = carregar_casos_de_csv(CAMINHO_CSV)
    print(f"Total de casos carregados: {len(casos)}")

    treino, teste = dividir_treino_teste(casos, proporcao_treino=0.8, seed=42)
    print(f"Tamanho treino: {len(treino)} | Tamanho teste: {len(teste)}")

    # RBC 1-NN (k=1) por padrão
    rbc = RBC(k=1)
    rbc.ajustar(treino)

    # Avaliação simples
    y_true = [c.label for c in teste]
    y_pred = rbc.prever_lote(teste)
    acc = acuracia(y_true, y_pred)
    print(f"Acurácia (k=1): {acc * 100:.2f}%")

    # Demonstração de previsões
    print("\nExemplos de previsões:")
    for i, caso in enumerate(teste[:5], start=1):
        previsto = rbc.prever(caso)
        print(f"{i}. Real: {caso.label:15s} | Previsto: {previsto:15s} | rating={caso.imdb_rating} | meta={caso.meta_score}")

if __name__ == '__main__':
    main()
