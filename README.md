# course_service

Course domain service for content structure and progress.

## Responsibility

`course_service` owns:
- courses, modules, lessons
- publication state
- student lesson completion and progress views
- student learning read model with modules, lessons, progress and next lesson
- course access checks against granted entitlements
- outbox events for downstream integrations

## Local run

### Install
```bash
make install
```

### Run with uvicorn
```bash
uvicorn src.interface.http.main:app --host 0.0.0.0 --port 8001 --reload
```

### Health
```bash
curl -fsS http://127.0.0.1:8001/healthz
```

## Environment

- [course_service/.env.example](/Users/olegsemenov/Programming/curs/course_service/.env.example)
- [course_service/.env.local.example](/Users/olegsemenov/Programming/curs/course_service/.env.local.example)

Key variables:
- `COURSE_DATABASE_URL`
- `COURSE_USE_INMEMORY`
- `COURSE_AUTH_JWKS_URL`
- `COURSE_AUTH_JWKS_JSON`
- `COURSE_SERVICE_TOKEN`

## Tests and quality

```bash
make test
make test-integration
make lint
make format
```

## Migrations

```bash
make migrate-up
make migrate-down-1
```

## Outbox dispatcher

```bash
python -m src.interface.http.main dispatch-outbox --limit 100
```

## Documentation

- [00-vision.md](/Users/olegsemenov/Programming/curs/course_service/docs/00-vision.md)
- [10-auth-integration-contract.md](/Users/olegsemenov/Programming/curs/course_service/docs/10-auth-integration-contract.md)
- [postgres.md](/Users/olegsemenov/Programming/curs/course_service/docs/postgres.md)
