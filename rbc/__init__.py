"""
Pacote `rbc` — Implementação simples de RBC (k-NN) para a base IMDB.

Módulos principais:
- domain: tipos e dataclasses do domínio
- preprocessing: limpeza e transformação de campos (gênero, escala de features, etc.)
- data_io: leitura do CSV e construção dos casos
- rbc: classificador RBC (k-NN) com explicabilidade (vizinhos)
- metrics: métricas simples (acurácia)
- split: divisão treino/teste
"""
