from django.contrib import admin
from .models import HomeBanner, BackgroundBanner, HomeNewsSharesBanner, Banners

@admin.register(Banners)
class BannersAdmin(admin.ModelAdmin):
    list_display = ['name_banner', 'status_banner']
    search_fields = ['name_banner']
    list_filter = []
    fields = ['name_banner', 'status_banner']

@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    list_display = ['image', 'url_banner', 'text_banner', 'speed_banner', 'status_banner']
    search_fields = ['text_banner']
    list_filter = ['status_banner']
    fields = ['image', 'url_banner', 'text_banner', 'speed_banner', 'status_banner']
@admin.register(HomeNewsSharesBanner)
class HomeNewsSharesBannerAdmin(admin.ModelAdmin):
    list_display = ['image', 'url_banner', 'speed_banner', 'status_banner']
    list_filter = ['status_banner']
    search_fields = []
    fields = ['image', 'url_banner', 'speed_banner', 'status_banner']

@admin.register(BackgroundBanner)
class BackgroundBannerAdmin(admin.ModelAdmin):
    list_display = ['image_banner']
    search_fields = []
    list_filter = []
    fields = ['image_banner']

