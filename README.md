# Telegram + СиМед WebApp запись

## Что внутри

- `bot.py` — Telegram-бот с кнопкой «Записаться к врачу».
- `backend.py` — FastAPI backend-прокси к API СиМед.
- `webapp/index.html` — Telegram WebApp форма записи.
- `.env.example` — пример настроек.

## Важное про reCAPTCHA

Для `/recordDirect` нужен reCAPTCHA site key, который принимает СиМед/виджет. Если использовать ключ, созданный для `localhost` или своего домена, СиМед может возвращать `-1`.

Нужно одно из двух:

1. Использовать site key из существующего виджета policlinica24.ru, если он подходит для вашего WebApp-домена.
2. Попросить Симплекс/СиМед добавить домен вашего WebApp в настройки reCAPTCHA/виджета.

## Локальный запуск

1. Создай `.env` на основе `.env.example`.
2. Установи зависимости:

```bash
pip install -r requirements.txt
```

3. Запусти backend:

```bash
uvicorn backend:app --reload
```

Backend будет на:

```text
http://127.0.0.1:8000
```

4. Для локальной проверки WebApp открой `webapp/index.html`, но лучше через локальный сервер:

```bash
cd webapp
python -m http.server 5500
```

Открыть:

```text
http://127.0.0.1:5500/index.html
```

Перед локальной проверкой в `index.html` замени:

```js
const BACKEND_URL = "__BACKEND_URL__";
let recaptchaSiteKey = "__RECAPTCHA_SITE_KEY__";
```

на реальные значения, например:

```js
const BACKEND_URL = "http://127.0.0.1:8000";
let recaptchaSiteKey = "ВАШ_SITE_KEY";
```

5. Запусти бота:

```bash
python bot.py
```

## Деплой

### Backend

Разместить `backend.py`, `requirements.txt`, `.env` на Railway/Render.

Start command:

```bash
uvicorn backend:app --host 0.0.0.0 --port $PORT
```

### WebApp

Разместить папку `webapp` на Vercel/Netlify.

В `index.html` указать:

```js
const BACKEND_URL = "https://your-backend.up.railway.app";
let recaptchaSiteKey = "ВАШ_SITE_KEY";
```

### Bot

В `.env` указать:

```env
BOT_TOKEN=...
WEBAPP_URL=https://your-webapp.vercel.app
```

Потом запустить:

```bash
python bot.py
```

## Цепочка записи

1. WebApp получает специальности: `/specializations`
2. Пользователь выбирает специальность.
3. WebApp получает врачей: `/doctors?spec_id=...`
4. Пользователь выбирает врача.
5. WebApp получает слоты: `/worker-cells`
6. Пользователь выбирает дату/время.
7. Пользователь вводит имя/телефон и проходит капчу.
8. WebApp вызывает `/record-direct`.
9. Backend вызывает `recordDirect` в СиМед и получает `request_key`.
10. WebApp вызывает `SendMedOrgSMS/20` и `SendRand/{request_key}` при необходимости.
11. Пользователь вводит код.
12. WebApp вызывает `/confirm`.
13. При успехе WebApp отправляет данные обратно в Telegram-бот через `Telegram.WebApp.sendData()`.
14. Бот пишет: «Вы записаны к врачу...».
