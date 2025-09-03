from django import forms
from .models import HomeBanner, BackgroundBanner, STATUS_CHOICES

class HomeBannerTopForm(forms.ModelForm):
    status_banner = forms.BooleanField(required=False, label='Status home banner', initial=True,
                                       widget=forms.RadioSelect(choices=STATUS_CHOICES,
                                                                attrs={'class': 'form-check-inline'}))
    url_banner = forms.URLField(required=False, label='URL banner',
                                widget=forms.URLInput(attrs={'placeholder': 'Write url address to home banner here',
                                                             'class': 'form-control'}),
                                help_text='Input URL for home banner')
    text_banner = forms.CharField(required=False, max_length=50, label='Banner text',
                                  help_text='Input text to home banner here',
                                  widget=forms.TextInput(attrs={'class': 'form-control',
                                                                'placeholder': 'Write text for home banner here'}))
    speed_banner = forms.IntegerField(required=False, label='Input speed to home banner',
                                      widget=forms.NumberInput(attrs={'class': 'form-control',
                                                                      'placeholder': 'Write secconds for home banner'}))

    class Meta:
        model = HomeBanner
        fields = ['status_banner', 'url_banner', 'text_banner', 'speed_banner']


class BackgroundBannerForm(forms.ModelForm):
    status_banner = forms.BooleanField(required=False, label='Status home banner', initial=True,
                                       widget=forms.RadioSelect(choices=STATUS_CHOICES,
                                                                attrs={'class': 'form-check-inline'}))
    image_banner = forms.ImageField(required=False, label="Image",
                                    widget=forms.ClearableFileInput(attrs={'class': 'form-control-file',
                                                                           'id': 'file_id',
                                                                           'placeholder': 'Choice image to banner'}))

    class Meta:
        model = BackgroundBanner
        fields = ['status_banner', 'image_banner']