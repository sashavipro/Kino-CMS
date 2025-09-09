import os

from django.db import models

from src.core.models import SeoBlock, Gallery


# # PAGE ----------------------------------------------------------------------------------------

class MainPage(models.Model):
    phone1 = models.CharField(max_length=11)
    phone2 = models.CharField(max_length=11)
    seo_text = models.TextField()
    seo_block = models.ForeignKey(SeoBlock, on_delete=models.CASCADE, null=True, blank=True)
    status = models.BooleanField(default=True)
    time_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk and MainPage.objects.exists():
            raise ValueError("MainPage может быть только одна. Отредактируйте существующую запись.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Главная страница"



class Contact(models.Model):
    name = models.CharField(max_length=50)
    address = models.TextField()
    coords = models.CharField(max_length=200)  # координаты для гугл карты
    logo = models.ImageField(upload_to="static/image/")
    seo_block = models.ForeignKey(SeoBlock, on_delete=models.CASCADE, null=True, blank=True)
    status = models.BooleanField(default=True)
    time_created = models.DateTimeField(auto_now_add=True)


class OtherPage(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    main_image = models.ImageField(upload_to="static/image/", blank=True, null=True)
    seo_block = models.ForeignKey(SeoBlock, on_delete=models.CASCADE, null=True, blank=True, default="")
    status = models.BooleanField(default=True)
    time_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "другая страница"
        verbose_name_plural = "другие страницы"

    def save(self, *args, **kwargs):
        if self.pk:
            old = OtherPage.objects.filter(pk=self.pk).first()
            if old and old.main_image and old.main_image != self.main_image:
                # Удаляем старый файл, если он заменяется новым
                if os.path.isfile(old.main_image.path):
                    os.remove(old.main_image.path)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Удаляем файл при удалении объекта
        if self.main_image and os.path.isfile(self.main_image.path):
            os.remove(self.main_image.path)
        super().delete(*args, **kwargs)

class OtherPageSlide(models.Model):
    page = models.ForeignKey(OtherPage, on_delete=models.CASCADE, related_name="slides")
    image = models.ImageField(upload_to="static/image/slides/")

    class Meta:
        verbose_name = "Слайд для другой страницы"
        verbose_name_plural = "Слайды для других страниц"


class NewsPromotionPage(models.Model):
    is_promotion = models.BooleanField(
        default=False,  # По умолчанию все новые записи будут новостями
        verbose_name="Это акция?",
        help_text="Отметьте, если это акция. Иначе запись будет считаться новостью."
    )
    status = models.BooleanField(default=True)
    name = models.CharField(max_length=50, unique=True)
    time_created = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    main_image = models.ImageField(upload_to="static/image/", blank=True, null=True)
    gallery_banner = models.OneToOneField(Gallery, on_delete=models.CASCADE, blank=True, null=True, help_text='Select Gallery to Banner')
    url_movie = models.URLField(max_length=300, null=True, blank=True, help_text='Input url movie')
    seo_block = models.ForeignKey(SeoBlock, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name