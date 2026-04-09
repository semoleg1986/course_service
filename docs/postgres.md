# PostgreSQL: запуск course_service

## 1. URL подключения

Используйте переменную окружения `COURSE_DATABASE_URL`:

```bash
export COURSE_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/course_service'
```

## 2. Миграции

Применить миграции:

```bash
make migrate-up
```

Откатить последнюю миграцию:

```bash
make migrate-down-1
```

## 3. Локальный запуск API

```bash
export COURSE_USE_INMEMORY=0
uvicorn src.interface.http.main:app --reload
```

## 4. Auth интеграция (JWT + JWKS)

`course_service` проверяет Bearer access token от `auth_service` по JWKS:

- `COURSE_AUTH_ISSUER` (по умолчанию `auth_service`)
- `COURSE_AUTH_AUDIENCE` (по умолчанию `platform_clients`)
- `COURSE_AUTH_JWKS_URL`
- `COURSE_AUTH_JWKS_JSON` (опционально, для тестов)

Ожидается `typ=access` в JWT claims.

## 5. Интеграционные тесты (Postgres)

Перед запуском создайте тестовую БД:

```bash
docker exec curs_postgres psql -U postgres -d postgres -c "CREATE DATABASE course_service_test;"
```

Запуск интеграционных тестов:

```bash
COURSE_DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/course_service_test' make test-integration
```
