# 🎾 PadelHub — Платформа для турниров по падел-теннису

Веб-платформа для организации соревнований по падел-теннису. Аналог tennis-united.ru.  
**Стек:** Flask (REST API) + React (Vite) + PostgreSQL + Docker Compose.

---

## 🚀 Быстрый старт

### Требования
- [Docker](https://docs.docker.com/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/)
- Порты **5000** и **5173** должны быть свободны

### Запуск

```bash
git clone <ваш-репозиторий>
cd tennis_platform

docker compose up --build
```

После запуска:
- **Фронтенд:** http://localhost:5173
- **API:** http://localhost:5000/api

> Первый старт занимает 2–4 минуты — устанавливаются зависимости и накатывается БД.

---

## 🔐 Данные для входа (по умолчанию)

| Роль          | Email                  | Пароль    |
|---------------|------------------------|-----------|
| Администратор | admin@padelhub.ru      | admin123  |

---

## 👤 Создание суперпользователя вручную

Вариант 1 — через скрипт после запуска контейнеров:

```bash
docker compose exec web python make_superuser.py user@example.com
```

Вариант 2 — через SQL:

```bash
docker compose exec db psql -U tennis_user -d tennis_db -c \
  "UPDATE users SET is_superuser = TRUE WHERE email = 'user@example.com';"
```

Вариант 3 — в панели администратора:  
Войдите как admin → «Управление» → кнопка «Сделать admin» рядом с нужным пользователем.

---

## 📥 Импорт рейтинга из Excel

1. Войдите как администратор
2. Перейдите на страницу **Рейтинг**
3. Нажмите кнопку **↑ Импорт из Excel**
4. Загрузите `.xlsx`-файл

Поддерживаемые заголовки колонок (регистр не важен):

| Данные         | Варианты названий колонки             |
|----------------|---------------------------------------|
| ФИО            | ФИО, Имя, Name                        |
| Место          | Место, Place, Rank                    |
| Город          | Город, City                           |
| Уровень        | Уровень, Level                        |
| Очки           | Очки, Баллы, Points                   |
| Турниров       | Турниры, Tournaments                  |
| Пол            | Пол, Gender — значения: М/Ж, male/female |

> ⚠️ При импорте текущий рейтинг **заменяется** новым.

---

## 🏗️ Структура проекта

```
tennis_platform/
├── backend/               # Flask REST API
│   ├── app.py             # Все маршруты /api/*
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              # React + Vite
│   ├── src/
│   │   ├── pages/         # Landing, Login, Register, Dashboard, Profile,
│   │   │                  # Tournaments, TournamentDetail, AddTournament,
│   │   │                  # Rating, AdminUsers
│   │   ├── components/    # Layout (navbar)
│   │   ├── context/       # AuthContext (сессия пользователя)
│   │   └── api/           # axios client
│   ├── vite.config.js     # proxy /api → backend:5000
│   └── Dockerfile
├── scripts/
│   └── init.sql           # Схема БД + seed-данные
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Функциональность

### Обычный пользователь
- Регистрация / вход по email + пароль
- Личный кабинет: ФИО, уровень, дата рождения, город, телефон
- Список всех турниров с фильтрами по статусу и типу
- Страница турнира: описание, участники, группы, сетка плей-офф
- Рейтинг с поиском по имени и фильтрами по полу / уровню

### Администратор (суперпользователь)
- Всё вышеперечисленное +
- Создание турниров (название, категория, тип, описание, даты, место)
- Автоматический расчёт групп (например 12 пар → 4 группы × 3 пары)
- Задание размера сетки плей-офф (4 / 8 / 16 / 32)
- Добавление пар в турнир с назначением группы
- Смена статуса турнира (Скоро / Идёт / Завершён)
- Импорт рейтинга из Excel
- Управление пользователями (выдача / снятие прав admin)

### Типы турниров
- Мужной парный (`men_doubles`)
- Женский парный (`women_doubles`)
- Микст (`mixed`)
- Про-Ам (`proam`)

---

## 🛠️ Разработка (без Docker)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://tennis_user:tennis_pass@localhost:5432/tennis_db
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
# Поменяйте в vite.config.js target на 'http://localhost:5000'
npm run dev
```

---

## 🔧 Переменные окружения (backend)

| Переменная     | По умолчанию                                              | Описание           |
|----------------|-----------------------------------------------------------|--------------------|
| `DATABASE_URL` | `postgresql://tennis_user:tennis_pass@db:5432/tennis_db`  | Строка подключения |
| `SECRET_KEY`   | `super-secret-tennis-key-change-in-production`            | Ключ сессии Flask  |

> В production обязательно смените `SECRET_KEY` на случайную строку.

---

## 🗄️ Основные таблицы БД

| Таблица              | Описание                          |
|----------------------|-----------------------------------|
| `users`              | Аккаунты, пароли, роли            |
| `profiles`           | ФИО, уровень, дата рождения       |
| `tournaments`        | Турниры со всеми параметрами      |
| `tournament_pairs`   | Пары-участники турниров           |
| `group_matches`      | Матчи группового этапа            |
| `bracket_matches`    | Матчи плей-офф (сетка)           |
| `ratings`            | Рейтинг игроков                   |

---

## 🧹 Остановка и очистка

```bash
# Остановить
docker compose down

# Остановить и удалить данные БД
docker compose down -v
```
