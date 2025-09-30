# 🚀 Инструкция по загрузке проекта на GitHub

## Шаг 1: Создание репозитория на GitHub

1. Откройте https://github.com
2. Войдите в свой аккаунт
3. Нажмите на "+" в правом верхнем углу → "New repository"
4. Заполните форму:
   - **Repository name:** `mydoc-loyalty`
   - **Description:** Микросервис "Моя ❤ скидка" - программа лояльности для медицинской клиники
   - **Visibility:** Private (рекомендуется) или Public
   - **НЕ СОЗДАВАЙТЕ** README, .gitignore и license (они уже есть в проекте)
5. Нажмите "Create repository"

## Шаг 2: Связывание локального репозитория с GitHub

После создания репозитория GitHub покажет инструкции. Выполните следующие команды:

```bash
cd /tmp/mydoc-loyalty

# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/mydoc-loyalty.git

# Или используйте SSH (если настроен SSH ключ)
git remote add origin git@github.com:YOUR_USERNAME/mydoc-loyalty.git

# Переименуйте ветку в main (если хотите использовать main вместо master)
git branch -M main

# Загрузите код на GitHub
git push -u origin main
```

## Шаг 3: Проверка

1. Обновите страницу репозитория на GitHub
2. Вы должны увидеть все файлы проекта
3. Проверьте что README.md отображается корректно

## 📋 Структура проекта в репозитории

```
mydoc-loyalty/
├── backend/              # FastAPI бэкенд
├── frontend/             # React фронтенд (личный кабинет)
├── admin/                # React админ-панель
├── nginx/                # Nginx конфигурация
├── docker-compose.yml    # Docker Compose конфигурация
├── .env.example          # Пример переменных окружения
├── README.md             # Основная документация
├── START_HERE.md         # С чего начать
├── API_DOCUMENTATION.md  # Документация API
├── DEPLOYMENT.md         # Инструкции по деплою
└── .gitignore            # Игнорируемые файлы
```

## 🔐 Важно: Безопасность

✅ Файл `.gitignore` настроен так, чтобы **НЕ загружать**:
- `.env` файлы с секретами
- SSL сертификаты
- Логи
- Кэш и временные файлы
- `node_modules/` и `__pycache__/`

⚠️ **НИКОГДА не коммитьте:**
- Пароли
- API ключи
- JWT секреты
- Приватные ключи SSL

## 📝 Дальнейшая работа

### Создание новой ветки для разработки:

```bash
git checkout -b feature/new-feature
# Внесите изменения
git add .
git commit -m "Описание изменений"
git push origin feature/new-feature
```

### Обновление main ветки:

```bash
git checkout main
git pull origin main
# Внесите изменения
git add .
git commit -m "Описание изменений"
git push origin main
```

### Создание тегов для релизов:

```bash
git tag -a v1.0.0 -m "Релиз v1.0.0"
git push origin v1.0.0
```

## 🌟 GitHub Actions (опционально)

Вы можете настроить автоматическое тестирование и деплой через GitHub Actions.

Создайте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/mydoc-loyalty
            git pull origin main
            docker-compose down
            docker-compose up -d --build
```

## 📊 GitHub настройки для проекта

### Рекомендуемые настройки:

1. **Settings → Branches**
   - Защитите `main` ветку
   - Требуйте pull request перед мержем
   - Требуйте code review

2. **Settings → Secrets**
   - Добавьте секреты для CI/CD:
     - `SERVER_HOST` - IP сервера
     - `SERVER_USER` - SSH пользователь
     - `SSH_PRIVATE_KEY` - Приватный SSH ключ

3. **Settings → Pages** (если нужен GitHub Pages для документации)
   - Выберите ветку для деплоя документации

## 🔗 Полезные ссылки

- [GitHub Documentation](https://docs.github.com)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [GitHub Actions](https://docs.github.com/en/actions)

---

**Готово!** Ваш проект теперь на GitHub! 🎉
