# Syner × HiTO — Transformation Room

Workspace privado de advisory para el engagement de Grupo Syner con HiTO. API FastAPI + frontend React servidos desde un solo contenedor.

## Desarrollo local

1. `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
2. Copiar `.env.example` a `.env` y definir `DATABASE_URL`, `TEST_DATABASE_URL` y `JWT_SECRET` (Postgres obligatorio).
3. `alembic upgrade head`
4. `python -m app.seed` (usuarios demo: `admin@syner.demo`, `exec@hito.demo`, `collab@hito.demo`; passwords desde `SEED_*_PASSWORD`). Crea datos `[Demo]` para findings, initiatives, actions, milestones, meetings, decisions, documents y comments; es idempotente por módulo y solo añade datos demo cuando el engagement contiene las 4 initiatives `[Demo]`; en un engagement con datos reales no toca nada.
5. `uvicorn app.main:app --reload` → API en `http://localhost:8000/api`, docs en `/api/docs`.
6. Frontend: `cd frontend && npm install && npm run dev` → `http://localhost:5173` con proxy a `/api`.

### Postgres local sin sudo (WSL)

En este entorno Postgres 16 corre en espacio de usuario: binarios en `~/.local/pg`, datos en `~/.local/pgdata`.
Si está detenido: `~/.local/pg/bin/pg_ctl -D ~/.local/pgdata -l ~/.local/pgdata/server.log -o "-p 5432 -k /tmp" start`.
Rol `hitoxsyner` / password `hitoxsyner` con CREATEDB; bases `hitoxsyner_dev` (desarrollo) y `hitoxsyner_test` (tests).

## Tests

`pytest` usa `TEST_DATABASE_URL`, crea el esquema desde los modelos y trunca tablas entre tests.

## Build y deploy

- `cd frontend && npm run build` genera `frontend/dist`, que FastAPI sirve en `/`.
- Railway construye con el `Dockerfile`; el contenedor ejecuta `alembic upgrade head` y luego `uvicorn`.
- Variables en Railway: `DATABASE_URL`, `JWT_SECRET`, `ENVIRONMENT=production`, `SEED_*_PASSWORD` (solo si se corre el seed).
- Health: `GET /api/health`.

### Despliegue en Railway

- El builder del servicio debe ser Dockerfile. Hoy se fuerza con la variable de servicio `RAILWAY_DOCKERFILE_PATH=Dockerfile` (configurada en el dashboard, fuera del repo).
- `railway up` desde un mount `/mnt/d` de WSL sube archivos corruptos (bytes NUL). Copia el repo al filesystem nativo y despliega desde ahí:
  `rsync -a --exclude .venv --exclude node_modules --exclude .git /mnt/d/Devs/HiTOxSyner/ ~/hitoxsyner-upload/` y luego, dentro de `~/hitoxsyner-upload/`, `railway up --service HiTOxSyner --detach`.
- `railway ssh` puede requerir `-i ~/.ssh/id_railway_atlas`.
- El seed de producción corre dentro del contenedor: `railway ssh --service HiTOxSyner -- python -m app.seed`.
- La base `hitoxsyner` vive en el servicio Postgres compartido y se creó con `railway ssh --service Postgres -- psql -U postgres -c 'CREATE DATABASE "hitoxsyner"'`.
- Variables del servicio: `ENVIRONMENT=production`, `DATABASE_URL`, `JWT_SECRET` (≥32 bytes), `JWT_EXPIRE_HOURS`, `CORS_ORIGINS`, `RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`, `SEED_SYNER_PASSWORD`, `SEED_EXEC_PASSWORD`, `SEED_COLLAB_PASSWORD`. Nunca se versionan sus valores.
- En producción la app no arranca con `JWT_SECRET` por defecto o menor a 32 caracteres, y el seed se niega a usar las passwords demo.
