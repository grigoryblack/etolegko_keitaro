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

### Редактор офферов

- `GET /api/campaigns` — список кампаний из Keitaro
- `GET /api/campaigns/{id}/streams` — потоки кампании с офферами
- `POST /api/campaigns/{cid}/streams/{sid}/offers` — добавить оффер `{offer_id, share}`
- `PUT /api/campaigns/{cid}/streams/{sid}/offers/{oid}` — изменить долю оффера
- `DELETE /api/campaigns/{cid}/streams/{sid}/offers/{oid}` — удалить оффер

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
