#!/usr/bin/env python3
"""
Script de teste direto para debug do scraping
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapping.vip import testar_um_banco

if __name__ == "__main__":
    print("🧪 Teste direto do scraping")
    print("=" * 40)
    
    # Testa o Bradesco
    links = testar_um_banco("bradesco")
    
    print(f"\n🎯 Resultado: {len(links)} links encontrados")
    if links:
        print("\n📋 Links encontrados:")
        for i, link in enumerate(links, 1):
            print(f"  {i}. {link}")
    else:
        print("❌ Nenhum link de leilão válido encontrado")
