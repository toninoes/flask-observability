# flask-observability

Proyecto de aprendizaje personal para dominar el stack de observabilidad moderno construyendo una API de pagos en Flask, desplegada con Docker y monitorizadas con Prometheus, Grafana, Loki, OpenTelemetry y Tempo.

---

## Índice

- [Objetivo](#objetivo)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Requisitos previos](#requisitos-previos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Fases de aprendizaje](#fases-de-aprendizaje)
- [Cómo levantar el entorno](#cómo-levantar-el-entorno)
- [Endpoints de la API](#endpoints-de-la-api)
- [CI/CD](#cicd)

---

## Objetivo

Aprender de forma práctica y progresiva las tecnologías de observabilidad que se usan en entornos reales de producción, partiendo de una API sencilla e incorporando cada pilar del stack en fases separadas:

1. **Métricas** → Prometheus + Grafana
2. **Logs** → Loki
3. **Trazas** → OpenTelemetry + Tempo

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| API | Python 3.14 + Flask 3.1.x + Gunicorn 26.x |
| Base de datos | PostgreSQL 17 + SQLAlchemy 2.x + psycopg3 |
| Contenedores | Docker Engine 29.x + Docker Compose v2 |
| Registry | GitHub Container Registry (GHCR) |
| CI/CD | GitHub Actions (ubuntu-24.04) |
| Métricas | Prometheus + Grafana |
| Logs | Loki |
| Trazas | OpenTelemetry + Tempo |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                     │
│                                                     │
│  ┌──────────┐   ┌────────────┐   ┌───────────────┐ │
│  │ Flask    │   │ Prometheus │   │    Grafana    │ │
│  │ Payment  │──▶│            │──▶│  (dashboards) │ │
│  │ API      │   └────────────┘   └───────────────┘ │
│  │ :5000    │                                       │
│  │          │   ┌────────────┐                      │
│  │          │──▶│    Loki    │ (logs)               │
│  │          │   └────────────┘                      │
│  │          │                                       │
│  │          │   ┌────────────┐   ┌───────────────┐ │
│  │          │──▶│   OTel     │──▶│    Tempo      │ │
│  │          │   │ Collector  │   │   (trazas)    │ │
│  └──────────┘   └────────────┘   └───────────────┘ │
│       │                                             │
│  ┌────▼─────┐                                       │
│  │ PostgreSQL│                                      │
│  │  :5432   │                                       │
│  └──────────┘                                       │
└─────────────────────────────────────────────────────┘
```

---

## Requisitos previos

- Docker Engine 29.x o superior
- Docker Compose v2 (`docker compose`)
- Git

Verificar instalación:

```bash
docker --version && docker compose version
```

---

## Estructura del proyecto

```
flask-observability/
├── .github/
│   └── workflows/
│       └── ci.yml          # Pipeline CI → build + push a GHCR
├── app/
│   ├── app.py              # API Flask
│   ├── requirements.txt    # Dependencias Python
│   └── Dockerfile          # Imagen de la API
├── prometheus/             # Configuración Prometheus (Fase 2)
├── grafana/                # Dashboards y datasources (Fase 2)
├── docker-compose.yml      # Stack completo
├── .gitignore
├── LICENSE
└── README.md
```

---

## Fases de aprendizaje

### ✅ Fase 1 — Flask API + PostgreSQL + Docker + CI/CD

**Objetivo:** Construir la API base con persistencia real, dockerizarla y automatizar la publicación de la imagen en GHCR.

**Qué se implementa:**
- API Flask con 3 endpoints: `/health`, `GET /payments`, `POST /payments`
- Gunicorn como servidor WSGI de producción (2 workers)
- PostgreSQL 17 como base de datos con persistencia en volumen Docker
- SQLAlchemy 2.x + psycopg3 como ORM y driver
- Dockerfile con Python 3.14-slim
- Pipeline GitHub Actions que construye y publica la imagen en GHCR automáticamente en cada push a `main` que afecte a `app/`
- Runner fijado a `ubuntu-24.04` para reproducibilidad

**Conceptos clave:**
- Docker build + image layers + cache
- Volúmenes Docker para persistencia de datos
- GitHub Container Registry (GHCR) — imagen pública sin autenticación
- Tags de imagen: `latest` + `sha-<commit>` para trazabilidad
- Gunicorn vs servidor de desarrollo Flask
- psycopg3 vs psycopg2 — driver moderno con soporte nativo async
- Healthcheck en Docker Compose con `condition: service_healthy`
- Problema de Docker snap vs Docker Engine nativo en Ubuntu

**Recursos:**
- [Docker Engine install](https://docs.docker.com/engine/install/ubuntu/)
- [GitHub Actions — Publishing to GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [docker/build-push-action](https://github.com/docker/build-push-action)
- [Flask documentation](https://flask.palletsprojects.com/)
- [Gunicorn documentation](https://docs.gunicorn.org/)
- [psycopg3 documentation](https://www.psycopg.org/psycopg3/docs/)
- [SQLAlchemy 2.x ORM](https://docs.sqlalchemy.org/en/20/)

---

### 🔲 Fase 2 — Métricas con Prometheus + Grafana

**Objetivo:** Exponer métricas de la API y visualizarlas en dashboards.

**Qué se implementará:**
- Endpoint `/metrics` con `prometheus-flask-exporter`
- Métricas: total de pagos, latencia por endpoint, errores
- Prometheus scrapeando la API
- Dashboard en Grafana con los datos en tiempo real

**Recursos:**
- [prometheus-flask-exporter](https://github.com/rycus86/prometheus_flask_exporter)
- [Prometheus — Getting started](https://prometheus.io/docs/prometheus/latest/getting_started/)
- [Grafana — Prometheus datasource](https://grafana.com/docs/grafana/latest/datasources/prometheus/)
- 📺 Video recomendado: [Prometheus & Grafana tutorial](https://www.youtube.com/results?search_query=prometheus+grafana+docker+compose+tutorial)

---

### 🔲 Fase 3 — Logs estructurados con Loki

**Objetivo:** Centralizar y consultar los logs de la API desde Grafana.

**Qué se implementará:**
- Logging estructurado en JSON con `python-json-logger`
- Loki como backend de logs
- Promtail como agente de recolección
- Consultas en Grafana con LogQL

**Recursos:**
- [Loki — Getting started](https://grafana.com/docs/loki/latest/get-started/)
- [python-json-logger](https://github.com/madzak/python-json-logger)
- [LogQL cheatsheet](https://grafana.com/docs/loki/latest/query/)

---

### 🔲 Fase 4 — Trazas con OpenTelemetry + Tempo

**Objetivo:** Instrumentar la API con trazas distribuidas y visualizarlas en Tempo.

**Qué se implementará:**
- Instrumentación automática con `opentelemetry-instrumentation-flask`
- OpenTelemetry Collector como intermediario
- Tempo como backend de trazas
- Correlación logs + métricas + trazas en Grafana

**Recursos:**
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [OTel Collector](https://opentelemetry.io/docs/collector/)

---

### 🔲 Fase 5 (opcional/avanzada) — Alta disponibilidad de métricas con Thanos

**Cuándo tiene sentido:** cuando hay múltiples instancias de Prometheus (varios clústeres, varios entornos) y se necesita almacenamiento a largo plazo, consultas federadas o alta disponibilidad del sistema de métricas. En un entorno con múltiples clústeres OpenShift, Thanos es la pieza que une todo.

En este proyecto con un solo Prometheus en local **no es necesario**, pero se documenta como referencia para cuando se aplique en un entorno real.

**Qué aportaría:**
- Retención de métricas más allá de los 15 días por defecto de Prometheus
- Consultas unificadas entre múltiples Prometheus
- Almacenamiento en object storage (S3, MinIO, Azure Blob, Nutanix Objects)
- Alta disponibilidad del sistema de métricas

**Recursos:**
- [Thanos — Getting started](https://thanos.io/tip/thanos/getting-started.md/)
- [Thanos con MinIO (S3-compatible)](https://thanos.io/tip/thanos/storage.md/)
- [Caso de referencia Amadeus](https://www.cncf.io/case-studies/amadeus/)

---

## Cómo levantar el entorno

### Usando la imagen de GHCR (recomendado)

```bash
docker compose up -d
```

### Construyendo localmente

```bash
docker compose up --build -d
```

### Verificar que está corriendo

```bash
docker compose ps
docker compose logs -f api
```

### Parar el entorno (conservando datos)

```bash
docker compose down
```

### Parar el entorno eliminando datos

```bash
docker compose down -v
```

---

## Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Healthcheck de la API |
| GET | `/payments` | Lista todos los pagos |
| POST | `/payments` | Crea un nuevo pago |

### Ejemplos

```bash
# Healthcheck
curl http://localhost:5000/health

# Listar pagos
curl http://localhost:5000/payments

# Crear pago
curl -X POST http://localhost:5000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 99.99, "currency": "EUR"}'
```

---

## CI/CD

El pipeline de GitHub Actions se dispara en cada push a `main` que modifique archivos en `app/` o el propio workflow.

**Flujo:**

```
git push → GitHub Actions (ubuntu-24.04) → docker build → ghcr.io/toninoes/flask-observability/api:latest
                                                        → ghcr.io/toninoes/flask-observability/api:sha-<commit>
```

La imagen está disponible públicamente en:
`ghcr.io/toninoes/flask-observability/api:latest`
