"""
Aplicação CLI para o sistema de recomendação de filmes com RBC.

Execute:
    python app_cli.py
"""
import os
from rbc.data_io import carregar_casos_de_csv
from rbc.rbc import RBC
from rbc.domain import CasoFilme

from rbc.config import DEFAULT_DATASET_PATH
CAMINHO_PADRAO = DEFAULT_DATASET_PATH

def recomendar_filmes_similares(rbc: RBC, filme_alvo: str, casos: list, top_k: int = 5):
    """Recomenda filmes similares a um filme específico"""
    # Encontrar o filme alvo
    caso_alvo = next((c for c in casos if c.titulo and c.titulo.lower() == filme_alvo.lower()), None)
    
    if not caso_alvo:
        print(f"❌ Filme '{filme_alvo}' não encontrado na base de dados.")
        return
    
    print(f"🎬 Buscando filmes similares a: {caso_alvo.titulo}")
    print(f"   ⭐ IMDB Rating: {caso_alvo.imdb_rating}")
    print(f"   🎯 Meta Score: {caso_alvo.meta_score}")
    print(f"   🎭 Gênero: {caso_alvo.label}")
    print()
    
    # Encontrar recomendações
    recomendacoes = rbc.vizinhos_mais_proximos(caso_alvo, top_n=top_k+1)
    
    # Pular o primeiro (é o próprio filme)
    recomendacoes = recomendacoes[1:]
    
    print("🎭 FILMES RECOMENDADOS:")
    print("-" * 80)
    for i, (distancia, caso) in enumerate(recomendacoes, 1):
        similaridade = 100 - (distancia * 10)  # Converter distância em porcentagem de similaridade
        print(f"{i}. {caso.titulo}")
        print(f"   ⭐ Rating: {caso.imdb_rating} | 🎯 Meta: {caso.meta_score} | 🎭 Gênero: {caso.label}")
        print(f"   📊 Similaridade: {similaridade:.1f}%")
        print()

def main():
    print("🎬 SISTEMA DE RECOMENDAÇÃO DE FILMES - RBC")
    print("=" * 50)
    
    print(f"📁 Carregando base de dados: {CAMINHO_PADRAO}")
    casos = carregar_casos_de_csv(CAMINHO_PADRAO)
    print(f"✅ Total de filmes carregados: {len(casos)}")
    
    # Criar e treinar o RBC
    rbc = RBC(k=5)
    rbc.ajustar(casos)
    print("✅ Sistema de recomendação treinado e pronto!")
    print()
    
    # Exemplo de recomendações
    filmes_exemplo = ["The Godfather", "The Dark Knight", "Pulp Fiction", "Forrest Gump"]
    
    print("🎯 EXEMPLOS DE RECOMENDAÇÕES:")
    print()
    
    for filme in filmes_exemplo:
        if any(c.titulo and c.titulo.lower() == filme.lower() for c in casos):
            recomendar_filmes_similares(rbc, filme, casos, top_k=3)
            print()

if __name__ == '__main__':
    main()