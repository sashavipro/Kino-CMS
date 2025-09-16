from modeltranslation.translator import register, TranslationOptions

from src.cinema.models import Film
from src.core.models import SeoBlock
from src.page.models import MainPage, OtherPage, NewsPromotionPage


@register(MainPage)
class MainPageTranslationOptions(TranslationOptions):
    fields = ('seo_text',) # Телефоны обычно не переводятся

@register(OtherPage)
class OtherPageTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)

@register(NewsPromotionPage)
class NewsPromotionPageTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

@register(Film)
class FilmTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)

@register(SeoBlock)
class SeoBlockTranslationOptions(TranslationOptions):
    fields = ('title_seo', 'keywords_seo', 'description_seo',)



