# Инварианты И Политики

## Бизнес-Инварианты

1. `Module` и `Lesson` не существуют вне агрегата `Course`.
2. Курс переводится в `published` только если структура валидна:
   - есть минимум один модуль
   - есть минимум один модуль в статусе `published`
   - в каждом `published` модуле есть минимум один `published` урок
   - SEO-минимум валиден: непустые `slug`, `meta_title`, `meta_description`
3. `Enrollment` уникален по `(course_id, student_id)`.
4. `Course.slug` уникален среди активных (`draft|published`) курсов.
5. `AccessGrant` уникален по `(course_id, student_id)`.
6. Enrollment разрешен только когда:
   - курс в `published`
   - статус access grant равен `approved`
7. Переход access grant в `paid` выполняется только явным действием админа.
8. Переход access grant в `approved` возможен только из состояния `paid`.
9. Attribution-данные (`token`, `channel`, `discount`) фиксируются снимком при запросе и не переписываются тихо после `paid`.
10. Сабмит принадлежит ровно одной паре `(enrollment_id, assignment_or_quiz_id)`.
11. Оценка выставляется только после состояния `submitted`.
12. Архивный курс не принимает новые enrollment и submission.

## Политики Доступа

- `AdminPolicy`: отмечает оплату, одобряет/отклоняет доступ, модерирует курсы.
- `TeacherPolicy`: изменяет только собственные или разрешенные к редактированию курсы.
- `StudentPolicy`: читает доступный контент и отправляет только свои работы.
- `ParentPolicy`: читает прогресс/завершенные курсы ребенка только по подтвержденной связи из `users_service`.
- `ParentPolicy`: создает запросы доступа и видит статусы доступа своего ребенка.

## Стратегия Применения

- методы агрегатов обеспечивают state-инварианты
- доменные политики обеспечивают role-based разрешения
- application-хендлеры делают оркестрацию и межагрегатные проверки
- interface-слой маппит нарушения в RFC7807

## Идемпотентность И Повторы

- `POST /v1/student/courses/{course_id}/lessons/{lesson_id}/complete`
  - рассматривается как strict-idempotent бизнес-команда по natural key `(student_id, lesson_id)`
  - повтор не должен создавать дубликаты прогресса и оставляет completed-state неизменным
- `GET /v1/student/courses/{course_id}/progress`
  - read-only endpoint; безопасен для повторов и polling
- `GET /v1/student/courses/{course_id}/learning`
  - read-only endpoint; безопасен для повторов и polling
  - возвращает только published modules/lessons
  - требует роль `student` и активный approved access grant
  - отдает normalized read model: course summary, progress, lessons completion
    state и `next_lesson_id`
- `GET /v1/parent/students/{student_id}/courses/progress`
  - read-only endpoint; безопасен для повторов и polling
- `GET /v1/parent/students/{student_id}/courses/completed`
  - read-only endpoint; безопасен для повторов и polling
- `POST /v1/internal/access/course-access-granted`
  - replay-safe по `event_id`
  - повторная доставка одного и того же события должна быть зафиксирована как `replay`, а не как вторичное изменение состояния
- admin-команды создания и мутации структуры курса:
  - `POST /v1/admin/courses`
  - `PATCH /v1/admin/courses/{course_id}`
  - `POST /v1/admin/courses/{course_id}/modules`
  - `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons`
  - `PATCH /v1/admin/courses/{course_id}/modules/{module_id}`
  - `PATCH /v1/admin/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}`
  - `POST /v1/admin/courses/{course_id}/modules/reorder`
  - `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons/reorder`
  - `POST /v1/admin/courses/{course_id}/modules/{module_id}/archive`
  - `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/archive`
  - `POST /v1/admin/courses/{course_id}/modules/{module_id}/duplicate`
  - `POST /v1/admin/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/duplicate`
  - по умолчанию не считаются idempotent и не должны ретраиться вслепую без client-side discipline
- reorder-команды принимают полный текущий список элементов:
  - позиции должны быть непрерывными с `1`
  - дубликаты `module_id`/`lesson_id`/`position` запрещены
  - пропущенные или лишние элементы отклоняются как нарушение инварианта
- duplicate-команды создают новые сущности только в `draft`, даже если источник
  был `published`, чтобы копия не попадала в delivery без явной публикации.
- `POST /v1/admin/courses/{course_id}/publish` и `POST /v1/admin/courses/{course_id}/archive`
  - защищены state-инвариантами
  - но не объявлены strict-idempotent: повтор может быть отклонен текущим состоянием курса
