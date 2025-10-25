#!/usr/bin/env python3
"""
Teste completo de um único leilão: Cards → Lotes → PDFs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapping.vip import LeilaoVipScraper, bancos

def testar_um_leilao_completo():
    """Testa o fluxo completo de um único leilão"""
    print("🧪 Teste Completo: Um Leilão do Bradesco")
    print("=" * 60)
    
    scraper = LeilaoVipScraper()
    url_banco = bancos["bradesco"]
    
    # Etapa 1: Extrair cards de leilões
    print("\n📋 ETAPA 1: Extraindo cards de leilões...")
    links_leiloes = scraper.extrair_cards_leiloes(url_banco)
    print(f"✅ Encontrados {len(links_leiloes)} leilões")
    
    if not links_leiloes:
        print("❌ Nenhum leilão encontrado. Abortando teste.")
        return
    
    # Pega apenas o primeiro leilão para teste
    leilao_teste = links_leiloes[0]
    print(f"\n🎯 Testando leilão: {leilao_teste}")
    
    # Etapa 2: Extrair lotes do leilão
    print("\n📦 ETAPA 2: Extraindo lotes do leilão...")
    scraper.aguardar_entre_requests(2)
    links_lotes = scraper.extrair_lotes_do_leilao(leilao_teste)
    print(f"✅ Encontrados {len(links_lotes)} lotes")
    
    if not links_lotes:
        print("⚠️  Nenhum lote encontrado neste leilão.")
        return
    
    # Etapa 3: Baixar PDFs dos lotes (testa apenas os 3 primeiros)
    print("\n📄 ETAPA 3: Baixando PDFs dos lotes...")
    lotes_teste = links_lotes[:3]  # Apenas 3 para teste
    pdfs_baixados = 0
    
    for i, lote in enumerate(lotes_teste, 1):
        print(f"\n  📦 Processando lote {i}/{len(lotes_teste)}")
        scraper.aguardar_entre_requests(1)
        
        if scraper.baixar_pdf_matricula(lote, "bradesco"):
            pdfs_baixados += 1
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DO TESTE:")
    print(f"  🏠 Leilões encontrados: {len(links_leiloes)}")
    print(f"  📦 Lotes no leilão testado: {len(links_lotes)}")
    print(f"  📄 PDFs baixados: {pdfs_baixados}/{len(lotes_teste)}")
    print(f"  📁 Arquivos: {scraper.pdfs_baixados}")
    print("=" * 60)

if __name__ == "__main__":
    testar_um_leilao_completo()
