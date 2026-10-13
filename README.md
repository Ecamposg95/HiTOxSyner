# Syner × HiTO — Transformation Room

Workspace privado de advisory para el engagement de Grupo Syner con HiTO. API FastAPI + frontend React servidos desde un solo contenedor.

## Desarrollo local

1. `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
2. Copiar `.env.example` a `.env` y definir `DATABASE_URL`, `TEST_DATABASE_URL` y `JWT_SECRET` (Postgres obligatorio).
3. `alembic upgrade head`
4. `python -m app.seed` (usuarios demo: `admin@syner.demo`, `exec@hito.demo`, `collab@hito.demo`; passwords desde `SEED_*_PASSWORD`).
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
