from django.contrib import admin
from .models import SeoBlock, Image, Gallery

@admin.register(SeoBlock)
class SeoBlockAdmin(admin.ModelAdmin):
    list_display = ("slug", "title_seo", "keywords_seo", "description_seo")
    search_fields = ("title_seo", "keywords_seo", "description_seo")

class ImageInline(admin.TabularInline):
    # Указываем саму модель Image
    model = Image
    # Поля, которые мы хотим видеть в админке
    fields = ('image',)
    # Количество пустых форм для добавления новых картинок
    extra = 1
    # Разрешаем удаление
    can_delete = True

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['name_gallery']
    search_fields = ['name_gallery']
    inlines = [ImageInline]