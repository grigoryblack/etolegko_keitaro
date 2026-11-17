# Keitaro Campaign Manager

Обёртка над админкой Keitaro: создание кампаний с двумя потоками и staged-редактор
офферов в существующих кампаниях.

## Стек

- Backend: FastAPI + SQLAlchemy + Alembic + httpx
- Frontend: React + Vite + Tailwind + shadcn/ui (`frontend/`)
- Auth: логин/пароль админки Keitaro через форму в UI (без .env).
  Бэкенд вызывает `POST {tracker}/admin/?object=auth.login`, получает сессионную
  куку `states` и дальше работает через legacy object API `/admin/?object=...`
  (аналог Admin API v1). Сессия хранится в памяти сервера.

## Функционал

### Создаватор кампаний

`POST /api/campaigns` принимает название, гео-код страны (ISO alpha-2) и ID
оффера Keitaro, плюс опционально `domain_id`, `group_id`, `source_id`.
Создаёт кампанию и два потока:

1. `GEO -> Google` — поток с фильтром `country = accept [GEO]`,
   редирект (schema `redirect`, `action_type: http`) на Google.
2. `Offer` — поток со схемой `landings`, весь трафик на выбранный оффер.

Созданные кампании сохраняются в локальную БД (таблица `campaigns`).

### Редактор офферов (staged)

Потоки сначала вытягиваются из Keitaro в локальную БД (`Fetch streams again`),
все правки идут локально, поток при этом подсвечивается жёлтым (unpublished).
Публикация — `Push to KTM`, откат — `Cancel`.

- `POST /api/campaigns/{id}/fetch_streams` — синхронизация потоков из Keitaro
  (потоки без офферов тоже сохраняются; офферы, удалённые в Keitaro напрямую,
  помечаются `Removed` и остаются в архиве)
- `GET /api/campaigns/{id}/streams` — локально сохранённые потоки
- `GET /api/offers/search?query=` — автокомплит офферов
- `POST /api/streams/{id}/offers {offer_id}` — добавить оффер (веса пересчитываются)
- `POST /api/streams/{id}/offers/{oid}/remove` — удалить (статус `Removed`, вес 0)
- `POST /api/streams/{id}/offers/{oid}/restore` — Bring back
- `POST /api/streams/{id}/offers/{oid}/pin` — закрепить вес
- `POST /api/streams/{id}/push` — отправить активные офферы и веса в Keitaro
- `POST /api/streams/{id}/cancel` — откатить неопубликованные изменения

Пересчёт весов: сумма активных офферов всегда 100%; закреплённые (Pin)
сохраняют свой вес, остаток делится поровну между остальными.

Auth endpoints: `POST /api/auth/login {base_url, login, password}`,
`POST /api/auth/logout`, `GET /api/auth/status`.

## Запуск

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload   # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173 (прокси /api → :8000)
```

Открыть http://localhost:5173, в форме ввести URL трекера
(например `https://tlgk.host`) и креды админки.

### Миграции

```bash
alembic upgrade head                              # применить
alembic revision --autogenerate -m "message"      # новая миграция
```

## Конфигурация (.env)

| Переменная | Описание |
|---|---|
| `DATABASE_URL` | SQLAlchemy-строка подключения (по умолчанию SQLite) |
| `GOOGLE_REDIRECT_URL` | URL редиректа гео-потока |
