# Ubiquitous Language

## Базовые Термины

### Course
Корневой агрегат, который владеет структурой контента, публикацией, владением и расписанием.

### Module
Сущность курса, группирующая уроки в тематический блок.

### Lesson
Сущность курса с учебным контентом и целями.

### LessonContent
Value object типизированного контента: `text | video | file | link`.

### LearningObjective
Value object с ожидаемыми учебными результатами урока/модуля.

### Prerequisite
Value object зависимости между узлами курса без циклов.

### Assignment
Сущность курса для практического/домашнего задания с дедлайном.

### QuizCheckpoint
Сущность курса для формирующей проверки, привязанной к уроку/модулю.

### Enrollment
Корневой агрегат участия ученика в курсе.

### Progress
Состояние прохождения на уровне урока/модуля/курса.

### AccessGrant
Корневой агрегат, контролирующий право ученика на зачисление в курс.
Жизненный цикл: `requested | paid | approved | rejected | revoked`.

### PaymentConfirmation
Value object с метаданными ручного подтверждения оплаты (`confirmed_by_admin_id`, `confirmed_at`, `note`).

### AttributionSnapshot
Value object внутри access grant: `referral_token`, `channel`, `discount_amount`, `discount_type`, `campaign`.
Источник данных — `attribution-service`.

### Submission
Корневой агрегат попытки/ответа ученика и статуса оценивания.

### GradeAndFeedback
Value object результата оценки: балл, rubric outcome, комментарий преподавателя.

### Schedule
Value object временных окон открытия/закрытия и дедлайнов.

### PublishState
Value object enum: `draft | published | archived`.

### CourseSlug
Value object человеко-читаемого уникального URL-сегмента курса.
