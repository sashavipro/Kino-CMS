from django.shortcuts import render


# Главная
def index(request):
    return render(request, 'main/index.html')

# Афиша
def poster(request):
    return render(request, 'main/poster.html')

# Фильм из афиши
def film_page(request):
    return render(request, 'main/film_page.html')

# Расписание
def schedule(request):
    return render(request, 'main/schedule.html')

# Бронь билетов
def ticket_reservation(request):
    # Пример структуры зала: количество рядов и кол-во мест в каждом
    hall_layout = {
        'rows': [
            {'number': 1, 'seats': 12},
            {'number': 2, 'seats': 13},
            {'number': 3, 'seats': 15},
            {'number': 4, 'seats': 13},
            {'number': 5, 'seats': 13},
            {'number': 6, 'seats': 13},
            {'number': 7, 'seats': 13},
            {'number': 8, 'seats': 13},
            {'number': 9, 'seats': 13},
            {'number': 10, 'seats': 20}
        ]
    }
    return render(request, 'main/ticket_reservation.html', {'hall_layout': hall_layout})

# Скоро
def soon(request):
    return render(request, 'main/soon.html')

# Кинотеатры
def cinemas(request):
    return render(request, 'main/cinemas.html')

# Карта кинотеатра
def cinema_card(request):
    return render(request, 'main/cinema_card.html')

# Карта зала
def card_hall(request):
    return render(request, 'main/card_hall.html')

# Акции и скидки
def stocks(request):
    return render(request, 'main/stocks.html')

# Картачка акций и скидок
def stocks_card(request):
    return render(request, 'main/stocks_card.html')


# О кинотеатре
def about_cinema(request):
    return render(request, 'main/about_cinema.html')


# Новости
def news(request):
    return render(request, 'main/news.html')


# Реклама
def advertising(request):
    return render(request, 'main/advertising.html')


# Vip зал
def vip_hall(request):
    return render(request, 'main/vip_hall.html')


# Кафе
def cafe(request):
    # Пример структуры данных
    table_data = {
        'headers': [
            {'name': 'Head 1', 'sortable': True},
            {'name': 'Head 2', 'sortable': True},
            {'name': 'Head 3', 'sortable': True},
            {'name': 'Выбор', 'sortable': False},
        ],
        'rows': [
            {
                'cells': ['Cell 1', 'Cell 2', 'Cell 3'],
                'selection': {'type': 'checkbox', 'checked': False}
            },
            {
                'cells': ['Cell 4', 'Cell 5', 'Cell 6'],
                'selection': {'type': 'checkbox', 'checked': True}
            },
            {
                'cells': ['Cell 7', 'Cell 8', 'Cell 9'],
                'selection': {'type': 'radio', 'name': 'option', 'checked': False}
            },
            {
                'cells': ['Cell 10', 'Cell 11', 'Cell 12'],
                'selection': {'type': 'radio', 'name': 'option', 'checked': True}
            },
        ]
    }
    return render(request, 'main/cafe.html', {'table_data': table_data})


# Моб. приложение
def mob_app(request):
    return render(request, 'main/mob_app.html')


# Контакты
def contacts(request):
    return render(request, 'main/contacts.html')


