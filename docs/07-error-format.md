# Формат Ошибок (RFC 7807)

`course_service` возвращает ошибки в формате `application/problem+json`.

## Формат Ответа

- `type`
- `title`
- `status`
- `detail`
- `instance` (опционально)
- `request_id` (рекомендуется)

## Пример

```json
{
  "type": "https://api.example.com/problems/invariant-violation",
  "title": "Нарушение инварианта",
  "status": 409,
  "detail": "Курс нельзя публиковать без хотя бы одного модуля и урока",
  "instance": "/v1/admin/courses/8f5f/publish",
  "request_id": "8bc28d0a-3af8-48a6-8c8d-f3915300fef5"
}
```

## Стандартные Типы Проблем

- `/problems/validation` -> `422`
- `/problems/not-found` -> `404`
- `/problems/access-denied` -> `403`
- `/problems/conflict` -> `409`
- `/problems/unauthorized` -> `401`
- `/problems/invariant-violation` -> `409`

## Маппинг Исключений

- `ValidationError` -> `422`
- `NotFoundError` -> `404`
- `AccessDeniedError` -> `403`
- `InvariantViolationError` -> `409`
