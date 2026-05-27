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
│                        FastAPI Payment API                      │
│              GET /health · GET /payments · POST /payments       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  OTEL Collector │  recepción · normalización
                    │                 │  enriquecimiento · routing
                    └──┬──────┬──────┬┘
                       │      │      │
           ┌───────────▼─┐  ┌─▼───┐ ┌▼─────┐
           │ Prometheus  │  │Loki │ │Tempo │
           │  métricas   │  │logs │ │trazas│
           └──────┬──────┘  └──┬──┘ └──┬───┘
                  │            │        │
           ┌──────▼────────────▼────────▼──────┐
           │             MinIO (S3)            │
           │  object storage S3-compatible     │
           │  bloques Thanos · chunks Loki     │
           │  datos Tempo (retención larga)    │
           └──────────────────────┬────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │         Thanos             │
                    │  Sidecar · Query · StoreGW │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │           Grafana          │
                    │  métricas · logs · trazas  │
                    └────────────────────────────┘
```

---

<a name="3-requisitos-del-sistema"></a>
## 🖥️ 3. Requisitos del sistema

| Recurso | Mínimo | Probado con |
|---|---|---|
| SO | Ubuntu 22.04+ | Ubuntu 24.04 |
| RAM | 8 GB (Fases 1-4) | 16 GB (stack completo Fase 6) |
| CPU | 4 cores | 4 cores (i7) |
| Disco | 10 GB libres | 20 GB libres |
| Docker Engine | 24+ | última estable |
| Docker Compose | v2 (`docker compose`) | última estable |
| Python | 3.12+ | 3.14 |

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
│   │   ├── datasources/
│   │   │   ├── prometheus.yml    # Datasource Prometheus (Fase 2)
│   │   │   ├── loki.yml          # Datasource Loki (Fase 3)
│   │   │   └── tempo.yml         # Datasource Tempo + correlación (Fase 4)
│   │   └── dashboards/
│   │       └── dashboard.yml     # Config carga de dashboards (Fase 2)
│   └── dashboards/
│       ├── payment-api/
│       │   └── payments.json     # Dashboard de pagos (Fase 2)
│       └── infrastructure/
│           ├── node-exporter.json  # Dashboard Node Exporter (Fase 2)
│           ├── postgresql.json     # Dashboard PostgreSQL (Fase 2)
│           └── cadvisor.json       # Dashboard cAdvisor (Fase 2)
│
├── otel-collector/
│   └── otel-collector-config.yml # Pipeline unificado (Fase 5)
│
├── loki/
│   └── loki-config.yml           # Config Loki (Fase 3)
│
├── promtail/
│   └── promtail-config.yml       # Config Promtail (Fase 3)
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
| Uvicorn deployment | https://uvicorn.dev/deployment/ |
| Gunicorn settings | https://gunicorn.org/reference/settings/ |
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
        image: postgres:18-alpine
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

**Tipos de métricas:**

| Tipo | Descripción | Ejemplo en pagos |
|---|---|---|
| Counter | Solo sube, nunca baja. Se resetea al reiniciar | Pagos creados, requests totales |
| Gauge | Sube y baja libremente, refleja estado actual | Workers activos, RAM usada |
| Histogram | Distribución de valores, permite calcular percentiles | Tiempo de respuesta, importes |

**Qué se hace:**
- Añadir `prometheus-fastapi-instrumentator` a `app.py`, que expone `/metrics` automáticamente con métricas HTTP
- Añadir métricas custom de negocio con `prometheus-client`:
  - `payments_created_total` (Counter) con etiqueta `currency`
  - `payments_amount_euros` (Histogram) con buckets por importe y etiqueta `currency`
- Crear `prometheus/prometheus.yml` con la configuración de scraping cada 15s
- Crear provisioning de Grafana: datasource Prometheus y dashboards pre-configurados
- Añadir Prometheus y Grafana al `docker-compose.yml`
- Añadir exporters de infraestructura para monitorizar el servidor y los contenedores
- Verificar todos los targets en Prometheus y explorar dashboards en Grafana

**Exporters de infraestructura:**

En producción no basta con monitorizar la aplicación. Los exporters son agentes
que exponen métricas de sistemas que no hablan Prometheus de forma nativa.

| Exporter | Imagen | Puerto | Qué monitoriza |
|---|---|---|---|
| Node Exporter | `prom/node-exporter` | 9100 | CPU, RAM, disco, red del servidor Linux |
| postgres_exporter | `prometheuscommunity/postgres-exporter` | 9187 | Conexiones, queries, estado de PostgreSQL |
| cAdvisor | `gcr.io/cadvisor/cadvisor` | 8080 | RAM y CPU por contenedor Docker |

Los tres se añaden como servicios en `docker-compose.yml` y como jobs en `prometheus.yml`.

**Dashboards de Grafana provisionados:**

Los dashboards de la comunidad se descargan y se incluyen en el repo como código.
Al arrancar Grafana los carga automáticamente sin intervención manual.

```bash
mkdir -p grafana/dashboards/payment-api
mkdir -p grafana/dashboards/infrastructure

# Dashboard de la app (creado a mano)
# grafana/dashboards/payment-api/payments.json

# Dashboards de la comunidad
curl -s https://grafana.com/api/dashboards/1860/revisions/latest/download \
  -o grafana/dashboards/infrastructure/node-exporter.json
curl -s https://grafana.com/api/dashboards/9628/revisions/latest/download \
  -o grafana/dashboards/infrastructure/postgresql.json
curl -s https://grafana.com/api/dashboards/193/revisions/latest/download \
  -o grafana/dashboards/infrastructure/cadvisor.json

# Los dashboards de comunidad usan una variable de datasource que Grafana
# no resuelve al cargar desde fichero. Hay que reemplazarla con el nombre real:
sed -i 's/\${DS_PROMETHEUS}/Prometheus/g' grafana/dashboards/infrastructure/node-exporter.json
sed -i 's/\${DS_PROMETHEUS}/Prometheus/g' grafana/dashboards/infrastructure/postgresql.json
sed -i 's/\${DS_PROMETHEUS}/Prometheus/g' grafana/dashboards/infrastructure/cadvisor.json
```

**Ficheros nuevos:**
```
prometheus/
└── prometheus.yml
grafana/
├── provisioning/
│   ├── datasources/
│   │   └── prometheus.yml
│   └── dashboards/
│       └── dashboard.yml
└── dashboards/
    ├── payment-api/
    │   └── payments.json
    └── infrastructure/
        ├── node-exporter.json
        ├── postgresql.json
        └── cadvisor.json
```

**Bugs encontrados y corregidos durante la implementación:**
- `payments_amount_euros.observe()` recibía un `Decimal` de SQLAlchemy en vez de `float` -> fix: `float(new_payment.amount)`
- El CI marcaba verde aunque pytest fallaba porque `| tee` ocultaba el exit code de pytest -> fix: `set -o pipefail`
- El CI no arrancaba en PRs de Dependabot porque el trigger solo cubría `push` a `main` -> fix: añadir trigger `pull_request`
- Los dashboards de comunidad mostraban "No data" al provisionar desde fichero -> fix: `sed` para reemplazar `${DS_PROMETHEUS}`

**Generar tráfico para ver los paneles:**
```bash
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/payments \
    -H "Content-Type: application/json" \
    -d "{\"amount\": $((RANDOM % 1000 + 1)).99, \"currency\": \"EUR\"}" > /dev/null
  sleep 0.5
done
```

**Al terminar esta fase tendrás:**
```
FastAPI (/metrics) <-- scraping cada 15s -- Prometheus
Node Exporter      <-- scraping cada 15s -- Prometheus
postgres_exporter  <-- scraping cada 15s -- Prometheus
cAdvisor           <-- scraping cada 15s -- Prometheus
                                                  ↕
                                              Grafana
                               (Payment API · Infrastructure)
```

**URLs añadidas:**
| Servicio | URL |
|---|---|
| Métricas raw | http://localhost:8000/metrics |
| Node Exporter | http://localhost:9100/metrics |
| postgres_exporter | http://localhost:9187/metrics |
| cAdvisor | http://localhost:8080/metrics |
| Prometheus targets | http://localhost:9090/targets |
| Prometheus query | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |

**Para profundizar:**

| Recurso | Enlace |
|---|---|
| Prometheus docs | https://prometheus.io/docs/introduction/overview/ |
| PromQL basics | https://prometheus.io/docs/prometheus/latest/querying/basics/ |
| Prometheus exporters | https://prometheus.io/docs/instrumenting/exporters/ |
| Node Exporter | https://github.com/prometheus/node_exporter |
| postgres_exporter | https://github.com/prometheus-community/postgres_exporter |
| cAdvisor | https://github.com/google/cadvisor |
| Grafana dashboards | https://grafana.com/docs/grafana/latest/dashboards/ |
| Grafana provisioning | https://grafana.com/docs/grafana/latest/administration/provisioning/ |
| prometheus-fastapi-instrumentator | https://github.com/trallnag/prometheus-fastapi-instrumentator |

YouTube:
- Canal **TechWorld with Nana** (Prometheus) -> https://www.youtube.com/@TechWorldwithNana/search?query=Prometheus+Grafana
- Canal **TechWorld with Nana** (Node Exporter) -> https://www.youtube.com/@TechWorldwithNana/search?query=node+exporter
- Canal **That DevOps Guy** (Prometheus exporters) -> https://www.youtube.com/@MarcelDempers/search?query=prometheus+exporter

---

### 🟡 Fase 3: Logs estructurados con Loki

**Concepto:** los logs son la señal más detallada. Un log bien estructurado
te dice exactamente qué pasó, cuándo, en qué contexto y con qué datos.

El problema habitual es que los logs son texto plano y son imposibles de
buscar a escala:

```
# Log plano (inútil para buscar por campo)
2026-05-25 19:30:01 INFO Payment created amount=99.99 currency=EUR

# Log estructurado JSON (filtrable por cualquier campo)
{"event": "payment_created", "level": "info", "timestamp": "2026-05-25T19:30:01Z",
 "payment_id": "dc56ff88", "amount": 99.99, "currency": "EUR"}
```

Promtail recoge los logs de todos los contenedores Docker automáticamente
y los envía a Loki. Grafana los visualiza y permite consultarlos con LogQL.

**Vídeo previo recomendado:**
YouTube -> canal **Grafana** oficial -> https://www.youtube.com/@Grafana/search?query=loki+docker

**Qué se hace:**
- Añadir `structlog` a `app.py` para emitir logs JSON estructurados
- Crear `loki/loki-config.yml` con la configuración de Loki
- Crear `promtail/promtail-config.yml` para recoger logs de todos los contenedores Docker via socket
- Añadir datasource Loki en Grafana via provisioning
- Explorar LogQL en Grafana: filtrar por campo, nivel, servicio

**Scope de logs recogidos:**
- Logs JSON estructurados de FastAPI (evento `payment_created` con `payment_id`, `amount`, `currency`)
- Logs de todos los contenedores Docker (PostgreSQL, Prometheus, Grafana, cAdvisor...) via Promtail

**Ficheros nuevos:**
```
loki/
└── loki-config.yml
promtail/
└── promtail-config.yml
grafana/provisioning/datasources/
└── loki.yml
```

**Queries LogQL de ejemplo:**

```logql
# Todos los logs de la API
{service="api"}

# Solo logs del evento payment_created
{service="api"} |= "payment_created"

# Filtrar por campo JSON: pagos con importe mayor de 500€
{service="api"} | json | amount > 500

# Solo logs de nivel error
{service="api"} | json | level="error"

# Logs de PostgreSQL
{service="db"}

# Todos los contenedores menos Prometheus
{container=~".+"} != "prometheus"
```

**Bug encontrado durante la implementación:**
- Loki 3.x corre como usuario no-root (uid 10001) y no tiene permisos para escribir
  en volúmenes Docker creados como root -> fix: eliminar el volumen externo y dejar
  que Loki use `/tmp/loki` internamente dentro del contenedor

**Nota sobre Promtail:**
Promtail está en modo mantenimiento. Grafana lo está reemplazando por **Grafana Alloy**,
su nuevo agente unificado. Para este proyecto Promtail sigue siendo válido y en Fase 5
lo reemplazaremos por el OTEL Collector.

**Al terminar esta fase tendrás:**
```
FastAPI (JSON logs)         ---> Promtail ---> Loki
Todos los contenedores      ---> Promtail ---> Loki
                                                ↕
                                            Grafana (Explore -> Loki)
```

**URLs añadidas:**
| Servicio | URL |
|---|---|
| Loki (health) | http://localhost:3100/ready |
| Grafana (Loki) | http://localhost:3000 -> Explore -> Loki |

**Para profundizar:**

| Recurso | Enlace |
|---|---|
| Grafana Loki docs | https://grafana.com/docs/loki/latest/ |
| LogQL reference | https://grafana.com/docs/loki/latest/query/ |
| Promtail docs | https://grafana.com/docs/loki/latest/send-data/promtail/ |
| structlog docs | https://www.structlog.org/en/stable/ |
| Grafana Alloy (sucesor de Promtail) | https://grafana.com/docs/alloy/latest/ |

YouTube:
- Canal **Grafana** (Loki) -> https://www.youtube.com/@Grafana/search?query=loki
- Canal **TechWorld with Nana** (Loki) -> https://www.youtube.com/@TechWorldwithNana/search?query=loki
- Canal **That DevOps Guy** (Loki) -> https://www.youtube.com/@MarcelDempers/search?query=loki

---

### 🟣 Fase 4: Trazas distribuidas con Tempo y OpenTelemetry

**Concepto:** una traza muestra el recorrido completo de una petición desde que entra
hasta que sale. Está formada por spans, uno por cada operación del camino:

```
Traza: POST /payments (29.73ms total)
  ├── span: POST /payments http receive    (66µs)
  ├── span: payment.process               (26ms)   <- span custom
  │     ├── span: connect                 (722µs)  <- SQLAlchemy auto
  │     ├── span: INSERT paymentsdb       (2.43ms) <- SQLAlchemy auto
  │     ├── span: connect                 (1.51ms) <- SQLAlchemy auto
  │     └── span: SELECT paymentsdb       (3.43ms) <- SQLAlchemy auto
  └── span: POST /payments http send      (45µs)
```

Las métricas te dicen qué está lento. Las trazas te dicen dónde exactamente.

**¿Qué es Tempo?**

Tempo es el backend de almacenamiento de trazas de Grafana Labs. A diferencia de
Jaeger o Zipkin, Tempo no indexa por defecto — guarda las trazas en object storage
sin índices pesados, lo que lo hace muy barato de operar a escala. Se integra
nativamente con Grafana y acepta el protocolo OTLP estándar.

```
FastAPI --OTLP HTTP (4318)--> Tempo (almacena)
Grafana --HTTP (3200)-------> Tempo (consulta)
```

**¿Por qué el OTEL Collector va en la Fase 5 y no ahora?**

En esta fase el flujo es directo: `FastAPI -> Tempo`. En la Fase 5 el Collector
se pone en medio: `FastAPI -> OTEL Collector -> Tempo/Prometheus/Loki`.

El Collector aporta valor cuando tienes múltiples señales y múltiples destinos:
la app solo habla con un sitio, el Collector decide adónde va cada señal, y si
cambias de backend (de Tempo a Jaeger por ejemplo) solo cambias la config del
Collector sin tocar la app.

**¿Las trazas son solo de la app?**

Las trazas son para aplicaciones, no para infraestructura. Node Exporter o
cAdvisor emiten métricas, no trazas. PostgreSQL no se traza directamente, pero
con `opentelemetry-instrumentation-sqlalchemy` cada query SQL se convierte en
un span dentro de la traza de la petición, mostrando exactamente cuánto tiempo
tarda cada operación de BD.

En arquitecturas con varios microservicios el valor se multiplica: una sola
traza con el mismo `trace_id` recorre todos los servicios.

**Vídeo previo recomendado:**
YouTube -> canal **opentelemetry** oficial -> https://www.youtube.com/@otel-official/search?query=python+fastapi

**Qué se hace:**
- Añadir dependencias OpenTelemetry al `requirements.txt`
- Configurar `TracerProvider` con `OTLPSpanExporter` apuntando a Tempo (HTTP puerto 4318)
- Inyectar `trace_id` y `span_id` en cada log de structlog via `add_trace_context`
- Auto-instrumentación de FastAPI con `FastAPIInstrumentor`
- Auto-instrumentación de SQLAlchemy con `SQLAlchemyInstrumentor`
- Span custom `payment.process` con atributos de negocio (`payment.amount`, `payment.currency`)
- Definir el service name directamente en el código via `Resource.create({SERVICE_NAME: "payment-api"})`
- Crear `tempo/tempo-config.yml` con receptor OTLP HTTP y gRPC
- Añadir datasource Tempo en Grafana con correlación configurada hacia Loki
- Verificar correlación traza -> logs en Grafana

**Dependencias añadidas:**
```
opentelemetry-api==1.41.1
opentelemetry-sdk==1.41.1
opentelemetry-instrumentation-fastapi==0.62b1
opentelemetry-instrumentation-sqlalchemy==0.62b1
opentelemetry-exporter-otlp-proto-http==1.41.1
```

**Ficheros nuevos:**
```
tempo/
└── tempo-config.yml
grafana/provisioning/datasources/
└── tempo.yml
```

**Correlación traza -> logs:**

El campo `trace_id` es el hilo conductor. Cada log JSON de structlog incluye
el `trace_id` del span activo en ese momento. Al abrir una traza en Grafana
y pulsar el icono de logs junto a un span, Grafana ejecuta automáticamente
esta query en Loki:

```logql
{container="payment-api"} | trace_id="0427e8800e08decfeb5dde07610ea6fc"
```

Y muestra el log exacto de ese pago con todos sus campos.

**Bugs encontrados durante la implementación:**
- Usar `OTEL_SERVICE_NAME` como variable de entorno conflictuaba con la
  auto-configuración del SDK -> fix: definir el service name directamente en
  el código con `Resource.create({SERVICE_NAME: "payment-api"})` y eliminar
  la env var
- La correlación Tempo -> Loki usaba el label `service_name` que no existe en
  Loki -> fix: mapear `service.name` al label `container` en el datasource de
  Tempo, que sí existe en Promtail

**Al terminar esta fase tendrás:**
```
FastAPI --OTLP HTTP--> Tempo
                          ↕
                       Grafana (ver traza + saltar a logs de Loki)
```

**URLs añadidas:**
| Servicio | URL |
|---|---|
| Tempo (health) | http://localhost:3200/ready |
| Grafana (Tempo) | http://localhost:3000 -> Explore -> Tempo |

**Para profundizar:**

| Recurso | Enlace |
|---|---|
| Grafana Tempo docs | https://grafana.com/docs/tempo/latest/ |
| OpenTelemetry Python | https://opentelemetry.io/docs/languages/python/ |
| OTel SDK Python | https://opentelemetry-python.readthedocs.io/ |
| OTel FastAPI instrumentation | https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html |
| OTel SQLAlchemy instrumentation | https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/sqlalchemy/sqlalchemy.html |
| TraceQL reference | https://grafana.com/docs/tempo/latest/traceql/ |

YouTube:
- Canal **opentelemetry** oficial -> https://www.youtube.com/@otel-official/search?query=python
- Canal **Grafana** (Tempo) -> https://www.youtube.com/@Grafana/search?query=tempo
- Canal **That DevOps Guy** (OpenTelemetry) -> https://www.youtube.com/@MarcelDempers/search?query=opentelemetry

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
                          -> Loki ---------------------------> MinIO
                          -> Tempo --------------------------> MinIO
                                    Thanos Store Gateway <---- MinIO
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
- **Todos los contenedores tienen `mem_limit`**: para no comprometer los 16 GB del equipo.
- **Thanos Compact se omite en local**: solo tiene sentido con semanas de datos históricos reales.

---

<a name="10-dependabot"></a>
## 🤖 10. Dependabot

Dependabot revisa automáticamente las dependencias del proyecto cada semana y abre
Pull Requests cuando hay versiones nuevas disponibles. Está configurado en
`.github/dependabot.yml` y cubre estos ecosistemas:

| Ecosistema | Qué monitoriza |
|---|---|
| `pip` | `app/requirements.txt` y `requirements-dev.txt` |
| `docker` | Imagen base del `app/Dockerfile` |
| `docker-compose` | Imágenes del `docker-compose.yml` |
| `github-actions` | Versiones de las Actions del workflow de CI (ej. `actions/checkout@v6`) |

Cada semana Dependabot abre PRs automáticos con las actualizaciones disponibles.
El test gate del CI se ejecuta sobre cada PR, de forma que solo se mergea
lo que pasa los tests.

**Limitación importante:** el ecosistema `github-actions` solo monitoriza las versiones
de las Actions, no las imágenes Docker referenciadas como servicios dentro de los workflows
(por ejemplo `postgres:18-alpine` en el job `test`). Esas imágenes hay que revisarlas
y actualizarlas a mano cuando se actualice la imagen principal de PostgreSQL.

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
