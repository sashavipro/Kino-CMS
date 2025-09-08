from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from src.banner.models import HomeBanner, HomeNewsSharesBanner, BackgroundBanner
from src.banner.forms import HomeBannerSlideForm, NewsSharesBannerForm
from src.core.models import SeoBlock
from src.page.models import MainPage, OtherPage, OtherPageSlide


def admin_stats(request):
    return render(request, 'core/adminlte/admin_stats.html')


def admin_banner_slider(request):
    home_slides = HomeBanner.objects.all().order_by("id")
    news_slides = HomeNewsSharesBanner.objects.all().order_by("id")
    background = BackgroundBanner.objects.first()

    if request.method == "POST":
        action = request.POST.get("action")

        # === УДАЛЕНИЕ ===
        delete_id = request.POST.get("delete_id")
        if delete_id:
            if HomeBanner.objects.filter(pk=delete_id).exists():
                HomeBanner.objects.filter(pk=delete_id).delete()
            elif HomeNewsSharesBanner.objects.filter(pk=delete_id).exists():
                HomeNewsSharesBanner.objects.filter(pk=delete_id).delete()
            return redirect("core:admin_banner_slider")

        # === ДОБАВЛЕНИЕ ===
        if action == "add_home_slide":
            HomeBanner.objects.create(url_banner="", text_banner="")
            return redirect("core:admin_banner_slider")

        if action == "add_news_slide":
            HomeNewsSharesBanner.objects.create(url_banner="")
            return redirect("core:admin_banner_slider")

        # === СОХРАНЕНИЕ HOME SLIDES ===
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
            HomeBanner.objects.update(speed_banner=speed)
            return redirect("core:admin_banner_slider")

        # === СОХРАНЕНИЕ NEWS SLIDES ===
        if action == "save_news_slides":
            for banner in news_slides:
                prefix = str(banner.id)
                form = NewsSharesBannerForm(
                    request.POST, request.FILES,
                    instance=banner,
                    prefix=prefix
                )
                if form.is_valid():
                    form.save()
            return redirect("core:admin_banner_slider")

        # === ФОН ===
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
            return redirect("core:admin_banner_slider")

        if action == "delete_background":
            if background:
                background.image_banner = None
                background.color = ""
                background.save()
            return redirect("core:admin_banner_slider")

    return render(request, "core/adminlte/admin_banner_slider.html", {
        "home_slides": home_slides,
        "news_slides": news_slides,
        "background": background,
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
    return render(request, "core/adminlte/admin_other_page.html")

#---------
def admin_home_page(request):
    """
       Редактор главной страницы через админку (admin_home_page.html).
       Ожидает поля POST:
         - phone1, phone2, seoText
         - url (slug), title, keywords, description  (для SeoBlock)
       Логика:
         - создаём MainPage если не существует (singleton)
         - по slug: если такой SeoBlock есть — обновляем его полями из формы,
           иначе создаём новый SeoBlock и присоединяем к main_page.
         - сохраняем main_page и перенаправляем на ту же страницу с сообщением.
       """
    # Получаем или создаём singleton MainPage (defaults пустые, чтобы не упасть)
    main_page, _ = MainPage.objects.get_or_create(
        defaults={'phone1': '', 'phone2': '', 'seo_text': ''}
    )
    seo_block = main_page.seo_block

    if request.method == 'POST':
        phone1 = request.POST.get('phone1', '').strip()
        phone2 = request.POST.get('phone2', '').strip()
        seo_text = request.POST.get('seoText', '').strip()

        slug = request.POST.get('url', '').strip()
        title = request.POST.get('title', '').strip()
        keywords = request.POST.get('keywords', '').strip()
        description = request.POST.get('description', '').strip()

        # Обновляем поля главной страницы
        main_page.phone1 = phone1
        main_page.phone2 = phone2
        main_page.seo_text = seo_text

        # Если slug задан — создаём/находим SeoBlock и обновляем поля
        if slug:
            # get_or_create по slug. Если найден — обновляем поля.
            seo_obj, created = SeoBlock.objects.get_or_create(
                slug=slug,
                defaults={
                    'title_seo': title or slug,
                    'keywords_seo': keywords,
                    'description_seo': description,
                }
            )
            # В любом случае обновляем поля (на случай, если был найден существующий)
            seo_obj.title_seo = title or seo_obj.title_seo
            seo_obj.keywords_seo = keywords
            seo_obj.description_seo = description
            seo_obj.save()

            main_page.seo_block = seo_obj
        else:
            # Если slug пустой — отвязываем seo_block
            main_page.seo_block = None

        main_page.save()
        messages.success(request, 'Данные главной страницы сохранены.')
        return redirect('core:admin_home_page')

    # GET — показываем форму с текущими значениями
    context = {
        'main_page': main_page,
        'seo_block': seo_block,
    }
    return render(request, 'core/adminlte/admin_home_page.html', context)

def admin_users(request):
    return render(request, 'core/adminlte/admin_users.html')


def admin_about_cinema_page(request):
    return edit_other_page(request, page_name="about_cinema_page", template="core/adminlte/admin_about_cinema_page.html")

def admin_cafe_page(request):
    return edit_other_page(request, page_name="cafe_page", template="core/adminlte/admin_cafe_page.html")


def admin_vip_hall_page(request):
    return edit_other_page(request, page_name="vip_hall_page", template="core/adminlte/admin_vip_hall_page.html")


def admin_advertising_page(request):
    return edit_other_page(request, page_name="advertising_page", template="core/adminlte/admin_advertising_page.html")


def admin_child_room_page(request):
    return render(request, 'core/adminlte/admin_child_room_page.html')


def admin_contacts_page(request):
    return render(request, "core/adminlte/admin_contacts_page.html")


def admin_users_page(request):
    return render(request, 'core/adminlte/admin_users_page.html')


# views.py (фрагмент edit_other_page)
def edit_other_page(request, page_name, template="core/adminlte/edit_other_page.html"):
    page, _ = OtherPage.objects.get_or_create(
        name=page_name,
        defaults={"title": "", "description": ""}
    )
    seo_block = page.seo_block
    slides = page.slides.all()

    if request.method == "POST":
        action = request.POST.get("action")

        # Удалить слайд
        delete_id = request.POST.get("delete_id")
        if delete_id:
            OtherPageSlide.objects.filter(pk=delete_id, page=page).delete()
            messages.success(request, "Слайд удалён.")
            return redirect(request.path)

        # Добавить слайд
        if action == "add_slide":
            OtherPageSlide.objects.create(page=page)
            messages.success(request, "Слайд добавлен.")
            return redirect(request.path)

        # Удалить главную картинку
        if action == "delete_main_image":
            if page.main_image:
                page.main_image.delete(save=False)
                page.main_image = None
                page.save()
                messages.success(request, "Главная картинка удалена.")
            return redirect(request.path)

        # ---- Обычное сохранение страницы (ОДНА кнопка «Сохранить») ----
        page.title = request.POST.get("title", "").strip()
        page.description = request.POST.get("description", "").strip()

        # Обновление главной картинки (если загружена)
        if "main_image" in request.FILES:
            page.main_image = request.FILES["main_image"]

        # Обновление файлов слайдов
        for slide in slides:
            field_name = f"{slide.id}-image"
            if field_name in request.FILES:
                slide.image = request.FILES[field_name]
                slide.save()

        # SEO блок
        slug = request.POST.get("slug", "").strip()
        title_seo = request.POST.get("title_seo", "").strip()
        keywords_seo = request.POST.get("keywords", "").strip()  # Убедитесь, что имя в HTML - "keywords_seo"
        description_seo = request.POST.get("description_seo", "").strip()

        # Если slug не предоставлен, отвязываем и потенциально удаляем SEO блок
        if not slug:
            # Если вы хотите удалить связанный SeoBlock, когда slug стирается:
            # if page.seo_block:
            #     page.seo_block.delete() # Это удалит объект SeoBlock из базы данных
            page.seo_block = None
        else:
            # Если у страницы уже есть SEO блок, обновляем его
            if page.seo_block:
                seo_obj = page.seo_block
                seo_obj.slug = slug
                seo_obj.title_seo = title_seo
                seo_obj.keywords_seo = keywords_seo
                seo_obj.description_seo = description_seo
                seo_obj.save()
            # Если у страницы нет SEO блока, создаем новый
            else:
                # Проверяем, не занят ли уже такой slug другим объектом
                if SeoBlock.objects.filter(slug=slug).exists():
                    messages.error(request, f"SEO блок с таким slug «{slug}» уже существует. Придумайте другой.")
                    # Прерываем сохранение и возвращаем пользователя на страницу редактирования
                    # Важно вернуть redirect, чтобы избежать повторной отправки формы
                    return redirect(request.path)
                else:
                    seo_obj = SeoBlock.objects.create(
                        slug=slug,
                        title_seo=title_seo,
                        keywords_seo=keywords_seo,
                        description_seo=description_seo,
                    )
                    page.seo_block = seo_obj

        page.save()
        messages.success(request, f"Изменения страницы «{page_name}» сохранены.")
        return redirect(request.path)

    context = {"page": page, "seo_block": page.seo_block, "slides": slides}
    return render(request, template, context)

#---------
def admin_mailing(request):
    return render(request, 'core/adminlte/admin_mailing.html')

#------------------------------
# Главная
def index(request):
    """
    Отображение главной страницы (index.html).
    Подаём в шаблон main_page (или None) и связанный seo_block (или None).
    """
    try:
        main_page = MainPage.objects.get()
    except MainPage.DoesNotExist:
        main_page = None

    seo_block = main_page.seo_block if main_page and main_page.seo_block else None
    context = {
        'main_page': main_page,
        'seo_block': seo_block,
        "home_slides": HomeBanner.objects.filter(status_banner=True).order_by("id"),
        "background": BackgroundBanner.objects.filter(status_banner=True).first(),
        "news_slides": HomeNewsSharesBanner.objects.filter(status_banner=True).order_by("id"),
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
    page = get_object_or_404(OtherPage, name="about_cinema_page")
    seo_block = page.seo_block

    context = {
        'page': page,
        'seo_block': seo_block,
        'slides': page.slides.all(),
    }

    return render(request, 'core/user/about_cinema.html', context)


# Новости
def news(request):
    return render(request, 'core/user/news.html')


# Реклама
def advertising(request):
    page = get_object_or_404(OtherPage, name="advertising_page")
    seo_block = page.seo_block

    context = {
        'page': page,
        'seo_block': seo_block,  # <--- ВОТ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ
        'slides': page.slides.all(),  # Также не забудьте передать слайды, если они нужны на странице
    }

    return render(request, 'core/user/advertising.html', context)


# Vip зал
def vip_hall(request):
    page = get_object_or_404(OtherPage, name="vip_hall_page")
    seo_block = page.seo_block

    context = {
        'page': page,
        'seo_block': seo_block,  # <--- ВОТ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ
        'slides': page.slides.all(),  # Также не забудьте передать слайды, если они нужны на странице
    }

    return render(request, 'core/user/vip_hall.html',context)


# Кафе
def cafe(request):
    page = get_object_or_404(OtherPage, name="cafe_page")
    seo_block = page.seo_block

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

    context = {
        'page': page,
        'seo_block': seo_block,
        'slides': page.slides.all(),
        'table_data': table_data,
    }

    return render(request, 'core/user/cafe.html', context)


# Моб. приложение
def mob_app(request):
    return render(request, 'core/user/mob_app.html')


# Контакты
def contacts(request):
    return render(request, 'core/user/contacts.html')


