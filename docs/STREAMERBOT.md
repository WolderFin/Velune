# Streamer.bot + Velune

Velune отдаёт готовый текст для чата по локальному адресу:

```text
http://127.0.0.1:8765/api/streamerbot
```

Если в Velune выбран конкретный источник, используй URL из блока **Команда Streamer.bot** — параметр `source` уже будет добавлен автоматически.

## Настройка команды

1. Запусти Velune и музыку.
2. В Streamer.bot создай новый **Action**, например `Velune — текущий трек`.
3. Добавь к Action триггер **Commands → Command Triggered** и создай команду `!song` (или другую выбранную в Velune).
4. Добавь sub-action **Core → Network → Fetch URL**:
   - **URL:** скопируй из Velune;
   - **Variable Name:** `veluneSong`;
   - **Parse result as JSON:** выключено.
5. Добавь sub-action отправки сообщения для нужной площадки:
   - Twitch: **Twitch → Chat → Send Message to Channel**;
   - YouTube: **YouTube → Chat → Send Message to Channel**;
   - Kick: **Kick → Chat → Send Message to Channel**.
6. В поле сообщения укажи `%veluneSong%`.

При активной музыке ответ будет выглядеть так:

```text
Сейчас играет: Исполнитель — Название трека
```

Если трек не найден:

```text
Сейчас ничего не играет.
```

## JSON для расширенных сценариев

Для собственного Action можно добавить `format=json`:

```text
http://127.0.0.1:8765/api/streamerbot?format=json
```

Ответ содержит `message`, `title`, `artist`, `album`, `playing`, `source` и другие поля текущего состояния.

Интеграция работает только через локальный адрес `127.0.0.1`: данные о треке не отправляются в интернет. Velune должна оставаться запущенной или свёрнутой в трей.
