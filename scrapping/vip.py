import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin, urlparse
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

palavra_chave = "Extrajudicial"

# URLs dos bancos
bancos = {
    "bradesco": "https://www.leilaovip.com.br/agenda?Filtro.ComitenteId=8936579c-897d-425c-a252-b18c011710bf",
    "banco_pan": "https://www.leilaovip.com.br/agenda?Filtro.ComitenteId=ddbba3da-1e3b-46f6-8f6c-b18e012f43d7",
    "bv": "https://www.leilaovip.com.br/agenda?Filtro.ComitenteId=729ccab8-f1ba-4ce6-85ce-b18c0114503a"
}

class LeilaoVipScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.links_processados = set()  # Para evitar duplicatas
        self.pdfs_baixados = []
        
    def aguardar_entre_requests(self, segundos=2):
        """Evita sobrecarregar o servidor"""
        time.sleep(segundos)
    
    def extrair_links_leiloes(self, url):
        """Extrai links dos leilões da página principal"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procura divs com a classe específica
            divs_leiloes = soup.find_all('div', class_='col d-flex justify-content-center')
            links = []
            
            for div in divs_leiloes:
                ancora = div.find('a')
                if ancora and ancora.get('href'):
                    link_completo = urljoin(url, ancora['href'])
                    if link_completo not in self.links_processados:
                        links.append(link_completo)
                        self.links_processados.add(link_completo)
            
            return links
            
        except Exception as e:
            logger.error(f"Erro ao extrair links de {url}: {e}")
            return []
    
    def verificar_palavra_chave(self, soup):
        """Verifica se a página contém a palavra-chave"""
        texto_pagina = soup.get_text().lower()
        return palavra_chave.lower() in texto_pagina
    
    def baixar_pdf_matricula(self, url_leilao, nome_banco):
        """Baixa o PDF da matrícula se encontrar o link"""
        try:
            response = self.session.get(url_leilao)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Verifica se contém a palavra-chave
            if not self.verificar_palavra_chave(soup):
                logger.info(f"Palavra-chave '{palavra_chave}' não encontrada em {url_leilao}")
                return False
            
            # Procura link da matrícula
            link_matricula = soup.find('a', string=lambda text: text and 'Matrícula' in text)
            
            if link_matricula and link_matricula.get('href'):
                pdf_url = urljoin(url_leilao, link_matricula['href'])
                
                # Baixa o PDF
                pdf_response = self.session.get(pdf_url)
                pdf_response.raise_for_status()
                
                # Cria nome do arquivo
                nome_arquivo = f"{nome_banco}_{urlparse(url_leilao).path.split('/')[-1]}.pdf"
                caminho_arquivo = os.path.join('pdfs', nome_arquivo)
                
                # Cria diretório se não existir
                os.makedirs('pdfs', exist_ok=True)
                
                # Salva o PDF
                with open(caminho_arquivo, 'wb') as f:
                    f.write(pdf_response.content)
                
                self.pdfs_baixados.append(caminho_arquivo)
                logger.info(f"PDF baixado: {caminho_arquivo}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao processar {url_leilao}: {e}")
            return False
    
    def processar_banco(self, nome_banco, url_banco):
        """Processa todos os leilões de um banco"""
        logger.info(f"Processando {nome_banco}...")
        
        links_leiloes = self.extrair_links_leiloes(url_banco)
        logger.info(f"Encontrados {len(links_leiloes)} leilões em {nome_banco}")
        
        for link in links_leiloes:
            self.aguardar_entre_requests()
            self.baixar_pdf_matricula(link, nome_banco)
    
    def executar_scraping(self):
        """Executa o scraping completo"""
        logger.info("Iniciando scraping do LeilaoVip...")
        
        for nome_banco, url_banco in bancos.items():
            self.processar_banco(nome_banco, url_banco)
            self.aguardar_entre_requests(3)  # Pausa maior entre bancos
        
        logger.info(f"Scraping concluído! {len(self.pdfs_baixados)} PDFs baixados.")
        return self.pdfs_baixados

def iniciar_scraping_vip():
    """Função principal para iniciar o scraping do LeilaoVip"""
    scraper = LeilaoVipScraper()
    pdfs = scraper.executar_scraping()
    
    print(f"\n📄 PDFs baixados ({len(pdfs)}):")
    for pdf in pdfs:
        print(f"  • {pdf}")
    
    return pdfs