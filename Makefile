CELERY_APP = Config

.PHONY: help celery-worker create-users create-schedule

help:
		@echo "Доступные команды: "
		@echo "		make create-schedule - Очистить и сгенерировать новое расписание на неделю"
		@echo "		make celery-worker - Запустить только Celery worker с автоперезагрузкой"
		@echo "		make create-users - Создать 500 тестовых пользователей"



celery-worker:
				@echo "Запуск Celery worker..."
				@celery -A $(CELERY_APP) worker -l info


# Создание 1000 тестовых пользователей
create-users:
				@echo "Создание 1000 тестовых пользователей..."
				@python manage.py create_test_users 500


# Создание расписания
create-schedule:
					@echo "Очистка старого и генерация нового расписания..."
					@python manage.py generate_schedule --clear

