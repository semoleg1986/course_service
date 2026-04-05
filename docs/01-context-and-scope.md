# Bounded Context И Границы

## Название Контекста

**Контекст Учебного Контента И Доставки**

## Назначение Контекста

Контекст управляет жизненным циклом создания и доставки курса.
Он определяет, как контент создается, публикуется, запрашивается к доступу, подтверждается по оплате вручную, одобряется администратором, назначается ученикам и оценивается через сабмиты.

## Ответственность

Контекст обязан:
1. управлять жизненным циклом `Course` и вложенных сущностей (`Module`, `Lesson`)
2. обеспечивать правила публикации через `PublishState`
3. управлять `Enrollment` и `Progress` ученика
4. управлять артефактами оценивания внутри курса (`Assignment`, `QuizCheckpoint`, `Submission`)
5. управлять жизненным циклом `AccessGrant`
6. предоставлять read/query API для учеников, родителей, преподавателей и админов
7. публиковать доменные события для downstream-интеграций

## Структура Агрегатов

```shell
Course (Aggregate Root)
|- Module (Entity)
|  `- Lesson (Entity)
|- Assignment (Entity)
`- QuizCheckpoint (Entity)

Enrollment (Aggregate Root)
`- ProgressEntry (Entity)

Submission (Aggregate Root)
`- GradeAndFeedback (Value Object)

AccessGrant (Aggregate Root)
`- AccessGrantStatus (Value Object)
```

## Внешние Зависимости

Зависит от:
- `auth_service` для identity/roles актора
- `users_service` для проверки существования teacher/student и связей parent-child
- `attribution-service` для валидации referral-token, расчета скидки и фиксации paid-конверсий
- persistence/messaging адаптеров через порты

Не зависит от:
- деталей HTTP-фреймворка в domain/application
- прямого доступа к хранилищу извне
- UI-специфичной логики

## Точки Интеграции

Входящие:
- команды создания/изменения контента от teacher/admin
- родительский flow запроса доступа
- команды админа: ручное подтверждение оплаты и approve/reject доступа
