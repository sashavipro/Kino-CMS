from django.contrib import admin
from .models import SeoBlock, Image, Gallery

@admin.register(SeoBlock)
class SeoBlockAdmin(admin.ModelAdmin):
    list_display = ("slug", "title_seo", "keywords_seo", "description_seo")
    prepopulated_fields = {"slug": ("title_seo",)}
    search_fields = ("title_seo", "keywords_seo", "description_seo")

class ImageInline(admin.TabularInline):
    model = Image.gallery.through
    extra = 0
    can_delete = True

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['name_gallery']
    search_fields = ['name_gallery']
    list_filter = []
    # list_editable = []
    fields = ['name_gallery']
    # readonly_fields = ['create_time', 'update_time']
    inlines = [ImageInline]