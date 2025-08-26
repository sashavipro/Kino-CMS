# templatetags/hall_filters.py
from django import template

register = template.Library()

@register.filter
def get_range(value):
    """Фильтр для создания диапазона чисел от 1 до value."""
    return range(1, value + 1)