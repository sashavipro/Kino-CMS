import time
from django.core.management.base import BaseCommand
from src.users.models import CustomUser
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = 'Creates a specified number of test users for the mailing list test.'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Indicates the number of users to be created')

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        start_time = time.time()
        self.stdout.write(self.style.NOTICE(f'Начинаем создание {count} тестовых пользователей...'))

        # Находим последний ID, чтобы новые пользователи не пересекались с существующими
        try:
            last_id = CustomUser.objects.latest('id').id
        except CustomUser.DoesNotExist:
            last_id = 0

        created_count = 0
        for i in range(count):
            # Генерируем уникальные данные на основе ID
            user_id = last_id + i + 1
            email = f'testuser_{user_id}@example.com'
            username = f'testuser_{user_id}'

            try:
                # Используем objects.create_user, который правильно хеширует пароль
                CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',  # Простой пароль для всех
                    first_name='Тест',
                    last_name=f'Пользователь_{user_id}'
                )
                created_count += 1
                if created_count % 100 == 0:
                    self.stdout.write(f'Создано {created_count} из {count} пользователей...')

            except IntegrityError as e:
                # Эта ошибка может возникнуть, если username или email уже занят.
                # Мы просто пропустим этого пользователя и сообщим об этом.
                self.stdout.write(
                    self.style.WARNING(f"Не удалось создать пользователя {username} (возможно, уже существует): {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Неизвестная ошибка при создании пользователя {username}: {e}"))

        end_time = time.time()
        duration = end_time - start_time

        self.stdout.write(
            self.style.SUCCESS(f'Готово! Успешно создано {created_count} пользователей за {duration:.2f} секунд.'))