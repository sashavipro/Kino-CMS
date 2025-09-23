import random
from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from src.cinema.models import Film, Hall, MovieSession


class Command(BaseCommand):
    help = 'Generates a random movie schedule for the next 7 days.'

    def add_arguments(self, parser):
        # Добавляем опциональный флаг --clear, чтобы сначала очистить старое расписание
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all future movie sessions before generating new ones.',
        )

    @transaction.atomic  # Выполняем все действия в одной транзакции для скорости
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Начинаем генерацию расписания...'))

        # --- Очистка (если нужно) ---
        if kwargs['clear']:
            today = date.today()
            # Удаляем все сеансы, начиная с сегодняшнего дня
            sessions_to_delete = MovieSession.objects.filter(date__gte=today)
            count = sessions_to_delete.count()
            sessions_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Успешно удалено {count} будущих сеансов.'))

        # --- Сбор данных для генерации ---
        # Берем все фильмы, которые сейчас в прокате
        films = list(Film.objects.filter(status=Film.Status.NOW_SHOWING))
        # Берем все залы
        halls = list(Hall.objects.all())

        if not films:
            self.stdout.write(self.style.ERROR(
                'Ошибка: В базе нет фильмов со статусом "Сейчас в кино". Нечего добавлять в расписание.'))
            return
        if not halls:
            self.stdout.write(self.style.ERROR('Ошибка: В базе нет ни одного зала. Негде показывать фильмы.'))
            return

        # Возможные варианты времени начала сеансов
        possible_times = [
            time(10, 0), time(10, 10), time(10, 40),
            time(12, 30), time(13, 0), time(13, 20),
            time(15, 0), time(15, 45),
            time(17, 30), time(18, 10),
            time(19, 0), time(19, 50),
            time(21, 20), time(22, 0),
        ]

        # Возможные варианты цен
        possible_prices = [120, 150, 180, 200, 220, 250]

        # --- Основной цикл генерации ---
        today = date.today()
        sessions_created = 0

        # Генерируем расписание на 7 дней вперед
        for i in range(7):
            current_date = today + timedelta(days=i)

            # Для каждого зала в этот день создадим от 3 до 5 сеансов
            for hall in halls:
                # Перемешиваем фильмы и время, чтобы расписание было разным
                random.shuffle(films)
                random.shuffle(possible_times)

                # Создаем рандомное количество сеансов (от 3 до 5)
                for j in range(random.randint(3, 5)):
                    # Проверяем, что у нас еще есть фильмы и время для назначения
                    if j < len(films) and j < len(possible_times):
                        film_to_show = films[j]
                        show_time = possible_times[j]

                        # Создаем объект сеанса, но пока не сохраняем
                        session = MovieSession(
                            film=film_to_show,
                            hall=hall,
                            date=current_date,
                            time=show_time,
                            price=random.choice(possible_prices),
                            is_3d=film_to_show.is_3d and random.choice([True, False]),
                            # Если фильм поддерживает 3D, сеанс может быть 3D, а может и не быть
                            is_vip=random.choice([True, False, False]),  # Делаем VIP-сеансы более редкими
                        )
                        # Используем get_or_create, чтобы не создавать дубликаты
                        # (на случай, если мы запустим команду без --clear)
                        _, created = MovieSession.objects.get_or_create(
                            hall=session.hall, date=session.date, time=session.time,
                            defaults={
                                'film': session.film,
                                'price': session.price,
                                'is_3d': session.is_3d,
                                'is_vip': session.is_vip,
                            }
                        )
                        if created:
                            sessions_created += 1

        self.stdout.write(self.style.SUCCESS(f'Генерация завершена! Создано {sessions_created} новых сеансов.'))