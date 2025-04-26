# README

Репозиторий Telegram бота.

# Overview

Проект имеет следующие функциональности:
- Телеграм бот в чате.
- Направление вопроса пользователя в чате к API YandexGPT Light и вывод ответа пользователю.
- Сохранение действий пользователя в таблице tgbot.public.t_action (Postgresql).
- Сохранение запросов и ответов в таблице tgbot.public.t_query (Postgresql).

Также для проекта сделан:
- Дашборд в Yandex Data Lense.

# Install

Запустить все:

```shell
docker compose up -d
```
