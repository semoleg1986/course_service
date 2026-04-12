# Доменная Модель

## Назначение

Определяет доменные примитивы и границы агрегатов `course_service`.

## Структура Домена

```shell
src/domain/
|- content/
|  |- course/
|  |  |- entity.py
|  |  |- value_objects.py
|  |  |- repository.py
|  |  |- events.py
|  |  `- policies.py
|- delivery/
|  |- access_grant/
|  |  |- entity.py
|  |  |- value_objects.py
|  |  |- repository.py
|  |  |- events.py
|  |  `- policies.py
|  `- enrollment/
|     |- entity.py
|     |- repository.py
|     |- events.py
|     `- policies.py
|- evaluation/
|  `- submission/
|     |- entity.py
|     |- repository.py
|     |- events.py
|     `- policies.py
|- shared/
|  |- entity.py
|  `- statuses.py
`- errors.py
```

## Корневые Агрегаты

### `Course` (Aggregate Root)
Владеет иерархией module/lesson, состоянием публикации, ownership и ограничениями контента.
Дополнительно содержит доменные поля:
- `teacher_id` (источник истины — `users_service`);
- `teacher_display_name` (snapshot для каталога);
- `schedule.starts_at`;
- `schedule.duration_days`;
- `schedule.enrollment_opens_at` / `schedule.enrollment_closes_at`;
- `schedule.access_ttl_days`;
- `schedule.timezone`;
- `pricing.price` / `pricing.currency`;
- `audience.language` / `audience.level` / `audience.age_min` / `audience.age_max` / `audience.max_students`;
- `delivery.tags` / `delivery.cover_image_url` / `delivery.is_live_enabled` / `delivery.live_room_template_id`;
- расчетные метрики `lessons_total` и `estimated_duration_hours` (правило: 1 урок = 1 час).
- расчетные/системные поля `modules_count`, `is_free`, `published_at`, `published_by_admin_id`, `archived_at`, `archived_by`.

### `Enrollment` (Aggregate Root)
Владеет состоянием участия ученика и прогрессом для пары `(course_id, student_id)`.

### `AccessGrant` (Aggregate Root)
Владеет решением по доступу к курсу для пары `(course_id, student_id)` с ручным подтверждением оплаты и жизненным циклом одобрения.

### `Submission` (Aggregate Root)
Владеет payload попытки, жизненным циклом (`started/submitted/graded`) и результатом оценки.

## Сущности

- `Module`, `Lesson`, `Assignment`, `QuizCheckpoint`, `ProgressEntry`

## Value Objects

- `LessonContent`, `LearningObjective`, `Prerequisite`, `Schedule`, `PublishState`, `TeacherOwnership`, `GradeAndFeedback`, `PaymentConfirmation`, `AccessGrantStatus`

## Репозиторные Порты

- `CourseRepository`
- `EnrollmentRepository`
- `SubmissionRepository`
- `AccessGrantRepository`
