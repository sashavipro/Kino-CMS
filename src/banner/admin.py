from django.contrib import admin
from .models import HomeBanner, BackgroundBanner, HomeNewsSharesBanner, Banners

@admin.register(Banners)
class BannersAdmin(admin.ModelAdmin):
    list_display = ['name_banner', 'status_banner']
    search_fields = ['name_banner']
    list_filter = []
    # list_editable = []
    fields = ['name_banner', 'status_banner']
    # readonly_fields = ['create_time', 'update_time']

@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    list_display = ['gallery_banner', 'url_banner', 'text_banner', 'speed_banner']
    search_fields = []
    list_filter = []
    # list_editable = []
    fields = ['gallery_banner', 'url_banner', 'text_banner', 'speed_banner']
    # readonly_fields = ['create_time', 'update_time']

@admin.register(HomeNewsSharesBanner)
class HomeNewsSharesBannerAdmin(admin.ModelAdmin):
    list_display = ['gallery_banner', 'url_banner', 'speed_banner']
    search_fields = []
    list_filter = []
    # list_editable = []
    fields = ['gallery_banner', 'url_banner', 'speed_banner']
    # readonly_fields = ['create_time', 'update_time']

@admin.register(BackgroundBanner)
class BackgroundBannerAdmin(admin.ModelAdmin):
    list_display = ['image_banner']
    search_fields = []
    list_filter = []
    # list_editable = []
    fields = ['image_banner']
    # readonly_fields = ['create_time', 'update_time']

