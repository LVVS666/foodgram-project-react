![example workflow](https://github.com/lvvs666/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

# Учебный проект  FOODGRAM
http://158.160.11.226/redoc/

## Описание:
 «Продуктовый помощник». На этом сервисе пользователи смогут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

## Пример заполнения .env файла:
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=postgres # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД 


## Команды для запуска контейнеров и заполнения БД:
docker-compose up  # Создание контейнеров

docker-compose exec foodgram_backend python manage.py makemigrations users
docker-compose exec foodgram_backend python manage.py makemigrations reviews
docker-compose exec foodgram_backend python manage.py migrate #Миграции

docker-compose exec foodgram_backend python manage.py createsuperuser #Создание админки
docker-compose exec foodgram_backend python manage.py collectstatic --no-input  #Загрузка статики

## Документация
После запуска проекта документация будет доступна по адресу: 
(http://158.160.11.226/redoc/)

