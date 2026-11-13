"""Entrypoint único para FastAPI no Databricks Apps."""
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from repository import Repository

ROOT = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    app.state.repository = Repository(os.getenv('DATA_DIR', str(ROOT / 'data')))
    logger.info('Snapshots carregados: %s', app.state.repository.counts)
    yield

app = FastAPI(title='Terra Signal · Central de relacionamento', version='0.4.0', lifespan=lifespan)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')

@app.middleware('http')
async def headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'"
    if request.url.path.startswith('/api/') or request.url.path == '/':
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.get('/', include_in_schema=False)
def index():
    return FileResponse(ROOT / 'static' / 'central.html')

@app.get('/health')
def health(request: Request):
    return {'status': 'ok', 'mode': 'snapshot', 'counts': request.app.state.repository.counts}

@app.get('/api/summary')
def summary(request: Request, base: Literal['history', 'inference'] = 'inference',
            portfolio: Literal['all', 'retention', 'recovery'] = 'all'):
    if base == 'inference' and portfolio != 'all':
        raise HTTPException(422, 'Carteiras disponíveis somente no atendimento ativo.')
    return request.app.state.repository.summary(base, portfolio)

@app.get('/api/customers')
def customers(request: Request, base: Literal['history', 'inference'] = 'inference',
              q: str = Query('', max_length=100),
              sentiment: Literal['', 'POSITIVO', 'NEGATIVO', 'MISTO', 'NEUTRO', 'INDETERMINADO'] = '',
              risk_only: bool = False, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
              portfolio: Literal['all', 'retention', 'recovery'] = 'all',
              decile: Literal['', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10'] = '',
              predicted_churn: Literal['', '0', '1'] = '',
              min_probability: float | None = Query(None, ge=0, le=1),
              max_probability: float | None = Query(None, ge=0, le=1)):
    if base == 'inference' and portfolio != 'all':
        raise HTTPException(422, 'Carteiras disponíveis somente no atendimento ativo.')
    if min_probability is not None and max_probability is not None and min_probability > max_probability:
        raise HTTPException(422, 'A probabilidade mínima não pode superar a máxima.')
    return request.app.state.repository.list(base, q.strip(), sentiment, risk_only, offset, limit,
                                             portfolio, decile, predicted_churn, min_probability, max_probability)

@app.get('/api/customers/{customer_id}')
def detail(request: Request, customer_id: str, base: Literal['history', 'inference'] = 'inference'):
    customer = request.app.state.repository.get(base, customer_id)
    if customer is None:
        raise HTTPException(404, 'Cliente não encontrado nesta base.')
    return customer

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('DATABRICKS_APP_PORT', '8012')))
