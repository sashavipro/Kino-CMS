import re

from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from src.banner.models import HomeBanner, HomeNewsSharesBanner, BackgroundBanner
from src.banner.forms import HomeBannerSlideForm, NewsSharesBannerForm
from src.cinema.models import Cinema, Hall
from src.core.models import SeoBlock, Gallery, Image, GalleryImage
from src.page.models import MainPage, OtherPage, OtherPageSlide, NewsPromotionPage, Contact
from src.users.models import CustomUser


def admin_stats(request):
    return render(request, 'core/adminlte/admin_stats.html')


# Главная
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
def index(request):
    try:
        main_page = MainPage.objects.get(status=True)
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
def admin_home_page(request):
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

        main_page.status = 'status' in request.POST

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


# Афиша # Скоро # Фильм из афиши
def admin_films(request):
    return render(request, 'core/adminlte/admin_films.html')
def soon(request):
    return render(request, 'core/user/soon.html')
def poster(request):
    return render(request, 'core/user/poster.html')
def film_page(request):
    return render(request, 'core/user/film_page.html')

# Акции и скидки и новости
def admin_news(request):
    # Логика POST-запросов (создание/удаление) остается без изменений
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            NewsPromotionPage.objects.create(name="НОВАЯ НОВОСТЬ", status=True, is_promotion=False)
            return redirect("core:admin_news")
        if action == "delete":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(NewsPromotionPage, pk=item_id, is_promotion=False)
            item.delete()
            return redirect("core:admin_news")

    # Получаем полный список новостей
    news_queryset = NewsPromotionPage.objects.filter(is_promotion=False).order_by("-time_created")

    # Добавляем пагинацию (20 новостей на страницу в админке)
    paginator = Paginator(news_queryset, 1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "core/adminlte/admin_news.html", {"news_list": page_obj})
def news(request):
    news_queryset = NewsPromotionPage.objects.filter(is_promotion=False, status=True).order_by("-time_created")

    # Добавляем пагинацию (9 новостей на страницу, удобно для сетки 3x3)
    paginator = Paginator(news_queryset, 1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- ПОЛУЧАЕМ SEO-БЛОК ДЛЯ СТРАНИЦЫ ---
    try:
        # Ищем по тому самому "якорю", который создали в админке
        seo_block = SeoBlock.objects.get(slug='news-list')
    except SeoBlock.DoesNotExist:
        seo_block = None  # Если забыли создать в админке, сайт не упадет

    context = {
        'news_list': page_obj,
        'seo_block': seo_block
    }

    return render(request, 'core/user/news.html', context)
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
    # Логика POST-запросов (создание/удаление) остается без изменений
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            NewsPromotionPage.objects.create(name="НОВАЯ АКЦИЯ", status=True, is_promotion=True)
            return redirect("core:admin_promotion")
        if action == "delete":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(NewsPromotionPage, pk=item_id, is_promotion=True)
            item.delete()
            return redirect("core:admin_promotion")

    # Получаем полный список акций
    promotion_queryset = NewsPromotionPage.objects.filter(is_promotion=True).order_by("-time_created")

    # Добавляем пагинацию (20 акций на страницу в админке)
    paginator = Paginator(promotion_queryset, 1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "core/adminlte/admin_promotion.html", {"promotion_list": page_obj})
def stocks(request):
    promotions_queryset = NewsPromotionPage.objects.filter(is_promotion=True, status=True).order_by("-time_created")

    # Добавляем пагинацию (9 акций на страницу)
    paginator = Paginator(promotions_queryset, 1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- ПОЛУЧАЕМ SEO-БЛОК ДЛЯ СТРАНИЦЫ ---
    try:
        # Ищем по "якорю" для акций
        seo_block = SeoBlock.objects.get(slug='promotions-list')
    except SeoBlock.DoesNotExist:
        seo_block = None

    # --- ДОБАВЛЯЕМ SEO-БЛОК В КОНТЕКСТ ---
    context = {
        'promotion_list': page_obj,
        'seo_block': seo_block
    }

    return render(request, 'core/user/stocks.html', context)
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


@require_http_methods(["GET", "POST"])
def admin_other_page(request):
    if request.method == "POST":
        if "create_page" in request.POST:
            base_name = "новая-страница"
            new_name = base_name
            counter = 1
            while OtherPage.objects.filter(name=new_name).exists():
                counter += 1
                new_name = f"{base_name}-{counter}"

            unique_slug = f'page-{int(timezone.now().timestamp())}'
            new_seo_block = SeoBlock.objects.create(slug=unique_slug)

            new_page = OtherPage.objects.create(
                name=new_name,
                title="Новая страница", # Сразу задаем временный заголовок
                description="",
                seo_block=new_seo_block,
                status=False
            )
            return redirect("core:edit_other_page", page_name=new_page.name)

        if "delete_page" in request.POST:
            page_id = request.POST.get("delete_page")
            page = get_object_or_404(OtherPage, id=page_id)
            page.delete()
            return redirect("core:admin_other_page")

    # Создаем универсальный список для передачи в шаблон
    pages_to_render = []

    # 1. Главная страница
    main_page_obj = MainPage.objects.first()
    if main_page_obj:
        pages_to_render.append({
            'display_title': "Главная страница",
            'created': main_page_obj.time_created,
            'status': main_page_obj.status,
            'type': "main",
            'id': main_page_obj.id,
            'system_name': None # Не нужно для URL
        })

    # 2. Страница контактов
    try:
        contact_seo = SeoBlock.objects.get(slug='contacts')
        pages_to_render.append({
            'display_title': 'Контакты',
            'created': contact_seo.time_created if hasattr(contact_seo, 'time_created') else timezone.now(),
            'status': True,
            'type': 'contact',
            'id': 'contact',
            'system_name': None # Не нужно для URL
        })
    except SeoBlock.DoesNotExist:
        pass

    # 3. Другие страницы
    other_pages = OtherPage.objects.all()
    for p in other_pages:
        pages_to_render.append({
            'display_title': p.title or p.name,
            'created': p.time_created,
            'status': p.status,
            'type': "other",
            'id': p.id,
            'system_name': p.name  # Системное имя для URL
        })

    return render(request, "core/adminlte/admin_other_page.html", {"pages": pages_to_render})
def edit_other_page(request, page_name):
    page = get_object_or_404(OtherPage, name=page_name)

    seo_block = page.seo_block
    slides = OtherPageSlide.objects.filter(page=page)

    if request.method == 'POST':
        # --- вся логика сохранения данных из формы ---

        # Обновление основных полей
        page.status = 'status' in request.POST
        page.title = request.POST.get('title', '')
        page.description = request.POST.get('description', '')

        # Обновление главной картинки
        if request.FILES.get('main_image'):
            page.main_image = request.FILES['main_image']

        # Логика удаления главной картинки
        if request.POST.get('action') == 'delete_main_image':
            if page.main_image:
                page.main_image.delete(save=False)  # save=False, так как мы сохраним объект ниже

        page.save()

        # Обновление SEO-блока
        if seo_block:
            seo_block.slug = request.POST.get('slug', '')
            seo_block.title_seo = request.POST.get('title_seo', '')
            seo_block.keywords_seo = request.POST.get('keywords', '')
            seo_block.description_seo = request.POST.get('description_seo', '')
            seo_block.save()

        # --- Логика для галереи ---

        # Добавление нового слайда
        if request.POST.get('action') == 'add_slide':
            OtherPageSlide.objects.create(page=page)  # Создаем пустой слайд

        # Удаление слайда
        if 'delete_id' in request.POST:
            slide_to_delete = get_object_or_404(OtherPageSlide, id=request.POST.get('delete_id'))
            slide_to_delete.delete()

        # Обновление изображений в существующих слайдах
        for slide in slides:
            image_file = request.FILES.get(f'{slide.id}-image')
            if image_file:
                slide.image = image_file
                slide.save()

        return redirect('core:edit_other_page', page_name=page.name)

    context = {
        'page': page,
        'slides': slides,
        'seo_block': seo_block,
    }

    # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: рендерим шаблон-обертку вместо "голой" формы
    return render(request, 'core/adminlte/admin_edit_page_wrapper.html', context)
def other_page_detail(request, page_name):
    """
    Универсальное представление для отображения любой "другой страницы"
    для пользователей.
    """
    # Ищем страницу по имени и обязательно проверяем, что она активна (status=True)
    page = get_object_or_404(OtherPage, name=page_name, status=True)
    seo_block = page.seo_block
    slides = page.slides.all() # Убедитесь, что у вас есть related_name='slides' в модели слайдов

    context = {
        'page': page,
        'seo_block': seo_block,
        'slides': slides,
    }

    # Всегда рендерим один и тот же шаблон
    return render(request, 'core/user/other_page_detail.html', context)




# Декоратор для проверки, что пользователь - суперюзер
def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def admin_users(request):
    """
       Отображает список пользователей.
       Обрабатывает ПОИСК, СОРТИРОВКУ, УДАЛЕНИЕ и ПАГИНАЦИЮ.
       """
    # --- Логика POST-запроса (удаление) остается без изменений ---
    if request.method == 'POST' and 'delete_user' in request.POST:
        user_id = request.POST.get('delete_user')
        user_to_delete = get_object_or_404(CustomUser, pk=user_id)
        if request.user.pk != user_to_delete.pk:
            user_to_delete.delete()
        return redirect('core:admin_users')

    # --- Логика GET-запроса (сортировка и поиск) остается без изменений ---
    users_list = CustomUser.objects.all()  # Переименовываем, чтобы не путать с итоговым списком
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'id')
    order = request.GET.get('order', 'asc')

    if search_query:
        users_list = users_list.filter(
            Q(id__icontains=search_query) | Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) | Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) | Q(username__icontains=search_query) |
            Q(city__icontains=search_query)
        )

    valid_sort_fields = ['id', 'date_joined', 'birthday', 'email', 'phone', 'last_name', 'username', 'city']
    if sort_by in valid_sort_fields:
        if order == 'desc':
            sort_by = f'-{sort_by}'
        users_list = users_list.order_by(sort_by)

    # --- 2. ДОБАВЛЯЕМ ЛОГИКУ ПАГИНАЦИИ ---
    # Создаем объект Paginator. 20 - количество пользователей на странице.
    paginator = Paginator(users_list, 1)

    # Получаем номер страницы из GET-параметра 'page'. По умолчанию - страница 1.
    page_number = request.GET.get('page')

    # Получаем объект Page для запрошенной страницы.
    # .get_page() безопаснее, чем .page(), т.к. обрабатывает некорректные номера страниц.
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # <-- 3. ПЕРЕДАЕМ В ШАБЛОН ОБЪЕКТ СТРАНИЦЫ, А НЕ ВЕСЬ СПИСОК
        'search_query': search_query,
        'sort': sort_by.lstrip('-'),  # Убираем минус для передачи в шаблон
        'order': order
    }
    return render(request, 'core/adminlte/admin_users.html', context)
@user_passes_test(is_superuser)
def edit_users(request, user_pk):
    """
        Редактирует данные конкретного пользователя.
        """
    user_to_edit  = get_object_or_404(CustomUser, pk=user_pk)
    success = False
    errors = []

    if request.method == 'POST':
        # Эта логика почти полностью взята из profile_view
        user_to_edit.first_name = request.POST.get('first_name', user_to_edit.first_name)
        user_to_edit.last_name = request.POST.get('last_name', user_to_edit.last_name)
        user_to_edit.username = request.POST.get('username', user_to_edit.username)
        user_to_edit.address = request.POST.get('address', user_to_edit.address)
        user_to_edit.city = request.POST.get('city', user_to_edit.city)
        user_to_edit.birthday = request.POST.get('birthday') or None
        user_to_edit.card_number = request.POST.get('card_number', user_to_edit.card_number)
        user_to_edit.gender = request.POST.get('gender', user_to_edit.gender)
        user_to_edit.language = request.POST.get('language', user_to_edit.language)

        email = request.POST.get('email')
        if email and email != user_to_edit.email:
            if CustomUser.objects.filter(email=email).exclude(pk=user_to_edit.pk).exists():
                errors.append('Этот email уже используется.')
            else:
                user_to_edit.email = email

        phone = request.POST.get('phone')
        phone_regex = r'^\+?1?\d{9,15}$'
        if phone and phone.strip() and not re.match(phone_regex, phone):
            errors.append('Введите корректный номер телефона.')
        else:
            user_to_edit.phone = phone

        password = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password or password2:
            if password == password2:
                if password:
                    user_to_edit.set_password(password)
            else:
                errors.append('Пароли не совпадают.')

        if not errors:
            user_to_edit.save()
            success = True
            return redirect('core:admin_users')

    context = {
        'user_to_edit': user_to_edit,
        'success': success,
        'errors': errors,
        'gender_choices': CustomUser.GENDER_CHOICES,
        'language_choices': CustomUser.LANGUAGE_CHOICES,
        'city_choices': CustomUser.CITY_CHOICES,
    }
    return render(request, 'core/adminlte/edit_users.html', context)



def admin_mailing(request):
    return render(request, 'core/adminlte/admin_mailing.html')


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


# Кинотеатры Карта кинотеатра Карта зала
def admin_cinema(request):
    """
    Отображает список кинотеатров.
    Обрабатывает ДОБАВЛЕНИЕ и УДАЛЕНИЕ кинотеатров.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        delete_id = request.POST.get('delete_id')

        if action == 'add_cinema':
            Cinema.objects.create(name="Новый кинотеатр")
            return redirect('core:admin_cinema')

        if delete_id:
            cinema_to_delete = get_object_or_404(Cinema, pk=delete_id)
            cinema_to_delete.delete()
            return redirect('core:admin_cinema')

    cinemas = Cinema.objects.all().order_by('name')
    return render(request, 'core/adminlte/admin_cinema.html', {'cinemas': cinemas})
def cinemas(request):
    cinemas = Cinema.objects.all()
    return render(request, 'core/user/cinemas.html', {'cinemas': cinemas})
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
def card_hall(request, pk):
    """
    Отображает детальную страницу одного зала.
    """
    hall = get_object_or_404(Hall, pk=pk)
    sibling_halls = hall.cinema.halls.all().order_by('number_hall')

    context = {
        'hall': hall,
        'cinema': hall.cinema,
        'halls': sibling_halls,
        'seo_block': hall.seo_block,
    }
    return render(request, 'core/user/card_hall.html', context)


# Контакты
def admin_contacts_page(request):
    """
       Управляет контактами и SEO-блоком в админ-панели.
       """
    # Получаем или создаем SEO-блок для страницы контактов
    seo_block, _ = SeoBlock.objects.get_or_create(
        slug='contacts',
        defaults={'title_seo': 'Контакты'}
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- ОБРАБОТКА ДЕЙСТВИЙ ИЗ ФОРМЫ ---

        # 1. Добавить новый контакт
        if action == 'add_contact':
            Contact.objects.create(name='Новый кинотеатр', status=False, address='')
            return redirect('core:admin_contacts_page')

        # 2. Удалить контакт по 'крестику'
        if 'delete_id' in request.POST:
            contact_to_delete = get_object_or_404(Contact, pk=request.POST.get('delete_id'))
            contact_to_delete.delete()  # Метод delete в модели также удалит файл
            return redirect('core:admin_contacts_page')

        # 3. Удалить логотип (исправленная логика)
        if 'delete_logo' in request.POST:
            contact_pk = request.POST.get('delete_logo')
            contact_to_update = get_object_or_404(Contact, pk=contact_pk)
            if contact_to_update.logo:
                contact_to_update.logo.delete(save=True)  # Удаляем файл и сохраняем
            return redirect('core:admin_contacts_page')

        # 4. Сохранить все изменения
        if action == 'save_all':
            # Обновляем SEO-блок
            seo_block.title_seo = request.POST.get('title_seo', '')
            seo_block.keywords_seo = request.POST.get('keywords', '')
            seo_block.description_seo = request.POST.get('description_seo', '')
            seo_block.save()

            # Обновляем все контакты
            for contact in Contact.objects.all():
                prefix = f'contact-{contact.pk}-'

                contact.name = request.POST.get(prefix + 'name', contact.name)
                contact.address = request.POST.get(prefix + 'address', contact.address)
                contact.coords = request.POST.get(prefix + 'coords', contact.coords)
                contact.status = request.POST.get(prefix + 'status') == 'on'

                # Загрузка нового логотипа
                if prefix + 'logo' in request.FILES:
                    if contact.logo:  # Если есть старый логотип, удаляем его
                        contact.logo.delete(save=False)
                    contact.logo = request.FILES[prefix + 'logo']

                contact.save()
            return redirect('core:admin_contacts_page')

    # GET-запрос: просто отображаем все контакты и SEO-блок
    contacts = Contact.objects.all()
    context = {
        'contacts': contacts,
        'seo_block': seo_block,
    }
    # Укажите правильный путь к вашему шаблону админки
    return render(request, 'core/adminlte/admin_contacts_page.html', context)
def contacts(request):
    """
    Отображает страницу с контактами для пользователей.
    Показывает только активные контакты.
    """
    # Мы жестко задаем slug='contacts' для поиска SEO-блока этой страницы
    seo_block = get_object_or_404(SeoBlock, slug='contacts')

    # Фильтруем контакты по статусу 'ВКЛ'
    contacts = Contact.objects.filter(status=True)

    context = {
        'contacts': contacts,
        'seo_block': seo_block,
    }
    # Укажите правильный путь к вашему шаблону
    return render(request, 'core/user/contacts.html', context)







