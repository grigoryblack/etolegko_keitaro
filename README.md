# Keitaro Campaign Manager

Обёртка над Keitaro Admin API v1: создание кампаний с двумя потоками и редактор
офферов в существующих кампаниях.

## Стек

- FastAPI + SQLAlchemy + Alembic
- httpx — клиент к Keitaro Admin API (`/admin_api/v1`, заголовок `Api-Key`)
- Фронт: один HTML-файл на чистом JS (`app/static/index.html`)

## Функционал

### Создаватор кампаний

`POST /api/campaigns` принимает название, гео-код страны (ISO alpha-2) и ID
оффера Keitaro, плюс опционально `domain_id`, `group_id`, `source_id`
(в UI — выпадающие списки, заполненные из API). Создаёт кампанию и два потока:

1. `GEO -> Google` — обычный поток с фильтром `country = accept [GEO]`,
   редирект (schema `redirect`, `action_type: http`) на Google.
2. `Offer` — поток со схемой `landings`, отправляющий трафик на выбранный оффер.

Созданные кампании сохраняются в локальную БД (таблица `campaigns`).

### Редактор офферов (staged)

Потоки сначала вытягиваются из Keitaro в локальную БД (`Fetch streams again`),
все правки идут локально, поток при этом подсвечивается жёлтым (unpublished).
Публикация — `Push to KTM`, откат — `Cancel`.

- `POST /api/campaigns/{id}/fetch_streams` — синхронизация потоков из Keitaro
  (потоки без офферов тоже сохраняются; офферы, удалённые в Keitaro напрямую,
  помечаются `Removed` и остаются в архиве)
- `GET /api/campaigns/{id}/streams` — локально сохранённые потоки
- `GET /api/offers/search?query=` — автокомплит офферов для добавления
- `POST /api/streams/{id}/offers {offer_id}` — добавить оффер (веса пересчитываются)
- `POST /api/streams/{id}/offers/{oid}/remove` — удалить (статус `Removed`, вес 0)
- `POST /api/streams/{id}/offers/{oid}/restore` — Bring back
- `POST /api/streams/{id}/offers/{oid}/pin` — закрепить вес (не участвует в пересчёте)
- `POST /api/streams/{id}/push` — отправить активные офферы и веса в Keitaro
- `POST /api/streams/{id}/cancel` — откатить неопубликованные изменения

Пересчёт весов: сумма активных офферов всегда 100%; закреплённые (Pin)
сохраняют свой вес, остаток делится поровну между остальными.

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # прописать KEITARO_API_URL и KEITARO_API_KEY
```

### Миграции

```bash
alembic upgrade head
```

Новая миграция при изменении моделей:

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

### Сервер

```bash
uvicorn app.main:app --reload
```

UI: http://localhost:8000/ , Swagger: http://localhost:8000/docs

## Конфигурация (.env)

| Переменная | Описание |
|---|---|
| `KEITARO_API_URL` | Базовый URL Admin API, напр. `https://tracker.example.com/admin_api/v1` |
| `KEITARO_API_KEY` | Ключ из админки Keitaro (Maintenance → Users → Admin API keys) |
| `DATABASE_URL` | SQLAlchemy-строка подключения (по умолчанию SQLite) |
| `GOOGLE_REDIRECT_URL` | URL редиректа гео-потока |
