from django.db import models
from django.core.validators import MinLengthValidator
from src.core.untils.my_validator import UrlValidatorMixin, CounterValidatorMixin
from src.core.models import Gallery

# BANNER ----------------------------------------------------------------------------------------
class Banners(models.Model, UrlValidatorMixin, CounterValidatorMixin):  # Abstract Model Banners
    name_banner = models.CharField(validators=[MinLengthValidator(1)], max_length=50, help_text='Input name Banner')
    status_banner = models.BooleanField(default=True, help_text='Select status Banner')

    class Meta:
        verbose_name = 'banner'
        verbose_name_plural = 'banners'


class HomeBanner(Banners):  # Model HomeBanner
    gallery_banner = models.OneToOneField(Gallery, on_delete=models.CASCADE, blank=True, null=True,
                                          help_text='Select Gallery to Banner')
    url_banner = models.URLField(max_length=300, null=True, blank=True, help_text='Input url Banner')
    text_banner = models.TextField(null=True, blank=True, help_text='Input text to Banner')
    speed_banner = models.IntegerField(default=5, null=True, blank=True, help_text='Input speed to Banner')

    class Meta:
        verbose_name = 'home banner'
        verbose_name_plural = 'home banners'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_banner = self.__class__.__name__.lower()

    def clean(self):
        super().clean()
        self.validate_url(self.url_banner)
        self.count_integer(self.speed_banner)


class HomeNewsSharesBanner(Banners):  # Model HomeNewsSharesBanner
    gallery_banner = models.OneToOneField(Gallery, on_delete=models.CASCADE, blank=True, null=True,
                                          help_text='Select Gallery to Banner')
    url_banner = models.URLField(max_length=300, null=True, blank=True, help_text='Input url to Banner')
    speed_banner = models.IntegerField(default=5, null=True, blank=True, help_text='Input speed to Banner')

    class Meta:
        verbose_name = 'home news and shares banner'
        verbose_name_plural = 'home news and shares banners'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_banner = self.__class__.__name__.lower()

    def clean(self):
        super().clean()
        self.validate_url(self.url_banner)
        self.count_integer(self.speed_banner)


class BackgroundBanner(Banners):  # Model BackgroundBanner
    image_banner = models.ImageField(upload_to='static/photos/', null=True, blank=True,
                                   help_text='Upload an image. Supported formats: JPEG, PNG')

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
