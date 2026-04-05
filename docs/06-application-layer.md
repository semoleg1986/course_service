# Application Слой

## Назначение

Application-слой оркестрирует use cases, координирует репозитории через порты и предоставляет единый `ApplicationFacade` для interface-адаптеров.

## Структура Application

```shell
src/application/
|- content/
|  |- commands/
|  |- queries/
|  `- handlers/
|- delivery/
|  |- commands/
|  |- queries/
|  `- handlers/
|- access/
|  |- commands/
|  |- queries/
|  `- handlers/
|- evaluation/
|  |- commands/
|  |- queries/
|  `- handlers/
|- facade/
|  `- application_facade.py
`- ports/
   |- repositories.py
   |- unit_of_work.py
   |- event_bus.py
   |- id_generator.py
   |- clock.py
   `- external_clients.py
```

## Command Side (write)

- content: `CreateCourse`, `AddModule`, `AddLesson`, `PublishCourse`, `ArchiveCourse`
- delivery: `EnrollStudent`, `UpdateProgress`
- access: `CreateAccessRequest`, `MarkAccessGrantPaid`, `ApproveAccessGrant`, `RejectAccessGrant`
- evaluation: `StartSubmission`, `SubmitWork`, `GradeSubmission`

## Query Side (read)

- `GetCourseCatalog`
- `GetCourseDetails`
- `GetStudentProgress`
- `ListStudentCourseProgress`
- `ListStudentCompletedCourses`
- `ListPendingAccessGrants`
- `GetParentChildAccessGrants`
- `GetSubmissionResult`

## Контракт Фасада

`ApplicationFacade` — единственная точка входа для interface-слоя:
- принимает типизированные command/query DTO
- делегирует в use-case handlers
- возвращает типизированные DTO или доменные ошибки

## Порты И Транзакции

- `UnitOfWork` инкапсулирует транзакцию и репозитории
- `EventBusPort` публикует доменные события
- внешние клиенты (`users_service`, `attribution-service`) доступны только через порты

## Границы Слоя

- без HTTP/ORM типов в application
- без бизнес-инвариантов в interface
- без инфраструктурных реализаций в domain
