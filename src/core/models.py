from django.core.validators import MinLengthValidator
from django.db import models
from src.core.untils.my_validator import ImageValidatorMixin, UrlValidatorMixin, SeoValidator
from django.urls import reverse
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


class Gallery(models.Model):  # Model Gallery
    name_gallery = models.CharField(validators=[MinLengthValidator(1)], max_length=300, help_text='Input name Gallery')

    def __str__(self):
        return f'{self.name_gallery}'

    class Meta:
        verbose_name = 'gallery'
        verbose_name_plural = 'gallerys'


class Image(models.Model, ImageValidatorMixin):  # Model Image
    gallery = models.ManyToManyField(Gallery, through='GalleryImage', help_text='Select Gallery')
    image = models.ImageField(blank=True, null=True, upload_to='static/images/',
                              help_text='Upload an image. Supported formats: JPEG, PNG')

    def __str__(self):
        return f'{self.image.name}'

    def clean(self):
        super().clean()
        self.validate_file_extension(self.image)
        self.validate_file_size(self.image)

    class Meta:
        verbose_name = 'image'
        verbose_name_plural = 'images'


class GalleryImage(models.Model):  # Connection ManyToMany between Gallery and Image
    gallery = models.ForeignKey(Gallery, on_delete=models.CASCADE)
    images = models.ForeignKey(Image, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.gallery} {self.images}'

    class Meta:
        verbose_name = 'gallery_image'
        verbose_name_plural = 'gallery_images'
