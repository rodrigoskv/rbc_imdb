from pathlib import Path

# Caminho padrão incorporado ao projeto (data/imdb_top_1000.csv)
DEFAULT_DATASET_PATH: str = str(Path(__file__).resolve().parent.parent / "data" / "imdb_top_1000.csv")
