# RBC IMDB — Projeto em Python (Raciocínio Baseado em Casos)

Este projeto implementa um **RBC (Case-Based Reasoning)** simples (k-NN) aplicado na base **IMDB Top 1000**.
- **Rótulo (label):** o **primeiro gênero** do campo `Genre`.
- **Atributos numéricos (features):** `IMDB_Rating` e `Meta_score` (este é escalado por 10 para ficar em ~0..10).

Inclui:
- **Biblioteca** (`rbc/`) com código limpo
- **Front-end** com **Streamlit** (`frontend/streamlit_app.py`) para **filtrar e visualizar** dados e **testar previsões**.

## Requisitos

- Python 3.9+
- Instalar dependências:
```bash
python -m venv .venv
pip install -r requirements.txt
```

## Dataset
- Caso esteja rodando localmente, baixe o **IMDB Top 1000**  

## Executar o CLI

```bash
python app_cli.py
```
Você pode ajustar o caminho do CSV e outros parâmetros no arquivo.

## Executar o Front-end (Streamlit)

```bash
streamlit run frontend/streamlit_app.py
```

## Estrutura

```
rbc_imdb_python/
├─ rbc/
│  ├─ config.py           # path  
│  ├─ domain.py           # dataclasses e tipos
│  ├─ preprocessing.py    # funções de limpeza/transformação
│  ├─ data_io.py          # leitura do CSV e construção dos casos
│  ├─ rbc.py              # implementação do RBC (k-NN)
│  
│ 
├─ frontend/
│  └─ streamlit_app.py    # app web para filtrar/visualizar e prever           
└─ README.md
```

