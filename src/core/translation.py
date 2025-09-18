from modeltranslation.translator import register, TranslationOptions

from src.cinema.models import Film, Cinema, Hall
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

@register(Cinema)
class CinemaTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'conditions')


@register(Hall)
class HallTranslationOptions(TranslationOptions):
    fields = ('number_hall', 'description')

@register(SeoBlock)
class SeoBlockTranslationOptions(TranslationOptions):
    fields = ('title_seo', 'keywords_seo', 'description_seo',)



