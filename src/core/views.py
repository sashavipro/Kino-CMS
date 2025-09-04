from django.shortcuts import render, redirect, get_object_or_404
from src.banner.models import HomeBanner, HomeNewsSharesBanner, BackgroundBanner
from src.banner.forms import HomeBannerSlideForm


def admin_stats(request):
    return render(request, 'core/adminlte/admin_stats.html')


def admin_banner_slider(request):
    home_slides = HomeBanner.objects.all().order_by("id")
    background = BackgroundBanner.objects.first()
    news_banner = HomeNewsSharesBanner.objects.first()

    if request.method == "POST":
        action = request.POST.get("action")

        # удалить слайд
        delete_id = request.POST.get("delete_id")
        if delete_id:
            HomeBanner.objects.filter(pk=delete_id).delete()
            return redirect("core:admin_banner_slider")

        # добавить слайд
        if action == "add_slide":
            HomeBanner.objects.create(url_banner="", text_banner="")
            return redirect("core:admin_banner_slider")

        # сохранить слайды
        if action == "save_home_slides":
            speed = request.POST.get("speed", 5)
            for banner in home_slides:
                prefix = str(banner.id)
                form = HomeBannerSlideForm(
                    request.POST, request.FILES,
                    instance=banner,
                    prefix=prefix
                )
                if form.is_valid():
                    form.save()
            # скорость обновляем всем слайдам
            HomeBanner.objects.update(speed_banner=speed)
            return redirect("core:admin_banner_slider")

        # фон
        if action == "save_background":
            mode = request.POST.get("mode")
            color = request.POST.get("color")
            image = request.FILES.get("image")

            if not background:
                background = BackgroundBanner.objects.create()

            if mode == "image" and image:
                background.image_banner = image
                background.color = ""
            elif mode == "color" and color:
                background.image_banner = None
                background.color = color.strip()
            background.save()
            # print(">>> SAVE_BACKGROUND mode:", mode, "color:", color)
            return redirect("core:admin_banner_slider")

        if action == "delete_background":
            if background:
                background.image_banner = None
                background.color = ""
                background.save()
            return redirect("core:admin_banner_slider")

    return render(request, "core/adminlte/admin_banner_slider.html", {
        "home_slides": home_slides,
        "background": background,
        "news_banner": news_banner,
        "speed_choices": [3, 5, 7, 10, 15],
    })

def admin_films(request):
    return render(request, 'core/adminlte/admin_films.html')


def admin_cinema(request):
    return render(request, 'core/adminlte/admin_cinema.html')


def admin_news(request):
    return render(request, 'core/adminlte/admin_news.html')


def admin_promotion(request):
    return render(request, 'core/adminlte/admin_promotion.html')


def admin_other_page(request):
    return render(request, 'core/adminlte/admin_other_page.html')


def admin_users(request):
    return render(request, 'core/adminlte/admin_users.html')


def admin_mailing(request):
    return render(request, 'core/adminlte/admin_mailing.html')

#------------------------------
# Главная
def index(request):
    context = {
        "home_slides": HomeBanner.objects.filter(status_banner=True).order_by("id"),
        "background": BackgroundBanner.objects.filter(status_banner=True).first(),
        "news_banner": HomeNewsSharesBanner.objects.filter(status_banner=True).first(),
    }
    return render(request, "core/user/index.html", context)

# Афиша
def poster(request):
    return render(request, 'core/user/poster.html')

# Фильм из афиши
def film_page(request):
    return render(request, 'core/user/film_page.html')

# Расписание
def schedule(request):
    return render(request, 'core/user/schedule.html')

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
    return render(request, 'core/user/ticket_reservation.html', {'hall_layout': hall_layout})

# Скоро
def soon(request):
    return render(request, 'core/user/soon.html')

# Кинотеатры
def cinemas(request):
    return render(request, 'core/user/cinemas.html')

# Карта кинотеатра
def cinema_card(request):
    return render(request, 'core/user/cinema_card.html')

# Карта зала
def card_hall(request):
    return render(request, 'core/user/card_hall.html')

# Акции и скидки
def stocks(request):
    return render(request, 'core/user/stocks.html')

# Картачка акций и скидок
def stocks_card(request):
    return render(request, 'core/user/stocks_card.html')


# О кинотеатре
def about_cinema(request):
    return render(request, 'core/user/about_cinema.html')


# Новости
def news(request):
    return render(request, 'core/user/news.html')


# Реклама
def advertising(request):
    return render(request, 'core/user/advertising.html')


# Vip зал
def vip_hall(request):
    return render(request, 'core/user/vip_hall.html')


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
    return render(request, 'core/user/cafe.html', {'table_data': table_data})


# Моб. приложение
def mob_app(request):
    return render(request, 'core/user/mob_app.html')


# Контакты
def contacts(request):
    return render(request, 'core/user/contacts.html')


