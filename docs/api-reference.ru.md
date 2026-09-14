# Справочник API: REST & MCP

Полная спецификация всех REST-эндпоинтов и инструментов протокола Model Context Protocol (MCP) JSON-RPC, предоставляемых сервисом ContextSync.

---

## 1. Аутентификация

Все REST-эндпоинты и SSE-потоки требуют проверки Bearer-токена:
- **Заголовок HTTP**: `Authorization: Bearer <API_TOKEN>`
- **Параметр URL**: `?token=<API_TOKEN>`

Токен по умолчанию для локальной разработки: `ctx_secret_token_7f9a8b1c4e2d3f5a`

---

## 2. Основные REST-эндпоинты базы контекста

### 2.1 Проверка работоспособности (Health Check)
- **Эндпоинт**: `GET /health`
- **Аутентификация**: Не требуется
- **Ответ**:
  ```json
  {
    "status": "healthy",
    "service": "remote-context-store",
    "version": "0.1.0"
  }
  ```

### 2.2 Сохранение контекста
- **Эндпоинт**: `POST /api/v1/contexts`
- **Тело запроса**:
  ```json
  {
    "title": "Архитектура портов сервера",
    "content": "Бэкенд запущен на порту 8200, база Postgres на порту 5445 во избежание коллизий.",
    "tags": ["docker", "devops", "ports"],
    "project": "context_sync",
    "metadata": {"author": "Antigravity"}
  }
  ```
- **Ответ (HTTP 200)**:
  ```json
  {
    "id": "c7a8b3d2-4f1e-4b9a-8c5d-6e2f1a3b4c5d",
    "title": "Архитектура портов сервера",
    "action": "created"
  }
  ```

### 2.3 Семантический векторный поиск
- **Эндпоинт**: `POST /api/v1/contexts/search`
- **Тело запроса**:
  ```json
  {
    "query": "какие порты используются для базы данных",
    "project": "context_sync",
    "limit": 5,
    "min_score": 0.25
  }
  ```
- **Ответ (HTTP 200)**:
  ```json
  {
    "query": "какие порты используются для базы данных",
    "count": 1,
    "results": [
      {
        "id": "c7a8b3d2-4f1e-4b9a-8c5d-6e2f1a3b4c5d",
        "title": "Архитектура портов сервера",
        "content": "Бэкенд запущен на порту 8200, база Postgres на порту 5445...",
        "score": 0.892,
        "tags": ["docker", "devops", "ports"]
      }
    ]
  }
  ```

### 2.4 Мониторинг флота агентов (Fleet Tracker)
- **Эндпоинт**: `GET /api/v1/fleet`
- **Ответ (HTTP 200)**: Возвращает список всех активных клиентов MCP, их IP-адреса, User-Agent и время последней активности.

---

## 3. Разрешение конфликтов на уровне фактов (FLCR REST API)

Движок FLCR управляет атомарными фактами (`Сущность -> Параметр -> Значение`) с поддержкой версионирования, аудита и политик разрешения конфликтов (`lww` и `authority`).

### 3.1 Список утвержденных фактов проекта (Truth-Table)
- **Эндпоинт**: `GET /api/v1/facts`
- **Параметры запроса**:
  - `project` (str, опционально, по умолчанию `"global"`)
  - `entity` (str, опционально): фильтрация по сущности (например, `"backend"`, `"database"`)
- **Ответ (HTTP 200)**:
  ```json
  {
    "project": "context_sync",
    "count": 2,
    "facts": [
      {
        "id": "7f8b9c1d-2e3a-4b5c-6d7e-8f9a0b1c2d3e",
        "project": "context_sync",
        "entity": "backend",
        "attribute": "port",
        "value": 8200,
        "source_agent": "Antigravity",
        "confidence": 1.0,
        "version": 2,
        "is_active": true,
        "superseded_by": null,
        "conflict_flag": false,
        "created_at": "2026-09-13T17:40:00Z",
        "updated_at": "2026-09-13T17:45:00Z"
      }
    ]
  }
  ```

### 3.2 Запись или обновление факта
- **Эндпоинт**: `POST /api/v1/facts`
- **Тело запроса**:
  ```json
  {
    "entity": "database",
    "attribute": "port",
    "value": 5445,
    "project": "context_sync",
    "source_agent": "Antigravity",
    "confidence": 1.0,
    "policy": "lww"
  }
  ```
- **Поддерживаемые политики**:
  - `lww` (Last-Write-Wins): автоматически версионирует факт (`v1 -> v2`) и деактивирует предыдущий (`is_active = false`, `superseded_by`).
  - `authority`: проверяет приоритет автора. Изменение от агента с более низким весом отклоняется, и выставляется `conflict_flag: true`.

### 3.3 Получение активного факта
- **Эндпоинт**: `GET /api/v1/facts/{entity}/{attribute}`
- **Параметры**: `project` (str, по умолчанию `"global"`)
- **Ответ (HTTP 200)**: Актуальный объект `ProjectFact`.

### 3.4 История версий и аудит факта
- **Эндпоинт**: `GET /api/v1/facts/{entity}/{attribute}/history`
- **Параметры**: `project` (str, по умолчанию `"global"`)
- **Ответ (HTTP 200)**: Полный хронологический список всех версий параметра, авторов и отметок времени.

### 3.5 Ручное разрешение спорного конфликта
- **Эндпоинт**: `POST /api/v1/facts/resolve`
- **Тело запроса**:
  ```json
  {
    "fact_id": "9a8b7c6d-5e4f-3a2b-1c0d-e9f8a7b6c5d4",
    "chosen_value": 8200,
    "resolver_agent": "user"
  }
  ```
- **Ответ (HTTP 200)**: Снимает флаг конфликта и фиксирует выбранное значение.

---

## 4. Репликация навыков (Skills API)

Централизованный реестр навыков (`SKILL.md` + скрипты + шаблоны) для обмена между Cursor, Antigravity, Claude Code, Codex и Windsurf.

### 4.1 Список доступных навыков
- **Эндпоинт**: `GET /api/v1/skills`
- **Параметры**: `tag` (str, опц), `search` (str, опц), `limit` (int, опц)

### 4.2 Публикация навыка
- **Эндпоинт**: `POST /api/v1/skills`
- **Тело запроса**:
  ```json
  {
    "name": "docker-expert",
    "content_md": "---\nname: docker-expert\ndescription: Docker wizardry\n---\n# Instructions...",
    "description": "Docker wizardry",
    "version": "1.0.0",
    "files_bundle": {"scripts/test.py": "print('ok')"},
    "tags": ["docker", "devops"]
  }
  ```

### 4.3 Установка навыка в агент
- **Эндпоинт**: `POST /api/v1/skills/{name}/install`
- **Тело запроса**: `{"target_agent": "cursor"}` (или `"claude"`, `"antigravity"`, `"codex"`, `"all"`)

---

## 5. Центральный реестр MCP-серверов (MCP Fleet Hub)

Единый реестр внешних MCP-серверов с возможностью мгновенного проброса в локальные конфиги агентов.

### 5.1 Список зарегистрированных серверов
- **Эндпоинт**: `GET /api/v1/mcp-registry`

### 5.2 Регистрация сервера
- **Эндпоинт**: `POST /api/v1/mcp-registry`
- **Тело запроса (stdio)**:
  ```json
  {
    "name": "github",
    "transport": "stdio",
    "config": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "..."}
    }
  }
  ```

### 5.3 Развертывание сервера в конфигурации агентов
- **Эндпоинт**: `POST /api/v1/mcp-registry/{name}/install`
- **Тело запроса**: `{"target_agent": "all"}` (или конкретный `app_id`: `"cursor"`, `"claude-desktop"`, `"antigravity"`)

---

## 6. Инструменты протокола MCP JSON-RPC

При подключении через `/sse` или `stdio` ИИ-агентам доступны следующие стандартные инструменты MCP:

### Работа с контекстом и документами
| Имя инструмента | Параметры | Описание |
|---|---|---|
| `context_save` | `title` (str), `content` (str), `tags` (list[str], опц), `project` (str, опц), `metadata` (obj, опц) | Сохраняет фрагмент знаний с вычислением вектора FastEmbed. |
| `context_search` | `query` (str), `project` (str, опц), `tags` (list[str], опц), `limit` (int, опц), `min_score` (float, опц) | Семантический векторный поиск по косинусному расстоянию. |
| `context_get` | `context_id` (str) | Извлечение полного текста по UUID или точному заголовку. |
| `context_list` | `project` (str, опц), `limit` (int, опц) | Список недавних записей с пагинацией. |
| `context_delete` | `context_id` (str) | Удаление устаревшей записи из базы. |

### Разрешение конфликтов фактов (FLCR)
| Имя инструмента | Параметры | Описание |
|---|---|---|
| `fact_set` | `entity` (str), `attribute` (str), `value` (any), `project` (str, опц), `confidence` (float, опц), `policy` (`"lww"` \| `"authority"`, опц) | Атомарно сохраняет или обновляет факт с версионированием и политикой разрешения. |
| `fact_get` | `entity` (str), `attribute` (str), `project` (str, опц) | Возвращает текущее утвержденное значение параметра. |
| `fact_list` | `project` (str, опц), `entity` (str, опц) | Возвращает всю Таблицу Истинных Фактов (Truth-Table) проекта. |
| `fact_history` | `entity` (str), `attribute` (str), `project` (str, опц) | Возвращает полную историю изменений, версий и зафиксированных конфликтов. |

### Репликация навыков флота (Skills)
| Имя инструмента | Параметры | Описание |
|---|---|---|
| `skill_publish` | `name` (str), `content_md` (str), `description` (str, опц), `version` (str, опц), `files_bundle` (obj, опц), `tags` (list, опц) | Публикация или обновление навыка в общем репозитории флота. |
| `skill_list` | `search` (str, опц), `tag` (str, опц) | Каталог и поиск навыков, созданных другими агентами. |
| `skill_get` | `name` (str) | Получение полного содержимого навыка и файлов. |
| `skill_install` | `name` (str), `target_agent` (str, по умолч: `'all'`) | Установка навыка в локальную файловую систему агентов. |

### Реестр MCP-серверов (MCP Hub)
| Имя инструмента | Параметры | Описание |
|---|---|---|
| `mcp_server_publish` | `name` (str), `transport` (`"stdio"` \| `"sse"`), `config` (obj) | Регистрация проверенного MCP-сервера в реестре флота. |
| `mcp_server_list` | `only_active` (bool, по умолч: `true`) | Список доступных внешних серверов. |
| `mcp_server_install` | `name` (str), `target_agent` (str, по умолч: `'all'`) | Авто-инъекция сервера в JSON-конфиги агентов на машине. |

