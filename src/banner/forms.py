from django import forms
from .models import HomeBanner, BackgroundBanner, HomeNewsSharesBanner
from src.core.models import Image, Gallery


class HomeBannerSlideForm(forms.ModelForm):
    upload_image = forms.ImageField(required=False, label="Загрузить новое изображение")

    class Meta:
        model = HomeBanner
        fields = ["url_banner", "text_banner"]

    def save(self, commit=True):
        banner = super().save(commit=False)
        new_image_file = self.cleaned_data.get("upload_image")

        if new_image_file:
            # Получаем или создаем "якорную" галерею для всех слайдов HomeBanner
            home_gallery, _ = Gallery.objects.get_or_create(name_gallery='Home Banner Images')

            # Создаем новый объект Image, СРАЗУ указывая, к какой галерее он принадлежит
            new_image_obj = Image.objects.create(
                image=new_image_file,
                gallery=home_gallery  # <--- ИСПРАВЛЕНО
            )
            banner.image = new_image_obj

        if commit:
            banner.save()
        return banner


class NewsSharesBannerForm(forms.ModelForm):
    upload_image = forms.ImageField(required=False, label="Загрузить новое изображение")

    class Meta:
        model = HomeNewsSharesBanner
        fields = ["url_banner"]

    def save(self, commit=True):
        banner = super().save(commit=False)
        new_image_file = self.cleaned_data.get("upload_image")

        if new_image_file:
            # Получаем или создаем "якорную" галерею для всех слайдов News
            news_gallery, _ = Gallery.objects.get_or_create(name_gallery='News Banner Images')

            # Создаем новый объект Image, СРАЗУ указывая, к какой галерее он принадлежит
            new_image_obj = Image.objects.create(
                image=new_image_file,
                gallery=news_gallery  # <--- ИСПРАВЛЕНО
            )
            banner.image = new_image_obj

        if commit:
            banner.save()
        return banner

class BackgroundForm(forms.ModelForm):
    mode = forms.ChoiceField(
        choices=[("image", "Картинка на фоне"), ("color", "Цвет фона")],
        widget=forms.RadioSelect
    )
    image = forms.ImageField(required=False)
    color = forms.CharField(required=False)

    class Meta:
        model = BackgroundBanner
        fields = []  # управляем вручную

    def save(self, commit=True):
        banner = super().save(commit=False)

        mode = self.cleaned_data.get("mode")
        color = self.cleaned_data.get("color")
        image = self.cleaned_data.get("image")

        if mode == "image" and image:
            banner.image_banner = image
            banner.color = ""   # очищаем цвет
        elif mode == "color" and color:
            banner.image_banner = None
            banner.color = color.strip()
        else:
            # ничего не выбрали
            banner.image_banner = None
            banner.color = ""

        if commit:
            banner.save()
        return banner