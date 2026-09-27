# fastapi-practice

## PostgreSQL setup

For Docker Compose, copy `.env.example` to `.env` and set a private password:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=replace_with_a_private_password
POSTGRES_DB=fastapi_practice
PGADMIN_DEFAULT_EMAIL=admin@fastapi.local
PGADMIN_DEFAULT_PASSWORD=replace_with_a_private_pgadmin_password
IMAGEKIT_PRIVATE_KEY=replace_with_your_imagekit_private_key
IMAGEKIT_PUBLIC_KEY=replace_with_your_imagekit_public_key
IMAGEKIT_URL=https://ik.imagekit.io/your_imagekit_id
SECRET=replace_with_a_long_random_secret
```

Start PostgreSQL, the API, and pgAdmin:

```bash
make up
```

This builds the API image when needed and starts both containers in the
background. To follow the application and database logs, run `make logs`.
Stop the project with `make down`.

Open pgAdmin at `http://localhost:5050` and sign in with the pgAdmin email and
password from `.env`. Register a server with host `db`, port `5432`, and the
PostgreSQL username, password, and database from `.env`.

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
