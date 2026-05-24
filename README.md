# 🔭 Observability Lab — FastAPI + OpenTelemetry Stack

Proyecto de aprendizaje progresivo de observabilidad en entornos OpenShift/Kubernetes,
construido sobre una API de pagos en FastAPI y desplegado íntegramente en local con Docker.

---

## 🎯 Objetivo

Aprender las tecnologías del stack de observabilidad de producción de forma incremental,
fase a fase, con una aplicación real como hilo conductor.

El punto de partida es una API de pagos ya existente en Flask. La migraremos a FastAPI
y sobre ella iremos añadiendo, capa a capa, todas las herramientas de observabilidad:
métricas, logs, trazas, retención histórica y visualización.

Al finalizar tendrás en local exactamente la misma arquitectura que se despliega
en OpenShift con Nutanix Objects como storage.

---

## 🏗️ Arquitectura final

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
           │  simula Nutanix Objects             │
           │  bloques Thanos · chunks Loki       │
           │  datos Tempo — retención larga      │
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

## 🖥️ Requisitos del sistema

| Recurso | Mínimo |
|---|---|
| SO | Ubuntu 22.04+ |
| RAM | 8 GB |
| CPU | 4 cores |
| Disco | 10 GB libres |
| Docker Engine | 24+ |
| Docker Compose | v2 (`docker compose`) |
| Python | 3.12+ |

```bash
# Verificar antes de empezar
docker --version
docker compose version
python3 --version
```

---

## 📁 Estructura del proyecto

```
flask-observability/
│
├── app/
│   ├── app.py                    # FastAPI app — endpoints + modelos + métricas
│   ├── Dockerfile
│   └── requirements.txt
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
├── .github/workflows/ci.yml
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🗺️ Itinerario de fases

---

### 🟢 Fase 1 — La API

**Objetivo:** migrar la app existente de Flask a FastAPI y dejarla
funcionando en local con Docker y PostgreSQL. Esta fase no toca nada
de observabilidad — es la base sobre la que construiremos todo lo demás.

**Qué se hace:**
- Migrar `app.py` de Flask a FastAPI
- Añadir modelos Pydantic para request y response
- Validación automática de datos de entrada
- Documentación OpenAPI gratuita en `/docs`
- Actualizar `requirements.txt` y `Dockerfile`
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
| API health | http://localhost:8000/health |
| API pagos | http://localhost:8000/payments |

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

# Importe negativo → 422 Unprocessable Content
curl -i -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": -50, "currency": "EUR"}'

# Moneda inválida → 422 Unprocessable Content
curl -i -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "currency": "eurosss"}'

# Sin importe → 422 Unprocessable Content
curl -i -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"currency": "EUR"}'
```

---

### 🔵 Fase 2 — Métricas con Prometheus y Grafana

**Concepto:** las métricas son la señal más básica de observabilidad.
Responden a preguntas como: ¿cuántas peticiones por segundo recibo?
¿cuánto tardan? ¿cuántos pagos se crean por minuto? ¿hay errores?

Prometheus recoge estas métricas cada 15 segundos haciendo scraping
al endpoint `/metrics` que expone la app. Grafana las visualiza.

**Vídeo previo recomendado:**
YouTube → `Prometheus Grafana Docker Compose tutorial` → canal **TechWorld with Nana**

**Qué se hace:**
- Añadir `prometheus-fastapi-instrumentator` a la app — expone `/metrics` automáticamente
- Añadir métricas de negocio custom: `payments_created_total`, `payments_amount_euros`
- Levantar Prometheus con su config de scraping
- Levantar Grafana con datasource y dashboard pre-provisionados
- Aprender PromQL básico: `rate()`, `histogram_quantile()`

**Al terminar esta fase tendrás:**
```
FastAPI (/metrics) ←── scraping cada 15s ── Prometheus
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

### 🟡 Fase 3 — Logs estructurados con Loki

**Concepto:** los logs son la señal más detallada. Un log bien estructurado
te dice exactamente qué pasó, cuándo, en qué contexto y con qué datos.
El problema habitual es que los logs son texto plano y son imposibles de
buscar a escala. La solución es emitirlos en JSON (logs estructurados)
e indexarlos con Loki para poder buscar con LogQL.

**Vídeo previo recomendado:**
YouTube → `Grafana Loki Docker Compose tutorial` → canal **Grafana** oficial

**Qué se hace:**
- Añadir `structlog` a la app — logging estructurado en JSON
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
| Grafana (Loki) | http://localhost:3000 → Explore → Loki |

---

### 🟣 Fase 4 — Trazas distribuidas con Tempo y OpenTelemetry

**Concepto:** una traza muestra el recorrido completo de una petición
desde que entra hasta que sale. En un sistema con microservicios es
la única forma de saber en qué paso exacto se perdió tiempo o falló algo.
Cada traza está formada por spans — uno por operación (validar, consultar BD, responder).

OpenTelemetry es el estándar CNCF que instrumenta la app para generar esas trazas.
Tempo las almacena. Grafana las visualiza.

**Vídeo previo recomendado:**
YouTube → `OpenTelemetry Python FastAPI tutorial` → canal **opentelemetry** oficial

**Qué se hace:**
- Añadir SDK de OpenTelemetry a la app — auto-instrumentación de FastAPI
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
| Grafana (Tempo) | http://localhost:3000 → Explore → Tempo |

---

### 🟠 Fase 5 — OTEL Collector: el router central

**Concepto:** en producción no se envían métricas, logs y trazas
directamente a sus backends. Todo pasa por un Collector centralizado
que recibe, normaliza, enriquece y enruta cada señal. Es exactamente
el bloque central del diagrama de arquitectura de OpenShift.

**Qué se hace:**
- Levantar OpenTelemetry Collector
- Configurar pipelines: receivers → processors → exporters
- La app solo habla con el Collector — él decide adónde va cada señal
- Reemplazar Promtail por el Collector para logs
- Añadir processors: `batch`, `memory_limiter`, enriquecimiento con metadatos

**Al terminar esta fase tendrás:**
```
FastAPI → OTEL Collector ──→ Prometheus
                         ──→ Loki
                         ──→ Tempo
                                ↓
                             Grafana
```

---

### 🔴 Fase 6 — Retención larga con Thanos y MinIO

**Concepto:** Prometheus solo retiene datos 7-15 días. Para retención
histórica de meses o años en producción se usa Thanos con object storage.

MinIO es S3-compatible al 100% — es exactamente lo mismo que Nutanix Objects
que usas en Voxel, cambiando solo el endpoint y las credenciales. Todo lo
que configures aquí funciona en producción sin cambios.

**Vídeo previo recomendado:**
YouTube → `Thanos Prometheus long term storage tutorial` → canal **That DevOps Guy**

**Qué se hace:**
- Levantar MinIO con buckets `thanos`, `loki`, `tempo`
- Thanos Sidecar junto a Prometheus: sube bloques TSDB a MinIO cada 2h
- Thanos Store Gateway: permite consultar datos históricos en MinIO
- Thanos Query: federa Prometheus local + datos históricos
- Loki y Tempo también persisten en MinIO
- Grafana apunta a Thanos Query en vez de Prometheus directamente

**Al terminar esta fase tendrás el stack completo:**
```
FastAPI → OTEL Collector → Prometheus ←→ Thanos Sidecar ──→ MinIO
                        → Loki ──────────────────────────→ MinIO
                        → Tempo ─────────────────────────→ MinIO
                                   Thanos Store Gateway ←─ MinIO
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

## 🔗 Correlación entre las tres señales

El campo `trace_id` es el hilo conductor de las 3 señales en Grafana:

```
1. Alerta en Prometheus → CPU alta en /payments
           ↓
2. Grafana → buscar logs de ese timestamp en Loki
           ↓
3. El log contiene trace_id → abrir esa traza en Tempo
           ↓
4. La traza muestra qué span tardó → causa raíz identificada
```

Este es exactamente el flujo del diagrama inferior de tu arquitectura de observabilidad.

---

## 📊 Métricas expuestas por la API (Fase 2 en adelante)

| Métrica | Tipo | Descripción |
|---|---|---|
| `http_requests_total` | Counter | Requests por endpoint y status (auto) |
| `http_request_duration_seconds` | Histogram | Latencia HTTP (auto) |
| `payments_created_total` | Counter | Pagos creados por moneda (custom) |
| `payments_failed_total` | Counter | Pagos fallidos por motivo (custom) |
| `payments_amount_euros` | Histogram | Distribución de importes (custom) |

---

## 🏷️ Campos de log (Fase 3 en adelante)

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

## ⚠️ Notas importantes

- **MinIO = Nutanix Objects** a efectos prácticos — misma API S3, misma config.
  Solo cambia el endpoint y las credenciales en producción.
- **Thanos Compact se omite en local** — solo tiene sentido con semanas de datos históricos.
- **Cada fase es acumulativa** — el `docker-compose.yml` crece en cada fase añadiendo servicios.
- **Todos los contenedores tienen `mem_limit`** — para no comprometer los 8 GB del equipo.

---

## 📚 Referencias

| Herramienta | Documentación |
|---|---|
| FastAPI | https://fastapi.tiangolo.com |
| OpenTelemetry Python | https://opentelemetry.io/docs/instrumentation/python |
| Prometheus | https://prometheus.io/docs |
| Grafana Loki | https://grafana.com/docs/loki |
| Grafana Tempo | https://grafana.com/docs/tempo |
| Thanos | https://thanos.io/tip/thanos |
| MinIO | https://min.io/docs |
