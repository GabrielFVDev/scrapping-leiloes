from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from scrapping.vip import iniciar_scraping_vip
import uvicorn
from datetime import datetime
import os

app = FastAPI(
    title="Sistema de Scraping de Leilões",
    description="API para realizar scraping de leilões extrajudiciais",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "🏠 Sistema de Scraping de Leilões",
        "version": "1.0.0",
        "endpoints": {
            "scraping_vip": "/scraping/vip",
            "status": "/status",
            "pdfs": "/pdfs"
        }
    }

@app.post("/scraping/vip")
async def executar_scraping_vip():
    """Executa o scraping do LeilaoVip"""
    try:
        print("🚀 Iniciando scraping do LeilaoVip via API...")
        
        pdfs_baixados = iniciar_scraping_vip()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "sucesso",
                "message": "Scraping concluído com sucesso!",
                "timestamp": datetime.now().isoformat(),
                "total_pdfs": len(pdfs_baixados),
                "pdfs_baixados": pdfs_baixados
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "erro",
                "message": f"Erro durante o scraping: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/status")
async def verificar_status():
    """Verifica o status da aplicação"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "message": "API funcionando normalmente"
    }

@app.get("/pdfs")
async def listar_pdfs():
    """Lista todos os PDFs baixados"""
    try:
        pdfs_dir = "pdfs"
        
        if not os.path.exists(pdfs_dir):
            return {
                "status": "vazio",
                "message": "Nenhum PDF encontrado",
                "total": 0,
                "pdfs": []
            }
        
        arquivos_pdf = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
        
        pdfs_info = []
        for pdf in arquivos_pdf:
            caminho_completo = os.path.join(pdfs_dir, pdf)
            stat = os.stat(caminho_completo)
            
            pdfs_info.append({
                "nome": pdf,
                "caminho": caminho_completo,
                "tamanho_bytes": stat.st_size,
                "data_criacao": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return {
            "status": "sucesso",
            "total": len(pdfs_info),
            "pdfs": pdfs_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "erro",
                "message": f"Erro ao listar PDFs: {str(e)}"
            }
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )