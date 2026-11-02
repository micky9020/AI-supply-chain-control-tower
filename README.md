# AI Supply Chain Control Tower

Panel de control web (FastAPI + HTML/JS) para supervisar operaciones de supply chain: pedidos, inventario, cumplimiento de entregas, señales de demora y alertas priorizadas por un **motor de reglas explicables**. Incluye 12 pedidos **ficticios** para funcionar desde el primer arranque; no requiere cuentas en servicios externos ni LinkedIn.

> **Alcance real de IA:** la versión inicial usa scoring heurístico transparente, no un LLM ni un modelo predictivo entrenado. No se deben interpretar las puntuaciones como probabilidades validadas. Conectar un modelo externo o un ERP es una extensión futura, no una capacidad implementada.

## Requisitos
- Python 3.12 o Docker + Docker Compose.
- Sistema compatible con Windows, macOS o Linux.

## Opción A: ejecución local (Python)

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_key.py
```

Copia el valor generado de forma privada. Configura la variable de entorno (no sustituyas por una clave fácil):

**Linux/macOS**
```bash
export CONTROL_TOWER_API_KEY='PEGA_TU_CLAVE_GENERADA'
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Windows PowerShell**
```powershell
$env:CONTROL_TOWER_API_KEY = 'PEGA_TU_CLAVE_GENERADA'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abre **http://127.0.0.1:8000**. Pega la clave en el campo de acceso y pulsa **Cargar dashboard**.

## Opción B: Docker (recomendado para probar de forma aislada)

```bash
cp .env.example .env
python scripts/generate_key.py
```

Edita `.env` y sustituye `REPLACE_WITH_A_RANDOM_SECRET_AT_LEAST_24_CHARS` por el valor generado. **No hagas commit de `.env`.**

```bash
docker compose up --build -d
```

Abre **http://127.0.0.1:8000** e introduce la misma clave. Para detenerlo: `docker compose down`.

## Publicación en GitHub

1. Crea un repositorio **privado** en GitHub con nombre `ai-supply-chain-control-tower`.
2. Descomprime el ZIP, sube su contenido (no el ZIP como único archivo) y conserva `.github/workflows/ci.yml`.
3. No subas `.env`, contraseñas, claves, tokens ni datos reales sensibles. `.gitignore` y `.dockerignore` ayudan a excluirlos, pero revisa siempre los commits.
4. En **Actions**, el flujo de CI ejecutará pruebas y auditoría de dependencias. **GitHub Actions no despliega ni expone automáticamente el dashboard.**

## Datos y métricas

`data/demo_orders.csv` contiene registros de ejemplo y las columnas documentadas por sus encabezados. Para usar datos propios configura `DATA_FILE` apuntando a CSV con el mismo formato, validado por el motor. No compartas CSV sensibles en repositorios públicos.

Se calculan: órdenes activas, demoras, monto de inventario, puntualidad promedio, cobertura de stock (`inventory_units / daily_demand`) y riesgo por orden de 0 a 100. Señales: estado de retraso, tránsito mayor al lead time, fecha vencida, cobertura de stock menor a 7/14 días e historial bajo de entregas puntuales. Los datos ficticios son estáticos y no representan un feed en vivo.

Endpoints protegidos (cabecera `X-API-Key`): `/api/dashboard`, `/api/orders`, `/api/alerts`. Público: `/` (frontend sin datos hasta autenticar), `/health` (solo estado de vida).

Ejemplo de prueba con curl:

```bash
curl -H 'X-API-Key: TU_CLAVE' http://127.0.0.1:8000/api/dashboard
```

## Seguridad implementada

- Se exige `CONTROL_TOWER_API_KEY` >= 24 caracteres al iniciar; autenticación constante en tiempo con `hmac.compare_digest`, fallando cerrado.
- Solo lectura: no existen endpoints para borrar/editar datos ni publicar en sistemas externos.
- Cabeceras CSP restrictivas, bloqueo de iframe, `nosniff`, no-referrer y no-store.
- Interfaz evita HTML dinámico no confiable; crea nodos con `textContent` para evitar XSS por datos del CSV.
- No guarda la clave en `localStorage`, cookies ni almacenamiento persistente; el campo se vacía al enviar.
- Docker: usuario sin privilegios, FS solo lectura, capabilities removidas, sin escalación, límites de memoria/procesos, puerto ligado a 127.0.0.1.
- Validación de tamaño de CSV, número de filas, esquema, rangos numéricos, estados y IDs únicos.
- GitHub Actions con permisos mínimos y auditoría de dependencias.

### Limitaciones y producción

- **No expongas este servidor directamente a Internet.** Para producción utiliza un reverse proxy con HTTPS, autenticación basada en identidades (OIDC/SSO), control de acceso por roles, rate limiting, auditoría, rotación de secretos y observabilidad.
- Una única clave compartida no equivale a IAM/RBAC y el rate limiting no está implementado.
- El contenedor de ejemplo está ligado a localhost (solo acceso local) de manera intencional.
- Los límites de Docker pueden variar según el host. No hay certificado TLS en el proyecto local.
- El `/health` es público y deliberadamente no expone secretos ni datos de negocio.
- Dependencias acotadas por rangos, pero no reproducibles byte a byte; en producción usa lockfile, hashes, escaneo de imágenes y versiones de acciones fijadas por SHA.
- Las integraciones ERP/WMS/TMS, ingesta de eventos y ML entrenado no están implementadas.

## Pruebas

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip_audit -r requirements.txt
```

## Estructura

```text
app/                API, motor analítico y frontend
  main.py
  analytics.py
  static/
data/demo_orders.csv
scripts/generate_key.py
tests/
.github/workflows/ci.yml
Dockerfile
compose.yaml
.env.example
requirements.txt
requirements-dev.txt
```

## Uso responsable

Los resultados son orientativos. Verifica datos, supuestos y recomendaciones con el equipo de operaciones antes de decidir compras, rutas o asignación de proveedores.
