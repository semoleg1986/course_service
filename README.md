## Outbox dispatcher

Разовый drain pending outbox-событий:

```bash
python -m src.interface.http.main dispatch-outbox --limit 100
```
