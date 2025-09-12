# core/context_processors.py
from src.page.models import OtherPage


def other_pages_processor(request):
    """
    Добавляет список активных "других страниц" в контекст каждого шаблона.
    """
    # Выбираем только активные страницы и упорядочиваем их, например, по дате создания
    pages = OtherPage.objects.filter(status=True).order_by('time_created')
    return {'other_pages_for_menu': pages}


def admin_menu_pages_processor(request):
    """
    Добавляет список всех "других страниц" в контекст для использования
    в меню админ-панели.
    """
    # Мы хотим видеть все страницы в админке, даже выключенные
    pages = OtherPage.objects.order_by('title')
    return {'admin_other_pages': pages}