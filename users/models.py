from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The email field must be set.')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    username = models.CharField(max_length=60, unique=True, blank=True)
    email = models.EmailField(max_length=60, unique=True)
    address = models.CharField(max_length=128, blank=True, null=True)

    phone = models.CharField(max_length=15, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    card_number = models.CharField(max_length=30, blank=True, null=True)

    GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('eu', 'English'),
    ]

    CITY_CHOICES = [
        ('kiev', 'Киев'),
        ('kharkov', 'Харьков'),
        ('odessa', 'Одесса'),
    ]
    city = models.CharField(max_length=60, blank=True, null=True)
    gender = models.CharField(blank=True, choices=GENDER_CHOICES, null=True)
    language = models.CharField(blank=True, choices=LANGUAGE_CHOICES, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email

    def clean(self):
        for field in ['first_name', 'last_name', 'address', 'card_number',
                      'language', 'gender', 'phone', 'birthday', 'city']:
            value = getattr(self, field)
            if value:
                setattr(self, field, strip_tags(value))
