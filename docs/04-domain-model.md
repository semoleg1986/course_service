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
