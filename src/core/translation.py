from modeltranslation.translator import register, TranslationOptions
from src.core.models import SeoBlock
from src.page.models import MainPage, OtherPage


@register(MainPage)
class MainPageTranslationOptions(TranslationOptions):
    fields = ('seo_text',) # Телефоны обычно не переводятся

@register(OtherPage)
class OtherPageTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)

@register(SeoBlock)
class SeoBlockTranslationOptions(TranslationOptions):
    fields = ('title_seo', 'keywords_seo', 'description_seo',)