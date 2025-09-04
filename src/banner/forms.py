from django import forms
from .models import HomeBanner, BackgroundBanner, HomeNewsSharesBanner
from src.core.models import Gallery, Image

class HomeBannerSlideForm(forms.ModelForm):
    class Meta:
        model = HomeBanner
        fields = ["url_banner", "text_banner", "gallery_banner"]

    image = forms.ImageField(required=False)

    def save(self, commit=True):
        banner = super().save(commit=False)

        if commit:
            banner.save()

        # если загружена новая картинка
        if self.cleaned_data.get("image"):
            img = Image.objects.create(image=self.cleaned_data["image"])
            if not banner.gallery_banner:
                gallery = Gallery.objects.create(name_gallery=f"banner_{banner.pk}_gallery")
                banner.gallery_banner = gallery
                banner.save(update_fields=["gallery_banner"])
            banner.gallery_banner.image_set.add(img)

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


class NewsSharesBannerForm(forms.ModelForm):
    class Meta:
        model = HomeNewsSharesBanner
        fields = ["url_banner", "gallery_banner"]

    image = forms.ImageField(required=False)

    def save(self, commit=True):
        banner = super().save(commit=False)

        if commit:
            banner.save()

        # если загружена новая картинка
        if self.cleaned_data.get("image"):
            img = Image.objects.create(image=self.cleaned_data["image"])
            if not banner.gallery_banner:
                gallery = Gallery.objects.create(name_gallery=f"banner_{banner.pk}")
                banner.gallery_banner = gallery
                banner.save(update_fields=["gallery_banner"])
            banner.gallery_banner.image_set.add(img)

        return banner