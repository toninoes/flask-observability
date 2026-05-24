import multiprocessing
import os

# ---------------------------------------------------------------------------
# Bind
# ---------------------------------------------------------------------------
bind = "0.0.0.0:8000"
backlog = 2048

# ---------------------------------------------------------------------------
# Workers
# WEB_CONCURRENCY permite sobrescribir desde docker-compose o Kubernetes
# sin tocar el código. Fórmula estándar: (CPU * 2) + 1
# ---------------------------------------------------------------------------
workers = int(os.environ.get("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# ---------------------------------------------------------------------------
# Estabilidad
# max_requests: reinicia el worker tras N requests para evitar memory leaks
# max_requests_jitter: añade aleatoriedad para que no reinicien todos a la vez
# timeout: mata el worker si lleva 60s sin responder
# graceful_timeout: tiempo para terminar requests en curso al recibir SIGTERM
# keepalive: segundos esperando siguiente request en conexión persistente
# ---------------------------------------------------------------------------
max_requests = 1000
max_requests_jitter = 100
timeout = 60
graceful_timeout = 30
keepalive = 5

# ---------------------------------------------------------------------------
# Logging
# "-" redirige a stdout/stderr para que Docker recoja los logs correctamente
# ---------------------------------------------------------------------------
accesslog = "-"
errorlog = "-"
loglevel = "info"

# ---------------------------------------------------------------------------
# Proceso
# ---------------------------------------------------------------------------
proc_name = "payment-api"
