import os

from django.db import models

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



# class Film(models.Model):
#     title = models.CharField(max_length=100)
#     trailer_url = models.URLField()
#     is_2d = models.BooleanField(default=True)
#     is_3d = models.BooleanField(default=False)
#     is_imax = models.BooleanField(default=False)
#
#     def __str__(self):
#         return self.title
#
#
#
# class MovieSession(models.Model):
#     film = models.ForeignKey(Film, on_delete=models.CASCADE)
#     hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
#     price = models.SmallIntegerField()
#     time = models.TimeField()
#     is_3d = models.BooleanField(default=False)
#     is_dbox = models.BooleanField(default=False)
#     is_vip = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f"{self.film} in {self.hall} at {self.time}"
