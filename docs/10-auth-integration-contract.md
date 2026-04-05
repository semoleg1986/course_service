# Контракт Интеграции `auth_service` -> `course_service`

## Назначение

Документ фиксирует межсервисный контракт авторизации и проверки доступа к курсам.
Это контракт, а не реализация: любое изменение требует версионирования и ADR.

## Модель Доверия

- `auth_service` выпускает access token (JWT, EdDSA/Ed25519)
- `course_service` валидирует подпись через JWKS (`/.well-known/jwks.json`)
- `course_service` не хранит пароли и не выполняет login/refresh
- права на курс определяются внутри `course_service` по доменным агрегатам (`AccessGrant`, `Enrollment`)

## Обязательные JWT Claims

- `sub` — `account_id` (UUID)
- `roles` — список ролей (`admin`, `teacher`, `parent`, `student`)
- `iss`, `iat`, `exp`, `jti`

Если claim отсутствует или невалиден, запрос отклоняется как `401`.

## Правила Авторизации В `course_service`

- `admin` имеет полный доступ к административным операциям
- `teacher` работает только со своими курсами и материалами
- `parent` может запрашивать доступ и читать прогресс привязанных детей
- `student` обучается только при активном/одобренном доступе

## Internal API: Проверка Доступа К Курсу

Для межсервисного вызова (BFF/API-Gateway/другие сервисы) используется контракт:

- `POST /internal/v1/access/check`
- transport: HTTP JSON
- auth: сервисный токен в `X-Service-Token`

### Request

- `course_id` (UUID)
- `actor_account_id` (UUID)
- `actor_roles` (array<string>)
- `student_id` (UUID|null)
- `require_active_grant` (bool, default `true`)
- `require_enrollment` (bool, default `false`)

### Response

- `decision` (`allow` | `deny`)
- `reason_code` (машиночитаемый код решения)
- `course_id`, `actor_account_id`, `student_id`
- `grant_status`, `enrollment_status` (nullable)
- `checked_at` (date-time UTC)

### Бизнес-Смысл

- endpoint не создает доступ и не меняет состояние агрегатов
- endpoint возвращает только факт решения на момент проверки
- изменение доступа выполняется отдельными командами (`mark-paid`, `approve`, `reject`, `enroll`)

## Коды Ошибок

- `401` — отсутствует/невалиден `X-Service-Token`
- `403` — сервис не имеет права вызывать данный internal endpoint
- `404` — курс не найден
- `422` — невалидный request

## Версионирование Контракта

- backward-compatible изменения допускаются в `v1` (новые optional поля)
- breaking changes только через новый путь (`/internal/v2/...`)
- перед изменением обязательных полей нужен ADR и уведомление потребителей
