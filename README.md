# 🔭 Observability Lab: FastAPI + OpenTelemetry Stack

Proyecto de aprendizaje progresivo de observabilidad construido sobre una API
de pagos en FastAPI y desplegado en local con Docker.

---

## Índice

1. [Objetivo](#1-objetivo)
2. [Arquitectura final](#2-arquitectura-final)
3. [Requisitos del sistema](#3-requisitos-del-sistema)
4. [Estructura del proyecto](#4-estructura-del-proyecto)
5. [Itinerario de fases](#5-itinerario-de-fases)
   - [Fase 1: La API](#-fase-1-la-api)
   - [Fase 2: Métricas con Prometheus y Grafana](#-fase-2-métricas-con-prometheus-y-grafana)
   - [Fase 3: Logs estructurados con Loki](#-fase-3-logs-estructurados-con-loki)
   - [Fase 4: Trazas distribuidas con Tempo y OpenTelemetry](#-fase-4-trazas-distribuidas-con-tempo-y-opentelemetry)
   - [Fase 5: OTEL Collector, el router central](#-fase-5-otel-collector-el-router-central)
   - [Fase 6: Retención larga con Thanos y MinIO](#-fase-6-retención-larga-con-thanos-y-minio)
6. [Correlación entre las tres señales](#6-correlacion-entre-las-tres-senales)
7. [Métricas expuestas por la API](#7-metricas-expuestas-por-la-api)
8. [Campos de log](#8-campos-de-log)
9. [Notas importantes](#9-notas-importantes)
10. [Dependabot](#10-dependabot)
11. [Referencias](#11-referencias)

---

<a name="1-objetivo"></a>
## 🎯 1. Objetivo

Aprender las tecnologías del stack de observabilidad de producción de forma incremental,
fase a fase, con una aplicación real como hilo conductor.

El punto de partida es una API de pagos construida en FastAPI. Sobre ella iremos
añadiendo, capa a capa, todas las herramientas de observabilidad: métricas, logs,
trazas, retención histórica y visualización.

---

<a name="2-arquitectura-final"></a>
## 🏗️ 2. Arquitectura final

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Payment API                       │
│              GET /health · GET /payments · POST /payments        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  OTEL Collector  │  recepción · normalización
                    │                 │  enriquecimiento · routing
                    └──┬──────┬───┬───┘
                       │      │   │
           ┌───────────▼┐  ┌──▼──┐ ┌▼─────┐
           │ Prometheus  │  │Loki │ │Tempo │
           │  métricas   │  │logs │ │trazas│
           └──────┬──────┘  └──┬──┘ └──┬───┘
                  │            │        │
           ┌──────▼────────────▼────────▼──────┐
           │             MinIO (S3)              │
           │  object storage S3-compatible       │
           │  bloques Thanos · chunks Loki       │
           │  datos Tempo (retención larga)      │
           └──────────────────────┬─────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │         Thanos              │
                    │  Sidecar · Query · Store GW │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │           Grafana            │
                    │  métricas · logs · trazas    │
                    └─────────────────────────────┘
```

---

<a name="3-requisitos-del-sistema"></a>
## 🖥️ 3. Requisitos del sistema

| Recurso | Mínimo | Recomendado |
|---|---|---|
| SO | Ubuntu 22.04+ | Ubuntu 24.04 |
| RAM | 8 GB (Fases 1-4) | 16 GB (stack completo Fase 6) |
| CPU | 4 cores | 6+ cores |
| Disco | 10 GB libres | 20 GB libres |
| Docker Engine | 24+ | última estable |
| Docker Compose | v2 (`docker compose`) | última estable |
| Python | 3.12+ | 3.13 |

```bash
# Verificar antes de empezar
docker --version
docker compose version
python3 --version
```

---

<a name="4-estructura-del-proyecto"></a>
## 📁 4. Estructura del proyecto

```
fastapi-observability/
│
├── app/
│   ├── app.py                    # FastAPI app (endpoints, modelos, métricas)
│   ├── Dockerfile
│   ├── gunicorn.conf.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_api.py
│
├── prometheus/
│   └── prometheus.yml            # Config scraping (Fase 2)
│
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/          # Datasources auto-provisionados (Fase 2)
│   │   └── dashboards/           # Config carga de dashboards (Fase 2)
│   └── dashboards/
│       └── payments.json         # Dashboard de pagos (Fase 2)
│
├── otel-collector/
│   └── otel-collector-config.yml # Pipeline unificado (Fase 5)
│
├── loki/
│   └── loki-config.yml           # Config Loki (Fase 3)
│
├── tempo/
│   └── tempo-config.yml          # Config Tempo (Fase 4)
│
├── thanos/
│   └── bucket-config.yml         # Config MinIO/S3 (Fase 6)
│
├── scripts/
│   └── load_test.sh              # Genera tráfico simulado
│
├── docker-compose.yml            # Crece fase a fase
├── .github/
│   ├── dependabot.yml
│   └── workflows/ci.yml
├── .gitignore
├── LICENSE
└── README.md
```

---

<a name="5-itinerario-de-fases"></a>
## 🗺️ 5. Itinerario de fases

---

### 🟢 Fase 1: La API

**Objetivo:** construir la API de pagos en FastAPI y dejarla funcionando
en local con Docker y PostgreSQL. Esta fase no toca nada de observabilidad,
es la base sobre la que construiremos todo lo demás.

**Qué se hace:**
- Crear `app.py` con FastAPI y Uvicorn
- Modelos Pydantic para request y response con validación automática
- Documentación OpenAPI gratuita en `/docs`
- PostgreSQL como base de datos con SQLAlchemy
- Tests con pytest y test gate en el pipeline de CI
- Arrancar con `docker compose up`

**Al terminar esta fase tendrás:**
```
FastAPI (/health · /payments)
    ↕
PostgreSQL
```

**URLs:**
| Servicio | URL |
|---|---|
| API docs (Swagger) | http://localhost:8000/docs |
| API docs (ReDoc) | http://localhost:8000/redoc |
| API health | http://localhost:8000/health |
| API pagos | http://localhost:8000/payments |

**Entorno virtual local (solo para el IDE):**

Los paquetes se instalan dentro de Docker, por lo que VS Code y Pylance no los
encuentran por defecto y muestra warnings de imports no resueltos. La solución
es crear un entorno virtual local únicamente para que el IDE tenga contexto:

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Después en VS Code: `Ctrl+Shift+P` -> `Python: Select Interpreter` -> seleccionar
el intérprete que apunta a `app/.venv/bin/python`.

El directorio `.venv` ya está en `.gitignore` y no se sube al repositorio.

**Servidor de producción: Gunicorn + Uvicorn workers**

FastAPI necesita un servidor ASGI para funcionar. Hay varias opciones y la elección
importa en producción.

Alternativas consideradas:

| Opción | Descripción | Apto para producción |
|---|---|---|
| `uvicorn` (1 worker) | Simple, arranque rápido | No (sin redundancia) |
| `uvicorn --workers N` | Múltiples procesos, sin process manager | Parcialmente |
| `gunicorn + UvicornWorker` | Gunicorn gestiona workers Uvicorn | Si (opción elegida) |

La opción elegida es **Gunicorn con workers de tipo UvicornWorker**. Gunicorn actúa
como process manager: si un worker muere lo reinicia automáticamente, gestiona señales
del sistema operativo (SIGTERM, SIGHUP) y permite graceful shutdown, algo crítico en
Kubernetes cuando un pod se destruye con peticiones en curso.

La configuración vive en `gunicorn.conf.py` y cubre:

- **workers**: calculado como `(CPU * 2) + 1`, sobreescribible con `WEB_CONCURRENCY`
- **worker_class**: `uvicorn.workers.UvicornWorker` para soporte async completo
- **max_requests / jitter**: reinicio periódico de workers para evitar memory leaks
- **graceful_timeout**: tiempo para terminar peticiones en curso antes de matar el proceso
- **timeout**: mata workers bloqueados sin respuesta
- **accesslog / errorlog**: redirigidos a stdout/stderr para que Docker los recoja

En local se fija `WEB_CONCURRENCY=2` en el `docker-compose.yml`. En producción
se sube ese valor via variable de entorno sin tocar el código ni la imagen.

Para profundizar:

| Recurso | Enlace |
|---|---|
| Uvicorn deployment | https://www.uvicorn.org/deployment/ |
| Gunicorn settings | https://docs.gunicorn.org/en/stable/settings.html |
| FastAPI server workers | https://fastapi.tiangolo.com/deployment/server-workers/ |

YouTube:
- **ArjanCodes** (FastAPI producción) -> https://www.youtube.com/@ArjanCodes/search?query=fastapi+production
- **ArjanCodes** (SQLAlchemy) -> https://www.youtube.com/@ArjanCodes/search?query=sqlalchemy
- **Corey Schafer** (SQLAlchemy, fundamentos) -> https://www.youtube.com/@coreyms/search?query=sqlalchemy
- **TechWorld with Nana** (FastAPI + Docker) -> https://www.youtube.com/@TechWorldwithNana/search?query=fastapi+docker
- **That DevOps Guy** (Python en producción) -> https://www.youtube.com/@MarcelDempers/search?query=python

**Para profundizar antes de continuar:**

| Recurso | Enlace | Para qué sirve |
|---|---|---|
| FastAPI Tutorial oficial | https://fastapi.tiangolo.com/tutorial/ | Conceptos base: path params, query params, body, response models |
| Pydantic docs | https://docs.pydantic.dev | Validación y modelos de datos |
| Testing en FastAPI | https://fastapi.tiangolo.com/tutorial/testing/ | Tests con `pytest` y `httpx` |
| SQLAlchemy 2.0 | https://docs.sqlalchemy.org/en/20/ | ORM y capa de base de datos |
| GitHub Actions docs | https://docs.github.com/en/actions | Workflows, jobs, steps, servicios |

YouTube recomendado:
- Canal **ArjanCodes** -> https://www.youtube.com/@ArjanCodes/search?query=fastAPI (buenas prácticas)
- Canal **TechWorld with Nana** -> https://www.youtube.com/@TechWorldwithNana/search?query=GitHub%20Actions (CI/CD desde cero)

**Tests con pytest:**

Los tests viven en `app/tests/` y usan `TestClient` de FastAPI junto con una
base de datos PostgreSQL de test independiente de la de desarrollo.

Las dependencias de test están separadas en `requirements-dev.txt` para que
no entren en la imagen Docker de producción:

```
pytest==9.0.3
httpx==0.28.1
```

Ejecutar tests en local:

```bash
cd app
DATABASE_URL=postgresql://payments:payments@localhost:5432/paymentsdb_test \
  pytest tests/ -v
```

Casos cubiertos:

| Test | Qué verifica |
|---|---|
| `test_health` | Respuesta correcta del healthcheck |
| `test_get_payments` | Estructura del listado: `payments` y `total` |
| `test_create_payment_valid` | Flujo completo: 201, campos presentes y valores correctos |
| `test_create_payment_negative_amount` | Importe negativo -> 422 |
| `test_create_payment_zero_amount` | Importe cero -> 422 (límite estricto `gt=0`) |
| `test_create_payment_invalid_currency` | Moneda fuera de patrón `^[A-Z]{3}$` -> 422 |
| `test_create_payment_missing_amount` | Campo obligatorio ausente -> 422 |
| `test_get_payments_after_creation` | El total del listado incrementa tras crear un pago |

**Pipeline CI con test gate:**

El workflow de GitHub Actions en `.github/workflows/ci.yml` tiene dos jobs:

```
test -> build-and-push
```

El job `test` levanta PostgreSQL como servicio, instala dependencias y ejecuta
pytest. El job `build-and-push` tiene `needs: test`, de forma que si los tests
fallan la imagen nunca se construye ni se publica en GHCR.

```yaml
jobs:
  test:
    services:
      postgres:           # PostgreSQL efímero solo para los tests
        image: postgres:17-alpine
    steps:
      - run: pytest tests/ -v

  build-and-push:
    needs: test           # bloquea el build si test falla
    steps:
      - build y push a GHCR
```

**Pruebas de validación:**

```bash
# Health check
curl http://localhost:8000/health

# Crear pago válido
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 99.99, "currency": "EUR"}'

# Listar pagos
curl http://localhost:8000/payments

# Importe negativo -> 422 Unprocessable Content
curl -i -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": -50, "currency": "EUR"}'

# Moneda inválida -> 422 Unprocessable Content
curl -i -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "eurosss"}'

# Sin importe -> 422 Unprocessable Content
curl -i -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"currency": "EUR"}'
```

---

### 🔵 Fase 2: Métricas con Prometheus y Grafana

**Concepto:** las métricas son la señal más básica de observabilidad.
Responden a preguntas como: cuántas peticiones por segundo recibo,
cuánto tardan, cuántos pagos se crean por minuto, hay errores.

Prometheus recoge estas métricas cada 15 segundos haciendo scraping
al endpoint `/metrics` que expone la app. Grafana las visualiza.

**Vídeo previo recomendado:**
YouTube -> canal **TechWorld with Nana** -> https://www.youtube.com/@TechWorldwithNana/search?query=Prometheus+Grafana

**Qué se hace:**
- Añadir `prometheus-fastapi-instrumentator` a la app, que expone `/metrics` automáticamente
- Añadir métricas de negocio custom: `payments_created_total`, `payments_amount_euros`
- Levantar Prometheus con su config de scraping
- Levantar Grafana con datasource y dashboard pre-provisionados
- Aprender PromQL básico: `rate()`, `histogram_quantile()`

**Al terminar esta fase tendrás:**
```
FastAPI (/metrics) <-- scraping cada 15s -- Prometheus
                                                  ↕
                                              Grafana
```

**URLs añadidas:**
| Servicio | URL |
|---|---|
| Métricas raw | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |

---

### 🟡 Fase 3: Logs estructurados con Loki

**Concepto:** los logs son la señal más detallada. Un log bien estructurado
te dice exactamente qué pasó, cuándo, en qué contexto y con qué datos.
El problema habitual es que los logs son texto plano y son imposibles de
buscar a escala. La solución es emitirlos en JSON (logs estructurados)
e indexarlos con Loki para poder buscar con LogQL.

**Vídeo previo recomendado:**
YouTube -> `Grafana Loki Docker Compose tutorial` -> canal **Grafana** oficial

**Qué se hace:**
- Añadir `structlog` a la app para logging estructurado en JSON
- Cada log incluye: `payment_id`, `endpoint`, `status_code`, `duration_ms`
- Levantar Loki como backend de logs
- Levantar Promtail para recoger logs de contenedores Docker
- Explorar LogQL en Grafana: filtrar por endpoint, ver errores agrupados

**Al terminar esta fase tendrás:**
```
FastAPI (JSON logs)
      ↓
  Promtail (recoge logs Docker)
      ↓
    Loki
      ↕
   Grafana
```

**URLs añadidas:**
| Servicio | URL |
|---|---|
| Loki (health) | http://localhost:3100/ready |
| Grafana (Loki) | http://localhost:3000 -> Explore -> Loki |

---

### 🟣 Fase 4: Trazas distribuidas con Tempo y OpenTelemetry

**Concepto:** una traza muestra el recorrido completo de una petición
desde que entra hasta que sale. En un sistema con microservicios es
la única forma de saber en qué paso exacto se perdió tiempo o falló algo.
Cada traza está formada por spans, uno por operación (validar, consultar BD, responder).

OpenTelemetry es el estándar CNCF que instrumenta la app para generar esas trazas.
Tempo las almacena. Grafana las visualiza.

**Vídeo previo recomendado:**
YouTube -> `OpenTelemetry Python FastAPI tutorial` -> canal **opentelemetry** oficial

**Qué se hace:**
- Añadir SDK de OpenTelemetry a la app con auto-instrumentación de FastAPI
- Spans custom: `payment.validate`, `payment.process`, `payment.persist`
- Levantar Tempo como backend de trazas
- Ver una traza completa en Grafana y navegar entre sus spans
- Correlacionar una traza con sus logs usando `trace_id`

**Al terminar esta fase tendrás:**
```
FastAPI (spans OTEL)
      ↓
    Tempo
      ↕
   Grafana (ver traza + correlacionar con logs de Loki)
```

**URLs añadidas:**
| Servicio | URL |
|---|---|
| Tempo (health) | http://localhost:3200/ready |
| Grafana (Tempo) | http://localhost:3000 -> Explore -> Tempo |

---

### 🟠 Fase 5: OTEL Collector, el router central

**Concepto:** en producción no se envían métricas, logs y trazas
directamente a sus backends. Todo pasa por un Collector centralizado
que recibe, normaliza, enriquece y enruta cada señal.

**Qué se hace:**
- Levantar OpenTelemetry Collector
- Configurar pipelines: receivers -> processors -> exporters
- La app solo habla con el Collector, que decide adónde va cada señal
- Reemplazar Promtail por el Collector para logs
- Añadir processors: `batch`, `memory_limiter`, enriquecimiento con metadatos

**Al terminar esta fase tendrás:**
```
FastAPI -> OTEL Collector --> Prometheus
                         --> Loki
                         --> Tempo
                                ↓
                             Grafana
```

---

### 🔴 Fase 6: Retención larga con Thanos y MinIO

**Concepto:** Prometheus solo retiene datos 7-15 días. Para retención
histórica de meses o años en producción se usa Thanos con object storage S3-compatible.
MinIO actúa como ese object storage en local.

**Vídeo previo recomendado:**
YouTube -> `Thanos Prometheus long term storage tutorial` -> canal **That DevOps Guy**

**Qué se hace:**
- Levantar MinIO con buckets `thanos`, `loki`, `tempo`
- Thanos Sidecar junto a Prometheus: sube bloques TSDB a MinIO cada 2h
- Thanos Store Gateway: permite consultar datos históricos en MinIO
- Thanos Query: federa Prometheus local con datos históricos
- Loki y Tempo también persisten en MinIO
- Grafana apunta a Thanos Query en vez de Prometheus directamente

**Al terminar esta fase tendrás el stack completo:**
```
FastAPI -> OTEL Collector -> Prometheus <-> Thanos Sidecar --> MinIO
                         -> Loki -----------------------------> MinIO
                         -> Tempo ----------------------------> MinIO
                                    Thanos Store Gateway <----- MinIO
                                    Thanos Query
                                         ↓
                                      Grafana
```

**URLs añadidas:**
| Servicio | URL |
|---|---|
| MinIO Console | http://localhost:9001 (minioadmin/minioadmin) |
| Thanos Query UI | http://localhost:10902 |

---

<a name="6-correlacion-entre-las-tres-senales"></a>
## 🔗 6. Correlación entre las tres señales

El campo `trace_id` es el hilo conductor de las 3 señales en Grafana:

```
1. Alerta en Prometheus -> CPU alta en /payments
           ↓
2. Grafana -> buscar logs de ese timestamp en Loki
           ↓
3. El log contiene trace_id -> abrir esa traza en Tempo
           ↓
4. La traza muestra qué span tardó -> causa raíz identificada
```

---

<a name="7-metricas-expuestas-por-la-api"></a>
## 📊 7. Métricas expuestas por la API (Fase 2 en adelante)

| Métrica | Tipo | Descripción |
|---|---|---|
| `http_requests_total` | Counter | Requests por endpoint y status (auto) |
| `http_request_duration_seconds` | Histogram | Latencia HTTP (auto) |
| `payments_created_total` | Counter | Pagos creados por moneda (custom) |
| `payments_failed_total` | Counter | Pagos fallidos por motivo (custom) |
| `payments_amount_euros` | Histogram | Distribución de importes (custom) |

---

<a name="8-campos-de-log"></a>
## 🏷️ 8. Campos de log (Fase 3 en adelante)

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "info",
  "service": "payment-api",
  "endpoint": "/payments",
  "method": "POST",
  "status_code": 201,
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 99.99,
  "currency": "EUR",
  "duration_ms": 45,
  "trace_id": "abc123def456",
  "span_id": "789xyz"
}
```

---

<a name="9-notas-importantes"></a>
## ⚠️ 9. Notas importantes

- **Cada fase es acumulativa**: el `docker-compose.yml` crece en cada fase añadiendo servicios.
- **Todos los contenedores tienen `mem_limit`**: para no comprometer los 8 GB del equipo.
- **Thanos Compact se omite en local**: solo tiene sentido con semanas de datos históricos reales.

---

<a name="10-dependabot"></a>
## 🤖 10. Dependabot

Dependabot revisa automáticamente las dependencias del proyecto cada semana y abre
Pull Requests cuando hay versiones nuevas disponibles. Está configurado en
`.github/dependabot.yml` y cubre cuatro ecosistemas:

| Ecosistema | Qué monitoriza |
|---|---|
| `pip` | `app/requirements.txt` y `requirements-dev.txt` |
| `docker` (app) | Imagen base del `app/Dockerfile` |
| `docker` (raíz) | Imágenes del `docker-compose.yml` |
| `github-actions` | Actions del workflow de CI |

Cada semana Dependabot abre PRs automáticos con las actualizaciones disponibles.
El test gate del CI se ejecuta sobre cada PR, de forma que solo se mergea
lo que pasa los tests.

---

<a name="11-referencias"></a>
## 📚 11. Referencias

| Herramienta | Documentación |
|---|---|
| FastAPI | https://fastapi.tiangolo.com |
| OpenTelemetry Python | https://opentelemetry.io/docs/instrumentation/python |
| Prometheus | https://prometheus.io/docs |
| Grafana Loki | https://grafana.com/docs/loki |
| Grafana Tempo | https://grafana.com/docs/tempo |
| Thanos | https://thanos.io/tip/thanos |
| MinIO | https://min.io/docs |
