from django.core.validators import MinLengthValidator
from django.db import models
from src.core.untils.my_validator import ImageValidatorMixin, UrlValidatorMixin, SeoValidator
from django.utils.text import slugify


class SeoBlock(models.Model):
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="URL (slug)",
        help_text="Уникальный slug для SEO блока (например: 'about-us', 'contacts')"
    )
    title_seo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="SEO Title"
    )
    keywords_seo = models.TextField(
        blank=True,
        null=True,
        verbose_name="SEO Keywords"
    )
    description_seo = models.TextField(
        blank=True,
        null=True,
        verbose_name="SEO Description"
    )

    def save(self, *args, **kwargs):
        # Если slug введён вручную — приводим его к правильному виду
        if self.slug:
            self.slug = slugify(self.slug)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.slug


class Gallery(models.Model):
    name_gallery = models.CharField(max_length=300, help_text='Input name Gallery')

    def __str__(self):
        return self.name_gallery

    class Meta:
        verbose_name = 'gallery'
        verbose_name_plural = 'galleries'


class Image(models.Model, ImageValidatorMixin):
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='gallery_images/', help_text='Upload an image.', null=True,blank=True)

    def __str__(self):
        if self.image:
            return f'Image {self.id} for {self.gallery.name_gallery}'
        return f'Empty slot {self.id} for {self.gallery.name_gallery}'

    def clean(self):
        super().clean()
        self.validate_file_extension(self.image)
        self.validate_file_size(self.image)

    class Meta:
        verbose_name = 'image'
        verbose_name_plural = 'images'


# Модель для хранения HTML-шаблонов рассылки
class MailingTemplate(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название шаблона")
    file = models.FileField(upload_to='mailing_templates/', verbose_name="HTML файл")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Шаблон рассылки"
        verbose_name_plural = "Шаблоны рассылки"
        # Сортируем так, чтобы новые шаблоны были сверху
        ordering = ['-created_at']


# Новая модель для отслеживания статуса кампании рассылки
class MailingCampaign(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'В ожидании'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершена'
        FAILED = 'failed', 'Ошибка'

    # Мы больше не храним ID шаблонов, а связываем с кампанией
    templates = models.ManyToManyField(MailingTemplate, verbose_name="Шаблоны")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Статус")
    task_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID задачи Celery")

    send_to_all = models.BooleanField(default=True, verbose_name="Отправить всем")
    # JSONField идеально подходит для хранения списка ID
    recipients = models.JSONField(null=True, blank=True, verbose_name="Получатели (ID)")

    total_recipients = models.PositiveIntegerField(default=0, verbose_name="Всего получателей")
    sent_count = models.PositiveIntegerField(default=0, verbose_name="Отправлено писем")

    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Время старта")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Время завершения")

    def __str__(self):
        # Получаем имена шаблонов для красивого отображения
        template_names = ", ".join([t.name for t in self.templates.all()])
        return f"Рассылка '{template_names}' от {self.started_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Кампания рассылки"
        verbose_name_plural = "Кампании рассылки"
        ordering = ['-started_at']