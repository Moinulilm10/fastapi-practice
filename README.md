# fastapi-practice

## PostgreSQL setup

For Docker Compose, copy `.env.example` to `.env` and set a private password:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace_with_a_private_password
POSTGRES_DB=fastapi_practice
```

Start PostgreSQL and the API:

```bash
docker compose up -d
```

The application creates the tables during startup. The Compose file builds the
internal `DATABASE_URL` from the private variables in `.env`; credentials are
not stored in `docker-compose.yml`. SQLTools connects through `127.0.0.1:5432`.

For running FastAPI outside Docker, set this additional local variable in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/fastapi_practice
```

Keep `.env` local and do not commit database passwords or other secrets.

## Database migrations

Alembic manages PostgreSQL schema changes. Apply migrations with:

```bash
uv run alembic upgrade head
```

After changing a SQLAlchemy model, create a migration:

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

If the existing database was created before Alembic was added, mark it as
matching the initial migration once, without recreating its tables:

```bash
uv run alembic stamp head
```
