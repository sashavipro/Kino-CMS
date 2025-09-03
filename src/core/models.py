from django.core.validators import MinLengthValidator
from django.db import models
from src.core.untils.my_validator import ImageValidatorMixin, UrlValidatorMixin, SeoValidator




class SeoBlock(models.Model, UrlValidatorMixin):  # Model SEO
    url_seo = models.URLField(null=True, blank=True, help_text='Input url address SEO')
    title_seo = models.CharField(validators=[MinLengthValidator(1)], max_length=300, help_text='Input title SEO')
    keywords_seo = models.CharField(null=True, blank=True, max_length=400, validators=[SeoValidator.validate_keywords],
                                    help_text='Input keywords SEO')
    description_seo = models.TextField(null=True, blank=True, help_text='Input description SEO')

    def __str__(self):
        return f'{self.title_seo}'

    def clean(self):
        super().clean()
        self.validate_url(self.url_seo)


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
