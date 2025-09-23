import os

from django.db import models
from django.urls import reverse

from Config import settings
from src.core.models import SeoBlock, Gallery


# # CINEMA ----------------------------------------------------------------------------------------
class Cinema(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    logo = models.ImageField(upload_to="cinemas/logos/", blank=True, null=True)
    main_image = models.ImageField(upload_to="cinemas/banners/", blank=True, null=True)
    gallery = models.OneToOneField(Gallery, on_delete=models.SET_NULL, blank=True, null=True)
    seo_block = models.ForeignKey(SeoBlock, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # Перед удалением записи из базы, удаляем связанные файлы

        # 1. Удаляем логотип, если он есть
        if self.logo:
            if os.path.isfile(self.logo.path):
                os.remove(self.logo.path)

        # 2. Удаляем главный баннер, если он есть
        if self.main_image:
            if os.path.isfile(self.main_image.path):
                os.remove(self.main_image.path)

        # 3. Если есть галерея, можно удалить и ее (более сложная логика)
        # if self.gallery:
        #     self.gallery.delete() # Это каскадно удалит и все картинки в галерее

        # 4. Вызываем оригинальный метод delete(), который удалит запись из базы
        super().delete(*args, **kwargs)


class Hall(models.Model):
    cinema = models.ForeignKey(Cinema,on_delete=models.CASCADE,related_name='halls')
    number_hall = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    scheme_image = models.ImageField(upload_to="halls/schemes/")
    banner_image = models.ImageField(upload_to="halls/banners/", blank=True, null=True)
    gallery = models.OneToOneField(Gallery, on_delete=models.SET_NULL, blank=True, null=True)
    seo_block = models.ForeignKey(SeoBlock, on_delete=models.SET_NULL, null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Показываем, к какому кинотеатру относится зал, для удобства в админке
        return f"Зал '{self.number_hall}' в '{self.cinema.name}'"

    def delete(self, *args, **kwargs):
        if self.scheme_image and os.path.isfile(self.scheme_image.path):
            os.remove(self.scheme_image.path)
        if self.banner_image and os.path.isfile(self.banner_image.path):
            os.remove(self.banner_image.path)
        super().delete(*args, **kwargs)


class Film(models.Model):
    # Добавляем выбор статуса
    class Status(models.TextChoices):
        NOW_SHOWING = 'now_showing', 'Сейчас в кино'
        COMING_SOON = 'coming_soon', 'Скоро'

    def get_absolute_url(self):
        # Возвращает URL для страницы этого конкретного фильма
        return reverse('core:film_page', args=[str(self.id)])

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    main_image = models.ImageField(upload_to="film/poster/", blank=True, null=True)
    gallery = models.OneToOneField(Gallery, on_delete=models.SET_NULL, blank=True, null=True)
    trailer_url = models.URLField(blank=True)

    # Добавляем новые поля
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
    )

    is_2d = models.BooleanField(default=True)
    is_3d = models.BooleanField(default=False)
    is_imax = models.BooleanField(default=False)

    seo_block = models.ForeignKey(SeoBlock, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title


class MovieSession(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='sessions')
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name='sessions')

    date = models.DateField(verbose_name="Дата сеанса")
    time = models.TimeField(verbose_name="Время начала")

    price = models.PositiveSmallIntegerField(verbose_name="Цена билета")
    is_3d = models.BooleanField(default=False)
    is_dbox = models.BooleanField(default=False)
    is_vip = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.film.title} в '{self.hall.number_hall}' - {self.date.strftime('%d.%m.%Y')} {self.time.strftime('%H:%M')}"

    class Meta:
        ordering = ['date', 'time']  # Сортируем сеансы по дате и времени


# Модель для хранения билетов
class Ticket(models.Model):
    class Status(models.TextChoices):
        BOOKED = 'booked', 'Забронирован'
        PAID = 'paid', 'Оплачен'

    session = models.ForeignKey(MovieSession, on_delete=models.CASCADE, related_name='tickets')
    price = models.PositiveSmallIntegerField(verbose_name="Цена")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cinema_tickets')
    row = models.PositiveSmallIntegerField(verbose_name="Ряд")
    seat = models.PositiveSmallIntegerField(verbose_name="Место")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.BOOKED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'row', 'seat')
        verbose_name = "Билет"
        verbose_name_plural = "Билеты"

    def __str__(self):
        return f"Билет на {self.session} для {self.user.email} (Ряд {self.row}, Место {self.seat})"