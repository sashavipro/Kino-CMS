from django.db import models
from django.core.validators import MinLengthValidator
from src.core.untils.my_validator import UrlValidatorMixin, CounterValidatorMixin
from src.core.models import Image


# BANNER ----------------------------------------------------------------------------------------
class Banners(models.Model, UrlValidatorMixin, CounterValidatorMixin):  # Abstract Model Banners
    name_banner = models.CharField(validators=[MinLengthValidator(1)], max_length=50, help_text='Input name Banner')
    status_banner = models.BooleanField(default=True, help_text='Select status Banner')

    class Meta:
        verbose_name = 'banner'
        verbose_name_plural = 'banners'


class HomeBanner(Banners):
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Изображение")

    url_banner = models.URLField(max_length=300, null=True, blank=True, help_text='Input url Banner')
    text_banner = models.TextField(null=True, blank=True, help_text='Input text to Banner')
    speed_banner = models.IntegerField(default=5, null=True, blank=True, help_text='Input speed to Banner')

    class Meta:
        verbose_name = 'home banner slide'
        verbose_name_plural = 'home banner slides'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_banner = self.__class__.__name__.lower()

    def clean(self):
        super().clean()
        self.validate_url(self.url_banner)
        self.count_integer(self.speed_banner)


class HomeNewsSharesBanner(Banners):
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Изображение")

    url_banner = models.URLField(max_length=300, null=True, blank=True, help_text='Input url Banner')
    speed_banner = models.IntegerField(default=5, null=True, blank=True, help_text='Input speed to Banner')

    class Meta:
        verbose_name = 'home news/shares slide'
        verbose_name_plural = 'home news/shares slides'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_banner = self.__class__.__name__.lower()

    def clean(self):
        super().clean()
        self.validate_url(self.url_banner)
        self.count_integer(self.speed_banner)


class BackgroundBanner(Banners):  # Model BackgroundBanner
    image_banner = models.ImageField(upload_to='backgrounds/', null=True, blank=True,
                                   help_text='Upload an image. Supported formats: JPEG, PNG')
    color = models.CharField(max_length=20, blank=True, null=True,
                             help_text='Color name or HEX, e.g. red or #ff0000'
    )
    class Meta:
        verbose_name = 'background banner'
        verbose_name_plural = 'background banners'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_banner = self.__class__.__name__.lower()


class TypePageChoices(models.TextChoices):
    NEWS = ('news', 'News')
    SHARES = ('shares', 'Shares')


STATUS_CHOICES = (
    (True, 'On'),
    (False, 'Off'),
)
