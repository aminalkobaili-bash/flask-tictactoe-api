# Flask Tic-Tac-Toe API

**Задача:** REST API для крестиков-ноликов: игра против компьютера (minimax) и между двумя пользователями, JWT-аутентификация с access- и refresh-токенами, история игр и рейтинг игроков на PostgreSQL.

**Стек:** Python 3.12 · Flask 3.1.3 · flask-jwt-extended 4.7.4 · SQLAlchemy 2.0.51 · psycopg 3.3.4 · PostgreSQL · Werkzeug (scrypt) · python-dotenv
Использование библиотек сверено с актуальной документацией через Context7: `DeclarativeBase` (SQLAlchemy 2.0), claim `type` в токенах flask-jwt-extended, `generate_password_hash` со scrypt по умолчанию (Werkzeug 3).

## Архитектура

```
web/          routes, handlers, request/response DTO, JWT provider
   │  зависит от
   ▼
domain/       модели (Game, GameField, User), сервисы (игра, minimax, auth), исключения
   ▲  реализует интерфейсы репозиториев
   │
datasource/   ORM-модели SQLAlchemy, мапперы ORM ↔ domain, Postgres-репозитории
di/container.py — собирает репозитории, сервисы и JWT-провайдер
main.py        — app factory: JWTManager, before_request (Bearer-токен → g.user_uuid), маршруты
```

- **Аутентификация:** глобальный `before_request` проверяет `Authorization: Bearer <access token>` для всех маршрутов, кроме `/signup`, `/login`, `/refresh/*`.
- **Ход** — клиент присылает всё поле 3×3. Сервер проверяет, что изменилась ровно одна пустая клетка и в неё поставлен символ игрока, чья сейчас очередь. Затем определяет победу или ничью, а в игре против компьютера сразу делает ответный ход.
- **Компьютер** — полный перебор minimax с учётом глубины, поэтому игра против него заканчивается победой компьютера или ничьей.
- **Ошибки** домена (`DomainError` и наследники) превращаются в JSON `{"error", "details"}` с кодами 400 / 401 / 404.

## API

| Метод | Путь | Auth | Что делает |
|---|---|---|---|
| POST | `/signup` | — | регистрация `{login, password}` |
| POST | `/login` | — | пара токенов `{type, accessToken, refreshToken}` |
| POST | `/refresh/access` | refresh token в теле | новый access-токен |
| POST | `/refresh/refresh` | refresh token в теле | новая пара токенов |
| GET | `/users/me` | access | текущий пользователь |
| GET | `/users/<uuid>` | access | пользователь по id |
| POST | `/games` | access | новая игра `{"game_type": "computer" \| "human"}` |
| GET | `/games` | access | игры, ожидающие второго игрока |
| POST | `/games/<uuid>/join` | access | присоединиться к игре |
| GET | `/games/<uuid>` | access | состояние игры |
| POST | `/game/<uuid>` | access | ход: `{"field": [[…],[…],[…]]}` |
| GET | `/games/history` | access | завершённые игры пользователя |
| GET | `/leaderboard?limit=N` | access | топ-N по `win_ratio` = победы / (поражения + ничьи) |
| POST | `/game` | access | **Legacy endpoint (v1):** игра против компьютера, оставлен для совместимости с первой версией API |

Примеры запросов со всеми сценариями и ошибками: [`docs/api-examples.md`](docs/api-examples.md).

## Что сделано

1. **v1:** Flask API с игрой против компьютера (minimax), хранение в памяти, слоистая архитектура web / domain / datasource с DI-контейнером.
2. **v2:** PostgreSQL через SQLAlchemy ORM, мапперы ORM ↔ domain, пользователи, игра двух людей (создание, список ожидающих, присоединение, очерёдность ходов).
3. **v3:** JWT вместо Basic Auth — access-токен на 15 минут, refresh на 7 дней, эндпоинты обновления. История игр и leaderboard одним SQL-запросом: `UNION ALL` участий игрока 1 и игрока 2 → `SUM(CASE …)` по победам, поражениям и ничьим → `JOIN users`.
4. **Ревью и исправления** (ниже).

## Исправлено после ревью

Каждый пункт воспроизведён до исправления и проверен после него на временной PostgreSQL 16 через Flask test client.

| Проблема | Было | Стало | Проверка |
|---|---|---|---|
| Пароли открытым текстом | в `users.password` лежал пароль как есть, сравнение `!=` | `generate_password_hash` при регистрации, `check_password_hash` при входе (Werkzeug, scrypt) | в БД `scrypt:32768:8:1$…`; верный пароль → 200, неверный → 401 |
| Тип JWT не проверялся | refresh-токен (7 дней) принимался как access, access — на `/refresh/*` | `validate_*_token` сверяет claim `type` (`access` / `refresh`) | refresh-токен на `/users/me` → 401; access на `/refresh/access` → 401 |
| Leaderboard: проигрыш компьютеру не считался | `winner_uuid != user_uuid`, а при победе компьютера `winner_uuid` = `NULL` → условие `NULL`, поражение терялось | `winner_uuid IS NULL OR winner_uuid != user_uuid` | 1 победа и 2 поражения компьютеру: было `1`, стало `0.5` |
| Leaderboard: тип `win_ratio` | `NUMERIC` возвращался как `Decimal` и сериализовался строкой `"1.5000000000000000"`, а без поражений — целым `wins` | `CAST(… AS FLOAT)` → всегда число | 3 победы и 2 поражения → `1.5` |
| `datetime.utcnow()` deprecated в Python 3.12 | `DeprecationWarning` при каждом создании игры | `datetime.now(timezone.utc)`, колонка `created_at` → `timestamp with time zone` | предупреждений нет |
| `declarative_base()` — legacy в SQLAlchemy 2.0 | `Base = declarative_base()` | `class Base(DeclarativeBase)` | таблицы создаются, все сценарии проходят |
| Секреты в коде | пароль БД и JWT-секрет в значениях по умолчанию в `config.py`; `app.run(debug=True)` | только из окружения / `.env` (без значений по умолчанию — приложение не стартует без них); debug через `FLASK_DEBUG` | — |
| Мёртвый код | `web/auth_utils.py` (Basic Auth из v1), `database.get_session()` | удалены | граф зависимостей (graphify) и `grep`: ссылок нет |

## Как запустить

Нужны Python 3.12 и PostgreSQL с созданной базой (`createdb tictactoe`).

```bash
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # заполнить DATABASE_URL и JWT_SECRET_KEY
cd src && python main.py                            # http://127.0.0.1:5000
```

Таблицы создаются при старте (`Base.metadata.create_all`). Если база осталась от версии до исправлений, её нужно пересоздать: в старых записях пароли лежат открытым текстом, а `created_at` — без часового пояса.

## Результат

- 15 эндпоинтов. Проверены сценарии: регистрация (в том числе повторный логин), вход, обновление токенов обоих типов, полная игра против компьютера (компьютер выигрывает), игра двух пользователей (ход не в свою очередь → 400, ход после конца игры → 400, победа по строке), история, leaderboard, ошибки валидации (не-UUID, поле 2×3, `limit=0`, запрос без токена → 401).
- Чистая установка из `requirements.txt` и запуск `python main.py` с `.env` проверены отдельно.

## Ограничения и future work

- **Нет blocklist refresh-токенов:** после `/refresh/refresh` старый refresh-токен остаётся валидным до истечения срока. Нужно хранить `jti` отозванных токенов (`@jwt.token_in_blocklist_loader`).
- **Legacy Query API:** репозитории используют `session.query(...)`; стиль SQLAlchemy 2.0 — `session.scalars(select(...))` и `with Session(...)`.
- **Нет миграций:** схема создаётся `create_all` при старте; для изменений схемы нужен Alembic.
- **Направление зависимостей:** граф (graphify) показывает 7 связей `domain → datasource` — сервисы импортируют интерфейсы репозиториев из `datasource`, а `UserRepository` типизирован ORM-классом. По чистой архитектуре интерфейсы должны жить в `domain`.
- Автотестов в репозитории нет — проверки выше выполнялись отдельным скриптом. Запуск на встроенном dev-сервере Flask; для продакшена нужен WSGI-сервер (gunicorn).
