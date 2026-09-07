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
