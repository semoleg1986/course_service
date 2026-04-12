# Infrastructure Слой

## Назначение

Infrastructure-слой реализует выходные адаптеры для application-портов.
Слой заменяем без изменений в domain/application.

## Структура

```shell
src/infrastructure/
|- db/
|  |- session.py
|  |- models.py
|  |- mappers.py
|  |- repositories/
|  |  |- course_repository_sqlalchemy.py
|  |  |- enrollment_repository_sqlalchemy.py
|  |  `- submission_repository_sqlalchemy.py
|  `- uow/sqlalchemy_uow.py
|- storage/
|  `- media_storage_s3.py
|- messaging/
|  |- outbox_publisher.py
|  `- event_bus_kafka.py
|- clients/
|  |- users_service_client.py
|  `- attribution_service_client.py
`- di/
   `- providers.py
```

## Ответственность

- реализовать репозитории и `UnitOfWork`
- реализовать медиа-метаданные и object-storage адаптеры (presigned URL flow)
- реализовать outbox/event bus публикацию
- реализовать внешние клиенты (`users_service` для teacher lookup, опционально другие)
- собрать DI composition root для runtime

## Правила Границ

- без HTTP-контрактов в infrastructure
- без use-case orchestration в infrastructure
- без доменных policy-решений в infrastructure
