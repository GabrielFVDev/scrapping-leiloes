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
    
    def extrair_cards_leiloes(self, url):
        """Etapa 1: Extrai cards de leilões (primeira imagem do usuário)"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links_leiloes = []
            base_url = '/'.join(url.split('/')[:3])  # https://www.leilaovip.com.br
            
            # Verifica se a página usa carregamento AJAX
            placeholder = soup.find('div', {'id': 'placeholder'})
            ajax_url_element = soup.find(attrs={'data-ajax-url': lambda x: x and 'pesquisarEventos' in x})
            
            if placeholder and ajax_url_element:
                ajax_url = ajax_url_element.get('data-ajax-url')
                logger.info(f"🔄 Detectado carregamento AJAX: {ajax_url}")
                
                # Extrai parâmetros da URL original (filtro do comitente)
                from urllib.parse import parse_qs, urlparse
                parsed_url = urlparse(url)
                params = parse_qs(parsed_url.query)
                
                # Tenta diferentes estratégias de requisição
                strategies = [
                    self.try_ajax_get_with_params,
                    self.try_ajax_post_form,
                    self.try_direct_search
                ]
                
                for strategy in strategies:
                    try:
                        links_leiloes = strategy(base_url, ajax_url, params)
                        if links_leiloes:
                            logger.info(f"✅ Estratégia {strategy.__name__} funcionou!")
                            break
                    except Exception as e:
                        logger.warning(f"⚠️  Estratégia {strategy.__name__} falhou: {e}")
            
            # Se não encontrou via AJAX, tenta buscar padrões específicos
            if not links_leiloes:
                logger.info("🔎 Tentando buscar padrões específicos...")
                links_leiloes = self.buscar_links_alternativos(soup, base_url)
            
            return links_leiloes
            
        except Exception as e:
            logger.error(f"Erro ao extrair cards de leilões: {e}")
            return []

    def try_ajax_get_with_params(self, base_url, ajax_url, params):
        """Estratégia 1: GET com parâmetros"""
        ajax_full_url = urljoin(base_url, ajax_url)
        if params:
            import urllib.parse
            query_string = urllib.parse.urlencode(params, doseq=True)
            ajax_full_url = f"{ajax_full_url}&{query_string}"
        
        logger.info(f"📡 Estratégia GET: {ajax_full_url}")
        
        ajax_response = self.session.get(ajax_full_url)
        ajax_response.raise_for_status()
        ajax_soup = BeautifulSoup(ajax_response.content, 'html.parser')
        
        logger.info(f"✅ Resposta recebida: {len(ajax_response.content)} bytes")
        return self.processar_cards_html(ajax_soup, base_url)

    def try_ajax_post_form(self, base_url, ajax_url, params):
        """Estratégia 2: POST simulando formulário"""
        ajax_full_url = urljoin(base_url, ajax_url)
        
        # Dados do formulário baseados na estrutura HTML
        form_data = {
            'Filtro.LocalEstadoId': '',
            'Filtro.LocalCidade': '',
            'Filtro.SegmentoId': '',
            'Filtro.DataInicial': '',
            'Filtro.DataFinal': '',
            'Filtro.EventoCodigo': '',
            'Filtro.CurrentPage': '1'
        }
        
        # Adiciona o filtro do comitente se disponível
        if params and 'Filtro.ComitenteId' in params:
            form_data['Filtro.ComitenteId'] = params['Filtro.ComitenteId'][0]
        
        logger.info(f"📡 Estratégia POST: {ajax_full_url}")
        logger.info(f"📊 Dados do formulário: {form_data}")
        
        ajax_response = self.session.post(ajax_full_url, data=form_data)
        ajax_response.raise_for_status()
        ajax_soup = BeautifulSoup(ajax_response.content, 'html.parser')
        
        logger.info(f"✅ Resposta POST recebida: {len(ajax_response.content)} bytes")
        
        return self.processar_cards_html(ajax_soup, base_url)

    def try_direct_search(self, base_url, ajax_url, params):
        """Estratégia 3: Busca direta por URLs conhecidas"""
        logger.info("📡 Estratégia busca direta")
        
        # Tenta URLs diretas baseadas em padrões conhecidos
        urls_diretas = [
            f"{base_url}/agenda",
            f"{base_url}/leiloes",
            f"{base_url}/eventos"
        ]
        
        # Se tem parâmetros de comitente, adiciona às URLs
        if params and 'Filtro.ComitenteId' in params:
            comitente_id = params['Filtro.ComitenteId'][0]
            urls_diretas.extend([
                f"{base_url}/agenda?ComitenteId={comitente_id}",
                f"{base_url}/leiloes?ComitenteId={comitente_id}"
            ])
        
        for url_direta in urls_diretas:
            try:
                logger.info(f"� Tentando URL direta: {url_direta}")
                response = self.session.get(url_direta)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                links = self.processar_cards_html(soup, base_url)
                if links:
                    logger.info(f"✅ URL direta funcionou: {url_direta}")
                    return links
                    
            except Exception as e:
                logger.warning(f"⚠️  URL direta falhou {url_direta}: {e}")
        
        return []
    
    def buscar_links_alternativos(self, soup, base_url):
        """Busca alternativa quando não encontra cards de leilões"""
        links_leiloes = []
        
        logger.info("🔍 Buscando por padrões alternativos...")
        
        # Estratégia 1: Procurar por qualquer link que contenha "leilao" e não seja rede social
        todos_links = soup.find_all('a', href=True)
        termos_excluir = ['facebook', 'twitter', 'instagram', 'youtube', 'tiktok', 'blog']
        
        for link in todos_links:
            href = link.get('href', '').lower()
            texto = link.get_text(strip=True)
            
            # Filtra redes sociais e links de navegação
            if any(termo in href for termo in termos_excluir):
                continue
                
            # Procura por padrões que podem indicar leilões
            if any(padrao in href for padrao in ['leilao', 'evento', 'detalhes']):
                # Verifica se tem ID ou parâmetros que indicam leilão específico
                if '=' in href or len(href.split('/')) > 2:
                    link_completo = urljoin(base_url, href)
                    if link_completo not in self.links_processados:
                        links_leiloes.append(link_completo)
                        self.links_processados.add(link_completo)
                        logger.info(f"🔗 Link alternativo encontrado: {texto[:30]} -> {href}")
        
        # Estratégia 2: Procurar por scripts ou dados JSON que podem conter URLs
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                script_content = script.string.lower()
                if 'leilao' in script_content or 'evento' in script_content:
                    logger.info("📜 Script com referência a leilão encontrado")
                    # Aqui poderia extrair URLs do JavaScript, mas é mais complexo
        
        # Estratégia 3: Verificar se existem iframes ou conteúdo carregado dinamicamente
        iframes = soup.find_all('iframe')
        if iframes:
            logger.info(f"🖼️  {len(iframes)} iframes encontrados (possível conteúdo dinâmico)")
        
        # Estratégia 4: Procurar por elementos com data-attributes que podem indicar carregamento dinâmico
        elementos_data = soup.find_all(attrs=lambda x: x and isinstance(x, dict) and any(
            attr.startswith('data-') for attr in x.keys()
        ))
        
        elementos_relevantes = []
        for elem in elementos_data:
            for attr, value in elem.attrs.items():
                if attr.startswith('data-') and any(termo in str(value).lower() for termo in ['leilao', 'evento', 'load']):
                    elementos_relevantes.append((elem, attr, value))
        
        if elementos_relevantes:
            logger.info(f"📊 {len(elementos_relevantes)} elementos com data-attributes relevantes encontrados")
            for elem, attr, value in elementos_relevantes[:3]:
                logger.info(f"  - {elem.name}.{attr}: {str(value)[:50]}")
        
        logger.info(f"🔍 Busca alternativa encontrou {len(links_leiloes)} possíveis links")
        return links_leiloes

    def processar_cards_html(self, soup, base_url):
        """Processa HTML buscando cards de leilões"""
        links_leiloes = []
        
        # Estratégia melhorada: busca por padrões mais específicos
        todos_links = soup.find_all('a', href=True)
        logger.info(f"🔗 Total de links encontrados: {len(todos_links)}")
        
        # Lista todos os links para debug (apenas os primeiros 10)
        logger.info("🔍 Analisando links encontrados:")
        for i, link in enumerate(todos_links[:10], 1):
            href = link.get('href', '')
            texto = link.get_text(strip=True)[:30]
            logger.info(f"  {i}. {href} - '{texto}'")
        
        for link in todos_links:
            href = link.get('href', '')
            texto = link.get_text(strip=True)
            
            # Verifica se é um link de leilão (mais flexível)
            if any(padrao in href.lower() for padrao in ['/leilao', '/evento', '/detalhes']):
                # Verifica se contém indicadores de leilão válido no contexto
                contexto_pai = ""
                if link.parent:
                    contexto_pai = link.parent.get_text()
                
                contexto_completo = (texto + " " + contexto_pai).lower()
                
                if any(indicador in contexto_completo for indicador in [
                    'leilão', 'lotes', 'extrajudicial', 'bradesco', 'r$', 'lance', 'imóvel'
                ]):
                    link_completo = urljoin(base_url, href)
                    
                    if link_completo not in self.links_processados:
                        links_leiloes.append(link_completo)
                        self.links_processados.add(link_completo)
                        logger.info(f"🏠 Card de leilão encontrado: {texto[:50]} -> {href}")
        
        logger.info(f"🏠 Total de cards de leilões encontrados: {len(links_leiloes)}")
        return links_leiloes
    
    def extrair_lotes_do_leilao(self, url_leilao):
        """Etapa 2: Extrai lotes individuais de um leilão (segunda imagem do usuário)"""
        try:
            response = self.session.get(url_leilao)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links_lotes = []
            base_url = '/'.join(url_leilao.split('/')[:3])
            
            logger.info(f"📦 Extraindo lotes do leilão: {url_leilao}")
            
            # Estratégia 1: Procura por link de "aberto para ofertas" ou similar
            link_ofertas = soup.find('a', href=lambda x: x and ('ofertas' in x.lower() or 'lances' in x.lower()))
            
            if link_ofertas:
                url_ofertas = urljoin(base_url, link_ofertas.get('href'))
                logger.info(f"🔗 Encontrado link de ofertas/lances: {url_ofertas}")
                
                # Segue o link para a página com os lotes
                self.aguardar_entre_requests(1)
                response_ofertas = self.session.get(url_ofertas, allow_redirects=True)
                response_ofertas.raise_for_status()
                
                # URL final após redirecionamentos
                url_final = response_ofertas.url
                logger.info(f"🔗 URL final após redirecionamento: {url_final}")
                
                soup = BeautifulSoup(response_ofertas.content, 'html.parser')
            
            # Busca por links de lotes individuais
            todos_links = soup.find_all('a', href=True)
            logger.info(f"🔗 Total de links na página: {len(todos_links)}")
            
            # Estratégia principal: Busca por <select> com options de lotes
            select_lotes = soup.find('select')
            if select_lotes:
                options = select_lotes.find_all('option')
                logger.info(f"✅ Encontrado dropdown com {len(options)} opções")
                
                for option in options:
                    value = option.get('value', '')
                    if value and value != '#':  # Ignora valores vazios ou #
                        # O value geralmente é o slug do lote (ex: apartamento-com-7275-m-imbui-12667)
                        # Monta a URL completa
                        link_lote = urljoin(base_url, f'/evento/anuncio/{value}')
                        
                        if link_lote not in self.links_processados:
                            links_lotes.append(link_lote)
                            self.links_processados.add(link_lote)
                            texto_lote = option.get_text(strip=True)
                            logger.info(f"  📦 Lote #{texto_lote}: {value}")
            
            # Se ainda não tem lotes, tenta buscar por links diretos
            if not links_lotes:
                # Conta quantos links parecem ser de lotes
                links_com_lote = [l for l in todos_links if any(p in l.get('href', '').lower() for p in ['/lote', '/item', '/imovel', '/anuncio'])]
                logger.info(f"🔗 Links que contêm '/lote', '/item', '/imovel' ou '/anuncio': {len(links_com_lote)}")
                
                # Mostra alguns exemplos para debug
                if links_com_lote:
                    logger.info("🔍 Exemplos de links de lotes encontrados:")
                    for i, link in enumerate(links_com_lote[:5], 1):
                        href = link.get('href', '')
                        texto = link.get_text(strip=True)[:40]
                        logger.info(f"  {i}. {href} - '{texto}'")
            
            for link in todos_links:
                href = link.get('href', '')
                texto = link.get_text(strip=True)
                
                # Verifica se é um link de lote individual
                # Padrões: /lote/, /item/, /imovel/, ou links com IDs de lote
                if any(padrao in href.lower() for padrao in ['/lote', '/item', '/imovel']):
                    # Evita links do próprio evento/leilão (queremos lotes específicos)
                    if '/evento/' not in href or '/lote' in href:
                        link_completo = urljoin(base_url, href)
                        
                        if link_completo not in self.links_processados and link_completo != url_leilao:
                            links_lotes.append(link_completo)
                            self.links_processados.add(link_completo)
                            logger.info(f"  📦 Lote encontrado: {texto[:30]} -> {href}")
            
            # Se não encontrou lotes com padrões específicos, tenta busca por AJAX
            if not links_lotes:
                logger.info("⚠️  Nenhum lote encontrado com padrões de URL, tentando buscar via AJAX...")
                
                # Procura por elementos com data-ajax que podem carregar lotes
                ajax_elements = soup.find_all(attrs={'data-ajax-url': True})
                
                for elem in ajax_elements:
                    ajax_url = elem.get('data-ajax-url')
                    if any(termo in ajax_url.lower() for termo in ['lote', 'item', 'imovel', 'pesquisar']):
                        logger.info(f"🔄 Tentando URL AJAX: {ajax_url}")
                        
                        try:
                            ajax_full_url = urljoin(base_url, ajax_url)
                            ajax_response = self.session.get(ajax_full_url)
                            ajax_response.raise_for_status()
                            ajax_soup = BeautifulSoup(ajax_response.content, 'html.parser')
                            
                            # Procura lotes no conteúdo AJAX
                            ajax_links = ajax_soup.find_all('a', href=True)
                            for link in ajax_links:
                                href = link.get('href', '')
                                if any(padrao in href.lower() for padrao in ['/lote', '/item', '/imovel']):
                                    link_completo = urljoin(base_url, href)
                                    
                                    if link_completo not in self.links_processados:
                                        links_lotes.append(link_completo)
                                        self.links_processados.add(link_completo)
                                        logger.info(f"  📦 Lote (AJAX) encontrado: {href}")
                        
                        except Exception as e:
                            logger.warning(f"⚠️  Erro ao processar AJAX {ajax_url}: {e}")
            
            # Se ainda não encontrou, tenta busca ampla por cards/elementos
            if not links_lotes:
                logger.info("⚠️  Ainda sem lotes, tentando busca ampla por elementos...")
                
                # Procura por elementos que parecem ser cards de lotes
                cards_possiveis = soup.find_all(['div', 'article', 'section'], class_=lambda x: x and any(
                    termo in str(x).lower() for termo in ['card', 'item', 'lote', 'imovel', 'property']
                ))
                
                logger.info(f"🔍 Encontrados {len(cards_possiveis)} elementos que podem ser cards")
                
                for card in cards_possiveis:
                    links_no_card = card.find_all('a', href=True)
                    
                    for link in links_no_card:
                        href = link.get('href', '')
                        texto = link.get_text(strip=True).lower()
                        contexto = card.get_text().lower()
                        
                        # Indicadores de lotes: valores, metragem, endereços
                        indicadores_lote = ['r$', 'lote', 'lance', 'm²', 'm2', 'casa', 'apartamento', 
                                           'terreno', 'sala', 'loja', 'galpão', 'local:', 'avaliação']
                        
                        if any(ind in (texto + contexto) for ind in indicadores_lote):
                            # Evita links de navegação
                            if not any(nav in href.lower() for nav in ['agenda', 'login', 'cadastro', 'blog', '#']):
                                link_completo = urljoin(base_url, href)
                                
                                if link_completo not in self.links_processados and link_completo != url_leilao and link_completo != url_leilao.replace('/detalhes/', '/detalhe/'):
                                    links_lotes.append(link_completo)
                                    self.links_processados.add(link_completo)
                                    logger.info(f"  📦 Lote (card) encontrado: {texto[:30]} -> {href}")
            
            logger.info(f"📦 Total de lotes encontrados: {len(links_lotes)}")
            return links_lotes
            
        except Exception as e:
            logger.error(f"Erro ao extrair lotes de {url_leilao}: {e}")
            return []
    
    def verificar_palavra_chave(self, soup):
        """Verifica se a página contém a palavra-chave"""
        texto_pagina = soup.get_text().lower()
        return palavra_chave.lower() in texto_pagina
    
    def baixar_pdf_matricula(self, url_lote, nome_banco):
        """Etapa 3: Baixa o PDF da matrícula de um lote específico"""
        try:
            response = self.session.get(url_lote)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            logger.info(f"🔍 Processando lote: {url_lote}")
            
            lote_id = urlparse(url_lote).path.split('/')[-1] or 'lote'
            
            # Verifica se contém a palavra-chave
            if not self.verificar_palavra_chave(soup):
                logger.info(f"⚠️  Palavra-chave '{palavra_chave}' não encontrada em {url_lote}")
                return False
            
            logger.info(f"✅ Palavra-chave '{palavra_chave}' encontrada!")
            
            # Procura link da matrícula com múltiplas estratégias
            link_matricula = None
            
            # Lista todos os links do lote para debug
            todos_links = soup.find_all('a', href=True)
            logger.info(f"🔗 Total de links no lote: {len(todos_links)}")
            
            # Mostra links que podem ser PDFs
            logger.info("📋 Links que podem ser documentos:")
            for link in todos_links[:15]:  # Mostra os primeiros 15
                href = link.get('href', '')
                texto = link.get_text(strip=True)
                if any(termo in href.lower() or termo in texto.lower() for termo in ['pdf', 'doc', 'matricula', 'download']):
                    logger.info(f"  - {texto[:40]} -> {href}")
            
            # Estratégia 1: Texto contém "Matrícula"
            link_matricula = soup.find('a', string=lambda text: text and 'matrícula' in text.lower())
            if link_matricula:
                logger.info(f"🎯 Estratégia 1: Encontrado por texto 'Matrícula'")
            
            # Estratégia 2: Diferentes variações
            if not link_matricula:
                termos_matricula = ['matricula', 'Matricula', 'MATRICULA', 'matrícula', 'Matrícula', 'MATRÍCULA']
                for termo in termos_matricula:
                    link_matricula = soup.find('a', string=lambda text: text and termo in str(text))
                    if link_matricula:
                        logger.info(f"🎯 Estratégia 2: Encontrado por termo '{termo}'")
                        break
            
            # Estratégia 3: Por href que contenha "matricula" ou extensões de documento
            if not link_matricula:
                for link in todos_links:
                    href = link.get('href', '').lower()
                    texto = link.get_text(strip=True).lower()
                    
                    if any(termo in href or termo in texto for termo in ['matricula', 'matrícula']):
                        link_matricula = link
                        logger.info(f"🎯 Estratégia 3: Encontrado por href/texto com 'matricula'")
                        break
            
            # Estratégia 4: Procura por qualquer PDF
            if not link_matricula:
                logger.info("⚠️  Matrícula não encontrada, procurando qualquer PDF...")
                for link in todos_links:
                    href = link.get('href', '').lower()
                    if '.pdf' in href or 'pdf' in href:
                        link_matricula = link
                        logger.info(f"🎯 Estratégia 4: Encontrado PDF genérico")
                        break
            
            if link_matricula and link_matricula.get('href'):
                pdf_url = urljoin(url_lote, link_matricula['href'])
                texto_link = link_matricula.get_text(strip=True)
                
                logger.info(f"📄 Link encontrado: '{texto_link}' -> {pdf_url}")
                
                # Baixa o PDF
                logger.info(f"⬇️  Baixando PDF...")
                pdf_response = self.session.get(pdf_url)
                pdf_response.raise_for_status()
                
                # Verifica se é realmente um PDF
                content_type = pdf_response.headers.get('Content-Type', '')
                if 'pdf' not in content_type.lower() and len(pdf_response.content) < 1000:
                    logger.warning(f"⚠️  Conteúdo pode não ser um PDF válido. Content-Type: {content_type}")
                
                # Cria nome do arquivo e diretório específico
                nome_arquivo = f"{nome_banco}_{lote_id}.pdf"
                diretorio_pdfs = os.path.join('pdfs', 'leilao_vip')
                caminho_arquivo = os.path.join(diretorio_pdfs, nome_arquivo)
                
                # Verifica se o PDF já existe
                if os.path.exists(caminho_arquivo):
                    logger.info(f"⏭️  PDF já existe, pulando: {caminho_arquivo}")
                    return False
                
                # Cria diretório se não existir
                os.makedirs(diretorio_pdfs, exist_ok=True)
                
                # Salva o PDF
                with open(caminho_arquivo, 'wb') as f:
                    f.write(pdf_response.content)
                
                tamanho_kb = len(pdf_response.content) / 1024
                self.pdfs_baixados.append(caminho_arquivo)
                logger.info(f"✅ PDF baixado: {caminho_arquivo} ({tamanho_kb:.2f} KB)")
                return True
            else:
                logger.warning(f"❌ Nenhum link de matrícula/PDF encontrado em {url_lote}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {url_lote}: {e}")
            return False
            return False
    
    def processar_banco(self, nome_banco, url_banco):
        """Processa um banco seguindo o fluxo completo: Leilões → Lotes → PDFs"""
        logger.info(f"🏦 Processando {nome_banco}...")
        
        # Etapa 1: Extrai cards de leilões
        links_leiloes = self.extrair_cards_leiloes(url_banco)
        logger.info(f"🏠 Encontrados {len(links_leiloes)} leilões em {nome_banco}")
        
        if not links_leiloes:
            logger.warning(f"⚠️  Nenhum leilão encontrado para {nome_banco}")
            return
        
        total_pdfs_banco = 0
        
        # Etapa 2: Para cada leilão, extrai os lotes
        for i, link_leilao in enumerate(links_leiloes, 1):
            logger.info(f"🔄 Processando leilão {i}/{len(links_leiloes)}")
            
            self.aguardar_entre_requests()
            
            # Extrai lotes do leilão
            links_lotes = self.extrair_lotes_do_leilao(link_leilao)
            
            # Etapa 3: Para cada lote, tenta baixar o PDF da matrícula
            for j, link_lote in enumerate(links_lotes, 1):
                logger.info(f"  📦 Processando lote {j}/{len(links_lotes)}")
                
                self.aguardar_entre_requests(1)  # Pausa menor entre lotes
                
                if self.baixar_pdf_matricula(link_lote, nome_banco):
                    total_pdfs_banco += 1
        
        logger.info(f"✅ {nome_banco} concluído: {total_pdfs_banco} PDFs baixados")
    
    def executar_scraping(self):
        """Executa o scraping completo de todos os bancos"""
        logger.info("🚀 Iniciando scraping do LeilaoVip...")
        
        for nome_banco, url_banco in bancos.items():
            self.processar_banco(nome_banco, url_banco)
            self.aguardar_entre_requests(3)  # Pausa maior entre bancos
        
        logger.info(f"🎉 Scraping concluído! {len(self.pdfs_baixados)} PDFs baixados no total.")
        return self.pdfs_baixados

def iniciar_scraping_vip():
    """Função principal para iniciar o scraping do LeilaoVip"""
    scraper = LeilaoVipScraper()
    pdfs = scraper.executar_scraping()
    
    print(f"\n📄 PDFs baixados ({len(pdfs)}):")
    for pdf in pdfs:
        print(f"  • {pdf}")
    
    return pdfs

def testar_um_banco(nome_banco="bradesco"):
    """Função para testar apenas um banco com debug"""
    logger.info(f"🧪 TESTE: Analisando apenas o banco {nome_banco}")
    
    scraper = LeilaoVipScraper()
    url_banco = bancos.get(nome_banco)
    
    if not url_banco:
        logger.error(f"Banco '{nome_banco}' não encontrado!")
        return []
    
    # Testa apenas a extração de cards de leilões
    links = scraper.extrair_cards_leiloes(url_banco)
    
    logger.info(f"🎯 Total de cards de leilões encontrados: {len(links)}")
    
    if links:
        logger.info("📋 Cards encontrados:")
        for i, link in enumerate(links[:3], 1):
            logger.info(f"  {i}. {link}")
    
    return links
