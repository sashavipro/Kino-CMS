from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from src.banner.models import HomeBanner, HomeNewsSharesBanner, BackgroundBanner
from src.banner.forms import HomeBannerSlideForm, NewsSharesBannerForm
from src.cinema.models import Cinema, Hall
from src.core.models import SeoBlock, Gallery, Image, GalleryImage
from src.page.models import MainPage, OtherPage, OtherPageSlide, NewsPromotionPage


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




def admin_news(request):
    if request.method == "POST" and request.POST.get("action") == "create":
        NewsPromotionPage.objects.create(
            name="НОВАЯ НОВОСТЬ",
            status=True,
            description="",
            time_created=timezone.now(),
            is_promotion=False  # Указываем, что создаем именно новость
        )
        return redirect("core:admin_news")

    # удалить новость
    if request.method == "POST" and request.POST.get("action") == "delete":
        pk = request.POST.get("news_id")
        # При удалении тоже проверяем, что это новость
        news = get_object_or_404(NewsPromotionPage, pk=pk, is_promotion=False)
        news.delete()
        return redirect("core:admin_news")

    # Получаем из базы ТОЛЬКО НОВОСТИ
    news_list = NewsPromotionPage.objects.filter(is_promotion=False).order_by("-time_created")
    return render(request, "core/adminlte/admin_news.html", {
        "news_list": news_list
    })


def edit_news(request, pk):
    # Используем имя 'item', т.к. это может быть и новость, и акция
    item = get_object_or_404(NewsPromotionPage, pk=pk)

    # Обработка POST-запроса
    if request.method == "POST":
        action = request.POST.get("action")

        # Удалить главную картинку
        if action == "delete_main_image":
            if item.main_image:
                item.main_image.delete(save=True)
            messages.success(request, "Главная картинка удалена.")
            return redirect(request.path)

        # Добавить картинку в галерею
        if action == "add_slide":
            # Если у записи еще нет галереи, создаем ее
            if not item.gallery_banner:
                gallery_name = f"Gallery for Item {item.pk}"
                gallery, _ = Gallery.objects.get_or_create(name_gallery=gallery_name)
                item.gallery_banner = gallery
                item.save()

            # Создаем изображение и СВЯЗЫВАЕМ его с галереей
            new_image = Image.objects.create()
            item.gallery_banner.images.add(new_image)

            messages.success(request, "Слот для изображения добавлен в галерею.")
            return redirect(request.path)

        # Удалить картинку из галереи
        delete_id = request.POST.get("delete_id")
        if delete_id:
            image_to_delete = get_object_or_404(Image, pk=delete_id)
            # Удаление самого объекта Image каскадно удалит и связь ManyToMany
            image_to_delete.delete()
            messages.success(request, "Изображение удалено из галереи.")
            return redirect(request.path)

        # Статус
        item.status = 'status' in request.POST

        # Текстовые поля
        item.name = request.POST.get('title', '').strip()
        item.description = request.POST.get('description', '').strip()
        item.url_movie = request.POST.get('url_movie', '').strip()

        # Дата
        publication_date = request.POST.get('publicationDate')
        if publication_date:
            item.time_created = publication_date

        # Главная картинка (если загружена новая)
        if 'main_image' in request.FILES:
            item.main_image = request.FILES['main_image']

        # Обновление файлов галереи
        if item.gallery_banner:
            # Обращаемся к 'images' через related_name
            for image in item.gallery_banner.images.all():
                field_name = f"{image.pk}-image" # Надежнее использовать pk
                if field_name in request.FILES:
                    image.image = request.FILES[field_name]
                    image.save()

        # SEO блок
        slug = request.POST.get("slug", "").strip()
        title_seo = request.POST.get("title_seo", "").strip()
        keywords = request.POST.get("keywords", "").strip()
        description_seo = request.POST.get("description_seo", "").strip()

        # ГЛАВНОЕ УСЛОВИЕ: Мы работаем с SEO-блоком, ТОЛЬКО ЕСЛИ slug НЕ ПУСТОЙ.
        if slug:
            # Проверяем, не занят ли этот slug другим SEO-блоком,
            # который не принадлежит текущей записи.
            conflicting_seo = SeoBlock.objects.filter(slug=slug).exclude(pk=getattr(item.seo_block, 'pk', None)).first()
            if conflicting_seo:
                messages.error(request,
                               f"URL (slug) '{slug}' уже используется другой записью. Пожалуйста, выберите уникальный URL.")
            else:
                # Если у записи уже есть SEO-блок, обновляем его
                if item.seo_block:
                    seo_obj = item.seo_block
                    seo_obj.slug = slug
                    seo_obj.title_seo = title_seo
                    seo_obj.keywords_seo = keywords
                    seo_obj.description_seo = description_seo
                    seo_obj.save()
                # Если SEO-блока нет, создаем новый
                else:
                    seo_obj = SeoBlock.objects.create(
                        slug=slug,
                        title_seo=title_seo,
                        keywords_seo=keywords,
                        description_seo=description_seo,
                    )
                    item.seo_block = seo_obj
        # ЕСЛИ SLUG ПУСТОЙ: значит, SEO-блок нам не нужен.
        else:
            # Если у записи был SEO-блок, удаляем его, чтобы не хранить мусор
            if item.seo_block:
                item.seo_block.delete()
            item.seo_block = None

        item.save()
        messages.success(request, f"Запись «{item.name}» успешно сохранена.")

        # <<< ИСПРАВЛЕНО: "Умный" редирект в зависимости от типа записи
        if item.is_promotion:
            return redirect('core:admin_promotion')
        else:
            return redirect('core:admin_news')

    # --- Обработка GET-запроса (просто отображение формы) ---
    gallery_images = []
    if item.gallery_banner:
        # <<< УЛУЧШЕНО: Обращаемся к 'images' через related_name
        gallery_images = item.gallery_banner.images.all()

    context = {
        'item': item, # Оставляем 'news', т.к. шаблон использует это имя
        'seo_block': item.seo_block,
        'slides': gallery_images,
    }
    return render(request, 'core/adminlte/edit_news.html', context)

def admin_promotion(request):
    if request.method == "POST" and request.POST.get("action") == "create":
        NewsPromotionPage.objects.create(
            name="НОВАЯ АКЦИЯ",
            status=True,
            description="",
            time_created=timezone.now(),
            is_promotion=True  # Указываем, что создаем именно АКЦИЮ
        )
        return redirect("core:admin_promotion")

    if request.method == "POST" and request.POST.get("action") == "delete":
        pk = request.POST.get("promotion_id")
        # При удалении проверяем, что это акция
        promotion = get_object_or_404(NewsPromotionPage, pk=pk, is_promotion=True)
        promotion.delete()
        return redirect("core:admin_promotion")

    # Получаем из базы ТОЛЬКО АКЦИИ
    promotion_list = NewsPromotionPage.objects.filter(is_promotion=True).order_by("-time_created")
    return render(request, "core/adminlte/admin_promotion.html", {
        "promotion_list": promotion_list
    })


@require_http_methods(["GET", "POST"])
def admin_other_page(request):
    if request.method == "POST":
        # Создание страницы
        if "create_page" in request.POST:
            OtherPage.objects.create(name="Новая страница", created=timezone.now(), status=False)
            return redirect("core:admin_other_page")

        # Удаление страницы
        if "delete_page" in request.POST:
            page_id = request.POST.get("delete_page")
            page = get_object_or_404(OtherPage, id=page_id)
            page.delete()
            return redirect("core:admin_other_page")

    # Объединяем MainPage и OtherPage
    main_pages = MainPage.objects.all()
    other_pages = OtherPage.objects.all()

    # Добавляем поле type для различия
    pages = []
    for p in main_pages:
        p.type = "main"
        pages.append(p)
    for p in other_pages:
        p.type = "other"
        pages.append(p)

    return render(request, "core/adminlte/admin_other_page.html", {"pages": pages})


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
    #seo_block = page.seo_block
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

        # Статус
        page.status = 'status' in request.POST

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



# Акции и скидки
def stocks(request):
    promotions = NewsPromotionPage.objects.filter(
        is_promotion=True,  # Условие 1: Это должна быть акция
        status=True  # Условие 2: У нее должен быть статус "ВКЛ"
    ).order_by("-time_created")

    context = {
        'promotion_list': promotions
    }
    return render(request, 'core/user/stocks.html', context)

# Картачка акций и скидок
def stocks_card(request, pk):
    """
    Отображает одну конкретную акцию по её ID,
    проверяя, что это действительно АКТИВНАЯ АКЦИЯ.
    """
    promotion = get_object_or_404(
        NewsPromotionPage,
        pk=pk,               # 1. Ищем по конкретному ID из URL
        is_promotion=True,   # 2. Убеждаемся, что это АКЦИЯ, а не новость
        status=True          # 3. Убеждаемся, что статус "ВКЛ"
    )

    # Если объект найден, передаем его в шаблон под именем 'promotion'
    context = {
        'promotion': promotion
    }

    # Отображаем ваш готовый шаблон
    return render(request, 'core/user/stocks_card.html', context)


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
def news(request):  # Имя функции может быть 'news_list' или другое
    news_items = NewsPromotionPage.objects.filter(is_promotion=False, status=True).order_by("-time_created")

    context = {
        'news_list': news_items
    }
    return render(request, 'core/user/news.html', context)


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
        'seo_block': seo_block,
        'slides': page.slides.all(),
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




def admin_cinema(request):
    """
    Отображает список кинотеатров.
    Обрабатывает ДОБАВЛЕНИЕ и УДАЛЕНИЕ кинотеатров.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        delete_id = request.POST.get('delete_id')

        if action == 'add_cinema':
            # Создаем пустой кинотеатр
            Cinema.objects.create(name="Новый кинотеатр")
            # ИСПРАВЛЕНО: Возвращаемся на ту же страницу (список кинотеатров)
            return redirect('core:admin_cinema')

        if delete_id:
            cinema_to_delete = get_object_or_404(Cinema, pk=delete_id)
            cinema_to_delete.delete()
            return redirect('core:admin_cinema')

    cinemas = Cinema.objects.all().order_by('name')
    return render(request, 'core/adminlte/admin_cinema.html', {'cinemas': cinemas})


def edit_cinema(request, cinema_pk):
    """
    Редактирует кинотеатр и все связанные с ним сущности.
    """
    cinema = get_object_or_404(Cinema, pk=cinema_pk)
    gallery = cinema.gallery
    # Используем 'image_set' для согласованности (или 'images', если вы добавили related_name)
    slides = gallery.image_set.all() if gallery else []
    seo_block = cinema.seo_block

    if request.method == 'POST':
        action = request.POST.get('action')
        delete_hall_id = request.POST.get('delete_hall_id')
        delete_slide_id = request.POST.get('delete_slide_id')

        # --- Сохранение ОСНОВНЫХ данных кинотеатра ---
        if action == 'save_cinema':
            cinema.name = request.POST.get('title')
            cinema.description = request.POST.get('description')
            cinema.conditions = request.POST.get('conditions')

            if 'logo' in request.FILES:
                cinema.logo = request.FILES['logo']

            if 'main_image' in request.FILES:
                cinema.main_image = request.FILES['main_image']

            if gallery:
                for image in slides:
                    field_name = f"{image.pk}-image"
                    if field_name in request.FILES:
                        image.image = request.FILES[field_name]
                        image.save()

            slug = request.POST.get('slug', '').strip()
            if slug:
                seo_data = {
                    'slug': slug,
                    'title_seo': request.POST.get('title_seo', ''),
                    'keywords_seo': request.POST.get('keywords', ''),
                    'description_seo': request.POST.get('description_seo', '')
                }
                if seo_block:
                    SeoBlock.objects.filter(pk=seo_block.pk).update(**seo_data)
                else:
                    new_seo = SeoBlock.objects.create(**seo_data)
                    cinema.seo_block = new_seo
            elif seo_block:
                seo_block.delete()

            cinema.save()

            # ЕДИНСТВЕННЫЙ редирект в конце блока сохранения
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        # --- Удаление изображений ---
        if action == 'delete_logo':
            if cinema.logo:
                cinema.logo.delete(save=True)
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        if action == 'delete_main_image':
            if cinema.main_image:
                cinema.main_image.delete(save=True)
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        # --- Управление залами ---
        if action == 'add_hall':
            Hall.objects.create(cinema=cinema, number_hall="Новый зал")
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        if delete_hall_id:
            hall_to_delete = get_object_or_404(Hall, pk=delete_hall_id, cinema=cinema)
            hall_to_delete.delete()
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        # --- Управление галереей ---
        if action == 'add_slide':
            if not gallery:
                gallery = Gallery.objects.create(name_gallery=f"Cinema {cinema.pk} Gallery")
                cinema.gallery = gallery
                cinema.save()

            new_image = Image.objects.create()
            GalleryImage.objects.create(gallery=gallery, images=new_image)
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        if delete_slide_id:
            if gallery:
                image_to_delete = get_object_or_404(Image, pk=delete_slide_id)
                GalleryImage.objects.filter(gallery=gallery, images=image_to_delete).delete()
                image_to_delete.delete()
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

    halls = cinema.halls.all().order_by('number_hall')
    context = {
        'cinema': cinema,
        'halls': halls,
        'slides': slides,
        'seo_block': seo_block,
    }
    return render(request, 'core/adminlte/edit_cinema.html', context)


def edit_halls(request, hall_pk):
    """
    Редактирует зал и все связанные с ним сущности.
    """
    hall = get_object_or_404(Hall, pk=hall_pk)
    gallery = hall.gallery
    slides = gallery.image_set.all() if gallery else []
    seo_block = hall.seo_block

    if request.method == 'POST':
        action = request.POST.get('action')
        delete_slide_id = request.POST.get('delete_slide_id')

        # --- Сохранение данных зала ---
        if action == 'save_hall':
            hall.number_hall = request.POST.get('title')
            hall.description = request.POST.get('description')

            # Сохранение схемы зала
            if 'scheme_image' in request.FILES:
                hall.scheme_image = request.FILES['scheme_image']

            # Сохранение баннера
            if 'banner_image' in request.FILES:
                hall.banner_image = request.FILES['banner_image']

            # Обновление изображений в галерее
            if gallery:
                for image in slides:
                    field_name = f"{image.pk}-image"
                    if field_name in request.FILES:
                        image.image = request.FILES[field_name]
                        image.save()

            # Обработка SEO-блока (аналогично cinema)
            slug = request.POST.get('slug', '').strip()
            if slug:
                seo_data = {
                    'slug': slug,
                    'title_seo': request.POST.get('title_seo', ''),
                    'keywords_seo': request.POST.get('keywords', ''),
                    'description_seo': request.POST.get('description_seo', '')
                }
                if seo_block:
                    SeoBlock.objects.filter(pk=seo_block.pk).update(**seo_data)
                else:
                    hall.seo_block = SeoBlock.objects.create(**seo_data)
            elif seo_block:
                seo_block.delete()

            hall.save()
            # После сохранения остаемся на той же странице
            return redirect('core:edit_hall', hall_pk=hall.pk)

        # --- Удаление изображений ---
        if action == 'delete_scheme_image':
            if hall.scheme_image: hall.scheme_image.delete(save=True)
            return redirect('core:edit_hall', hall_pk=hall.pk)

        if action == 'delete_banner_image':
            if hall.banner_image: hall.banner_image.delete(save=True)
            return redirect('core:edit_hall', hall_pk=hall.pk)

        # --- Управление галереей ---
        if action == 'add_slide':
            if not gallery:
                gallery = Gallery.objects.create(name_gallery=f"Hall {hall.pk} Gallery")
                hall.gallery = gallery
                hall.save()

            new_image = Image.objects.create()
            gallery.image_set.add(new_image)
            return redirect('core:edit_hall', hall_pk=hall.pk)

        if delete_slide_id:
            if gallery:
                slide_to_delete = get_object_or_404(Image, pk=delete_slide_id)
                gallery.image_set.remove(slide_to_delete)
                slide_to_delete.delete()
            return redirect('core:edit_hall', hall_pk=hall.pk)

    context = {
        'hall': hall,
        'slides': slides,
        'seo_block': seo_block,
    }
    return render(request, 'core/adminlte/edit_halls.html', context)




# Кинотеатры
def cinemas(request):
    cinemas = Cinema.objects.all()
    return render(request, 'core/user/cinemas.html', {'cinemas': cinemas})


# Карта кинотеатра
def cinema_card(request, pk):
    cinema = get_object_or_404(Cinema, pk=pk)

    halls = cinema.halls.all()

    seo_block = cinema.seo_block

    context = {
        'cinema': cinema,
        'halls': halls,
        'seo_block': seo_block,
    }

    return render(request, 'core/user/cinema_card.html', context)

# Карта зала
def card_hall(request, pk):
    """
    Отображает детальную страницу одного зала.
    """
    hall = get_object_or_404(Hall, pk=pk)
    # Получаем все залы того же кинотеатра для бокового меню
    sibling_halls = hall.cinema.halls.all().order_by('number_hall')

    context = {
        'hall': hall,
        'cinema': hall.cinema,  # Передаем родительский кинотеатр
        'halls': sibling_halls,  # Передаем все залы этого кинотеатра
        'seo_block': hall.seo_block,
    }
    return render(request, 'core/user/card_hall.html', context)