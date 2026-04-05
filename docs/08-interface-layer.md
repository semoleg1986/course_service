# Interface Слой

## Назначение

Interface-слой описывает транспортные контракты, валидацию запросов и маппинг ошибок для API-клиентов.
Слой зависит только от application facade и DTO-контрактов.

## Структура

```shell
src/interface/http/
|- app.py
|- main.py
|- health.py
|- errors.py
|- problem_types.py
|- wiring.py
`- v1/
   |- admin/router.py
   |- teacher/router.py
   |- student/router.py
   |- access/router.py
   |- parent/router.py
   |- internal/router.py
   `- schemas/
      |- content.py
      |- delivery.py
      `- evaluation.py
```

## Ответственность

- строить transport adapters (HTTP сейчас, gRPC/CLI позже)
- валидировать request DTO
- маппить application-ошибки в RFC7807
- извлекать actor context и вызывать `ApplicationFacade`
- предоставлять admin-endpoints для модерации access grant
- предоставлять parent-endpoints для чтения прогресса и завершенных курсов ребенка
- предоставлять internal-endpoints для межсервисной проверки доступа к курсам

## Правила Границ

- без SQLAlchemy/session usage
- без доменной логики инвариантов
- без прямого доступа к репозиториям
