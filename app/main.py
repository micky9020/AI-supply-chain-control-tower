"""Read-only, authenticated FastAPI logistics dashboard."""
from __future__ import annotations
import hmac
import os
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import APIKeyHeader
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .analytics import DataError, analyze, load_orders

BASE = Path(__file__).resolve().parent
DATA = Path(os.getenv('DATA_FILE', str(BASE.parent / 'data' / 'demo_orders.csv')))
API_KEY = os.getenv('CONTROL_TOWER_API_KEY','')
if len(API_KEY) < 24:
    raise RuntimeError('CONTROL_TOWER_API_KEY debe tener al menos 24 caracteres. Genere una clave segura y configúrela.')

app = FastAPI(title='AI Supply Chain Control Tower', docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[h.strip() for h in os.getenv('ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(',') if h.strip()])
header = APIKeyHeader(name='X-API-Key', auto_error=False)

async def authorized(value: str | None = Security(header)):
    if not value or not hmac.compare_digest(value, API_KEY):
        raise HTTPException(status_code=401, detail='Credenciales inválidas', headers={'WWW-Authenticate':'ApiKey'})

def get_data():
    try:
        return analyze(load_orders(DATA))
    except DataError as exc:
        raise HTTPException(status_code=503, detail='Datos no disponibles o inválidos') from exc

@app.middleware('http')
async def security_headers(request:Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy'] = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    return response

@app.get('/', include_in_schema=False)
def homepage():
    return FileResponse(BASE / 'static' / 'index.html')

@app.get('/static/app.js', include_in_schema=False)
def js():
    return FileResponse(BASE / 'static' / 'app.js', media_type='text/javascript')

@app.get('/static/styles.css', include_in_schema=False)
def css():
    return FileResponse(BASE / 'static' / 'styles.css', media_type='text/css')

@app.get('/health', include_in_schema=False)
def health():
    return {'status':'ok'}

@app.get('/api/dashboard', dependencies=[Depends(authorized)])
def dashboard():
    return get_data()

@app.get('/api/orders', dependencies=[Depends(authorized)])
def orders():
    return get_data()['orders']

@app.get('/api/alerts', dependencies=[Depends(authorized)])
def alerts():
    return get_data()['alerts']
