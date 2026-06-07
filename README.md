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
- `COURSE_COMMERCIAL_CATALOG_SERVICE_BASE_URL`
- `COURSE_COMMERCIAL_CATALOG_SERVICE_TOKEN`
- `COURSE_COMMERCIAL_CATALOG_SERVICE_TIMEOUT_SECONDS`

## Tests and quality

```bash
make test
make test-integration
make lint
make format
```

## Admin/studio authoring API

`course_service` exposes backend-owned read models for `studio_app`, so the
frontend does not assemble course editor state from unrelated responses.

- `GET /v1/admin/courses?publish_state=&teacher_id=&q=&limit=&offset=` — paginated
  list of draft/published/archived courses for admin/studio. Response includes
  `items`, `total`, `limit`, `offset`; list items include authoring audit fields
  `created_by` and `updated_by`.
- `GET /v1/admin/courses/{course_id}/authoring` — full editor read model:
  course summary, modules, lessons, statuses, positions, content refs,
  `readiness`, `has_unpublished_changes`, `draft_version` and
  `published_version`.
  `readiness.checks` includes `has_default_offer`; this is resolved through
  `commercial_catalog_service` because prices/offers are not owned by
  `course_service`.
- `POST /v1/admin/courses` / `PATCH /v1/admin/courses/{course_id}` — create and
  update course metadata.
- `POST /v1/admin/courses/{course_id}/modules` — append module.
- `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons` — append
  lesson.
- `PATCH /v1/admin/courses/{course_id}/modules/{module_id}` — update module.
- `PATCH /v1/admin/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}`
  — update lesson.
- `POST /v1/admin/courses/{course_id}/modules/reorder` — reorder all current
  modules. Request must include the full module list with continuous positions
  from `1` using `{ "module_id": "...", "position": 1 }`.
- `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons/reorder` —
  reorder all current lessons in a module. Request must include the full lesson
  list with continuous positions from `1` using
  `{ "lesson_id": "...", "position": 1 }`.
- `POST /v1/admin/courses/{course_id}/modules/{module_id}/archive` — archive a
  module through `status=archived`.
- `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/archive`
  — archive a lesson through `status=archived`.
- `POST /v1/admin/courses/{course_id}/modules/{module_id}/duplicate` — create a
  draft copy of a module and its lessons with fresh IDs.
- `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/duplicate`
  — create a draft copy of a lesson with a fresh ID.
- `POST /v1/admin/courses/{course_id}/publish` / `archive` — publish lifecycle.

After write mutations, clients should refetch
`GET /v1/admin/courses/{course_id}/authoring` instead of keeping local domain
state.

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
