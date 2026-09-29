# Lab 1 - REST API Service

## Опис сервісу
Цей проєкт є базовим REST API для управління сутностями (Items), створеним у рамках лабораторної роботи №1. Він підтримує стандартні CRUD-операції (створення, читання, оновлення та видалення об'єктів).

## Технології
* **Мова програмування:** Python
* **Фреймворк:** FastAPI

## Запуск тестів
Для перевірки працездатності сервісу та виконання unit-тестів використовуйте команду:
`pytest`

## Збирання та запуск Docker-контейнера
1. Зібрати Docker-образ:
`docker build -t lab1-api .`

2. Запустити контейнер:
`docker run -d -p 8000:8000 lab1-api`

Після запуску документація Swagger UI буде доступна у браузері за адресою: `http://localhost:8000/docs`

## Azure DevOps Pipeline

Файл `azure-pipelines.yml` описує CI-процес для гілки `main`:

1. В Azure DevOps створіть проєкт і підключіть цей GitHub-репозиторій у розділі **Pipelines**.
2. У **Project settings > Service connections** створіть підключення типу **Docker Registry**, виберіть **Docker Hub** і назвіть його `dockerHubConnection`.
3. У `azure-pipelines.yml` замініть `YOUR_DOCKERHUB_USERNAME` на ім'я користувача Docker Hub.
4. Створіть pipeline з наявного YAML-файлу та дозвольте pipeline використовувати Docker Hub service connection.

Після push у `main` pipeline встановлює залежності, запускає unit-тести, збирає Docker-образ і публікує його в Docker Hub з тегом `latest`.