# RBC IMDB — Projeto em Python (Raciocínio Baseado em Casos)

Este projeto implementa um **RBC (Case-Based Reasoning)** simples (k-NN) aplicado na base **IMDB Top 1000**.
- **Rótulo (label):** o **primeiro gênero** do campo `Genre`.
- **Atributos numéricos (features):** `IMDB_Rating` e `Meta_score` (este é escalado por 10 para ficar em ~0..10).

Inclui:
- **Biblioteca** (`rbc/`) com código limpo e comentado.
- **CLI** (`app_cli.py`) para treinar/testar e imprimir métricas.
- **Front-end** com **Streamlit** (`frontend/streamlit_app.py`) para **filtrar e visualizar** dados e **testar previsões**.

## Requisitos

- Python 3.9+
- Instalar dependências:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

## Dataset

- Se você estiver no ChatGPT com o arquivo já enviado, o caminho padrão `/mnt/data/imdb_top_1000.csv` será detectado automaticamente.
- Caso esteja rodando localmente, baixe o **IMDB Top 1000** (Kaggle) e aponte para o CSV no **Streamlit** (via uploader) ou passe o caminho no `app_cli.py`.

## Executar o CLI

```bash
python app_cli.py
```
Você pode ajustar o caminho do CSV e outros parâmetros no arquivo.

## Executar o Front-end (Streamlit)

```bash
streamlit run frontend/streamlit_app.py
```

No app web:
- Faça **upload** do CSV (ou deixe o app usar o caminho padrão, se existir).
- Filtre por gênero, faixa de `IMDB_Rating` e `Meta_score`.
- Visualize a tabela e um **gráfico de dispersão**.
- Teste uma **previsão** informando `IMDB_Rating` e `Meta_score` e escolha **K**.

## Estrutura

```
rbc_imdb_python/
├─ rbc/
│  ├─ __init__.py
│  ├─ domain.py           # dataclasses e tipos
│  ├─ preprocessing.py    # funções de limpeza/transformação
│  ├─ data_io.py          # leitura do CSV e construção dos casos
│  ├─ rbc.py              # implementação do RBC (k-NN)
│  ├─ metrics.py          # métricas simples (acurácia)
│  └─ split.py            # utilitários de divisão treino/teste
├─ frontend/
│  └─ streamlit_app.py    # app web para filtrar/visualizar e prever
├─ app_cli.py             # linha de comando para treino/teste
├─ requirements.txt
└─ README.md
```

## Observações

- O **RBC** foi escrito **sem dependências** externas.
- O **front-end** e a **carga/visualização** usam **pandas** e **Streamlit** (ver `requirements.txt`).
- Se preferir **não usar pandas**, é possível adaptar facilmente a leitura para `csv` puro; mantivemos pandas para melhorar a UX no front.

## Início Rápido (dataset incluído)

Este pacote já vem com **data/imdb_top_1000.csv** e está **pré-configurado** para usar esse arquivo por padrão.

### Windows
- CLI: `run_cli.bat`
- Front: `run_front.bat`

### Linux/Mac
- CLI: `./run_cli.sh`
- Front: `./run_front.sh`

Você também pode enviar um CSV diferente no próprio app Streamlit (sidebar).
