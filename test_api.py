#!/usr/bin/env python3
"""
Script para testar a API de Scraping de Leilões
"""

import requests
import json
from datetime import datetime

# URL base da API
BASE_URL = "http://localhost:8000"

def test_root():
    """Testa o endpoint raiz"""
    print("🧪 Testando endpoint raiz...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_status():
    """Testa o endpoint de status"""
    print("🧪 Testando endpoint de status...")
    response = requests.get(f"{BASE_URL}/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_listar_pdfs():
    """Testa o endpoint de listagem de PDFs"""
    print("🧪 Testando listagem de PDFs...")
    response = requests.get(f"{BASE_URL}/pdfs")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_scraping():
    """Testa o endpoint de scraping"""
    print("🧪 Testando scraping do LeilaoVip...")
    print("⚠️  ATENÇÃO: Este teste fará scraping real do site!")
    
    confirmar = input("Deseja continuar? (s/N): ").lower().strip()
    if confirmar != 's':
        print("Teste cancelado.")
        return
    
    print("🚀 Iniciando scraping...")
    response = requests.post(f"{BASE_URL}/scraping/vip")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def main():
    """Executa todos os testes"""
    print("🏠 Testador da API de Scraping de Leilões")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    try:
        test_root()
        test_status()
        test_listar_pdfs()
        test_scraping()
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
        print("Certifique-se de que a API está rodando em http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")

if __name__ == "__main__":
    main()
