from django.contrib import admin
from .models import MainPage

@admin.register(MainPage)
class MainPageAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # разрешаем добавлять, только если еще нет MainPage
        return not MainPage.objects.exists()