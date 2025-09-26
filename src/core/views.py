import re
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, datetime
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator

from Config import settings
from src.banner.models import HomeBanner, HomeNewsSharesBanner, BackgroundBanner
from src.banner.forms import HomeBannerSlideForm, NewsSharesBannerForm, BackgroundForm
from src.cinema.models import Cinema, Hall, Film, MovieSession, Ticket
from src.core.models import SeoBlock, Gallery, Image, MailingTemplate, MailingCampaign
from src.page.models import MainPage, OtherPage, NewsPromotionPage, Contact
from src.users.models import CustomUser
from .tasks import send_mailing_task
import json
import operator
from functools import reduce
from collections import defaultdict
from django.views.decorators.clickjacking import xframe_options_sameorigin

def admin_stats(request):
    return render(request, 'core/adminlte/admin_stats.html')


def search_results(request):
    """
    Обрабатывает поисковый запрос и отображает найденные фильмы с пагинацией.
    """
    # 1. Получаем поисковый запрос из GET-параметра 'q'.
    #    Если его нет, query будет пустой строкой.
    query = request.GET.get('q', '')

    results = []
    # 2. Если запрос не пустой, выполняем поиск
    if query:
        # Ищем по названию ИЛИ по описанию, без учета регистра
        # Также ищем только среди фильмов, которые "Сейчас в кино" или "Скоро"
        results = Film.objects.filter(
            (Q(title__icontains=query) | Q(description__icontains=query))
        ).distinct().order_by('-id')

    # 3. Добавляем пагинацию
    paginator = Paginator(results, 12)  # 12 результатов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'films': page_obj,  # Передаем под именем 'films', чтобы переиспользовать код карточки
    }
    return render(request, 'core/user/search_results.html', context)


def live_search_films(request):
    """
    Возвращает список фильмов в формате JSON для "живого" поиска.
    """
    # Получаем поисковый запрос 'q' из GET-параметров
    query = request.GET.get('q', '')

    films_data = []

    # Если запрос не пустой, выполняем поиск
    if query:
        # Ищем 5 самых релевантных фильмов
        films = Film.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()[:5]  # Ограничиваем количество результатов

        # Формируем список словарей с нужными данными
        for film in films:
            films_data.append({
                'title': film.title,
                'url': film.get_absolute_url(),  # Предполагаем, что у вас есть этот метод
                'poster_url': film.main_image.url if film.main_image else ''
            })

    # Возвращаем данные в формате JSON
    return JsonResponse({'films': films_data})


# Главная
def admin_banner_slider(request):
    home_slides = HomeBanner.objects.all().order_by("id")
    news_slides = HomeNewsSharesBanner.objects.all().order_by("id")
    background, _ = BackgroundBanner.objects.get_or_create(defaults={'name_banner': 'background'})

    if request.method == "POST":
        action = request.POST.get("action")
        delete_id = request.POST.get("delete_id")

        # --- УДАЛЕНИЕ ---
        if delete_id:
            # Пытаемся удалить из обеих моделей
            HomeBanner.objects.filter(id=delete_id).delete()
            HomeNewsSharesBanner.objects.filter(id=delete_id).delete()
            messages.success(request, "Слайд удален.")
            return redirect("core:admin_banner_slider")

        # --- ДОБАВЛЕНИЕ ---
        if action == "add_home_slide":
            HomeBanner.objects.create(name_banner='homebanner')  # Создаем пустой слайд
            messages.success(request, "Слот для слайда добавлен.")
            return redirect("core:admin_banner_slider")

        if action == "add_news_slide":
            HomeNewsSharesBanner.objects.create(name_banner='homenewssharesbanner')
            messages.success(request, "Слот для слайда добавлен.")
            return redirect("core:admin_banner_slider")

        # --- СОХРАНЕНИЕ HOME SLIDES ---
        if action == "save_home_slides":
            speed = request.POST.get("speed", 5)
            status_is_on = 'home_status' in request.POST

            for banner in home_slides:
                # Для каждого баннера создаем свою форму с префиксом
                form = HomeBannerSlideForm(
                    request.POST,
                    request.FILES,
                    instance=banner,
                    prefix=str(banner.id)  # Префикс, чтобы поля не конфликтовали
                )
                if form.is_valid():
                    form.save()

            # Обновляем общие поля для всех
            HomeBanner.objects.update(status_banner=status_is_on, speed_banner=speed)
            messages.success(request, "Баннеры на главной сохранены.")
            return redirect("core:admin_banner_slider")

        # --- СОХРАНЕНИЕ NEWS SLIDES ---
        if action == "save_news_slides":
            status_is_on = 'news_status' in request.POST

            for banner in news_slides:
                form = NewsSharesBannerForm(
                    request.POST,
                    request.FILES,
                    instance=banner,
                    prefix=str(banner.id)
                )
                if form.is_valid():
                    form.save()

            HomeNewsSharesBanner.objects.update(status_banner=status_is_on)
            messages.success(request, "Баннеры новостей и акций сохранены.")
            return redirect("core:admin_banner_slider")

        # --- ФОН ---
        if action == "save_background":
            form = BackgroundForm(request.POST, request.FILES, instance=background)
            if form.is_valid():
                bg = form.save(commit=False)
                bg.status_banner = 'background_status' in request.POST
                bg.save()
                messages.success(request, "Фон сохранен.")
            return redirect("core:admin_banner_slider")

        if action == "delete_background":
            if background.image_banner:
                background.image_banner.delete()
            background.color = ""
            background.save()
            messages.success(request, "Фон удален.")
            return redirect("core:admin_banner_slider")

    context = {
        "home_slides": home_slides,
        "news_slides": news_slides,
        "background": background,
        "speed_choices": [3, 5, 7, 10, 15],
    }
    return render(request, "core/adminlte/admin_banner_slider.html", context)


def index(request):
    try:
        main_page = MainPage.objects.get(status=True)
    except MainPage.DoesNotExist:
        main_page = None

    seo_block = main_page.seo_block if main_page and main_page.seo_block else None

    # Добавляем фильмы для главной страницы
    today_films = Film.objects.filter(status=Film.Status.NOW_SHOWING)[:4]
    soon_films = Film.objects.filter(status=Film.Status.COMING_SOON).order_by('-id')[:4]

    context = {
        'main_page': main_page,
        'seo_block': seo_block,
        "home_slides": HomeBanner.objects.filter(status_banner=True).order_by("id"),
        "background": BackgroundBanner.objects.filter(status_banner=True).first(),
        "news_slides": HomeNewsSharesBanner.objects.filter(status_banner=True).order_by("id"),
        'today_films': today_films,
        'soon_films': soon_films,
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


    # GET — показываем форму с текущими значениями
    context = {
        'main_page': main_page,
        'seo_block': seo_block,
    }
    return render(request, 'core/adminlte/admin_home_page.html', context)


# Афиша # Скоро # Фильм из афиши
def admin_films(request):
    """
    Отображает списки фильмов и обрабатывает создание новых фильмов.
    """
    if request.method == 'POST':
        action = request.POST.get('action')

        # Создаем фильм "Сейчас в кино"
        if action == 'add_now_showing':
            new_film = Film.objects.create(title="Новый фильм (в прокате)", status=Film.Status.NOW_SHOWING)
            return redirect('core:edit_film', film_pk=new_film.pk)

        # Создаем фильм "Скоро"
        if action == 'add_coming_soon':
            new_film = Film.objects.create(title="Новый фильм (скоро)", status=Film.Status.COMING_SOON)
            return redirect('core:edit_film', film_pk=new_film.pk)

        if action == 'delete_film':
            film_id = request.POST.get('film_id')
            film_to_delete = get_object_or_404(Film, pk=film_id)
            film_to_delete.delete()


    now_showing_list = Film.objects.filter(status=Film.Status.NOW_SHOWING).order_by('-id')
    coming_soon_list = Film.objects.filter(status=Film.Status.COMING_SOON).order_by('-id')

    # --- Пагинация для блока "Сейчас в кино" ---
    paginator_now = Paginator(now_showing_list, 1)  # 1 фильмов на страницу в админке
    page_now_number = request.GET.get('page_now')
    page_obj_now = paginator_now.get_page(page_now_number)

    # --- Пагинация для блока "Скоро в прокате" ---
    paginator_soon = Paginator(coming_soon_list, 1)
    page_soon_number = request.GET.get('page_soon')
    page_obj_soon = paginator_soon.get_page(page_soon_number)

    context = {
        'now_showing_films': page_obj_now,
        'coming_soon_films': page_obj_soon,
    }
    return render(request, 'core/adminlte/admin_films.html', context)


def soon(request):
    films_list = Film.objects.filter(status=Film.Status.COMING_SOON).order_by('-id')
    paginator = Paginator(films_list, 1)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/user/soon.html', {'films': page_obj})


def poster(request):
    films_list = Film.objects.filter(status=Film.Status.NOW_SHOWING).order_by('-id')
    paginator = Paginator(films_list, 1) # 1 фильмов на страницу для пользователей
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/user/poster.html', {'films': page_obj})


def film_page(request, film_pk):
    film = get_object_or_404(Film, pk=film_pk)

    # Преобразуем ссылку YouTube для встраивания
    embed_url = ''
    if film.trailer_url:
        if 'watch?v=' in film.trailer_url:
            embed_url = film.trailer_url.replace('watch?v=', 'embed/')
        else:
            embed_url = film.trailer_url  # На случай если уже в формате embed

    context = {
        'film': film,
        'embed_url': embed_url
    }
    return render(request, 'core/user/film_page.html', context)


def edit_film(request, film_pk):
    film = get_object_or_404(Film, pk=film_pk)

    if request.method == 'POST':
        # Обновление переводимых полей для Film
        film.title_ru = request.POST.get('title_ru', '')
        film.title_en = request.POST.get('title_en', '')
        film.description_ru = request.POST.get('description_ru', '')
        film.description_en = request.POST.get('description_en', '')
        # Обновление НЕпереводимых полей
        film.trailer_url = request.POST.get('trailer_url', '')
        film.is_2d = 'is_2d' in request.POST
        film.is_3d = 'is_3d' in request.POST
        film.is_imax = 'is_imax' in request.POST


        if 'main_image' in request.FILES:
            if film.main_image: film.main_image.delete()
            film.main_image = request.FILES['main_image']

        # Обновление файлов в галерее
        if film.gallery:
            for image_obj in film.gallery.images.all():
                field_name = f"{image_obj.pk}-image"
                if field_name in request.FILES:
                    if image_obj.image: image_obj.image.delete()
                    image_obj.image = request.FILES[field_name]
                    image_obj.save()

        # Сохранение SEO-блока ---
        slug = request.POST.get("slug", "").strip()
        if slug:
            # Данные для SEO (с учетом языков)
            seo_data = {
                'title_seo_ru': request.POST.get("title_seo_ru", "").strip(),
                'title_seo_en': request.POST.get("title_seo_en", "").strip(),
                'keywords_seo_ru': request.POST.get("keywords_seo_ru", "").strip(),
                'keywords_seo_en': request.POST.get("keywords_seo_en", "").strip(),
                'description_seo_ru': request.POST.get("description_seo_ru", "").strip(),
                'description_seo_en': request.POST.get("description_seo_en", "").strip(),
            }
            if film.seo_block:
                # Обновляем существующий блок
                SeoBlock.objects.filter(pk=film.seo_block.pk).update(slug=slug, **seo_data)
            else:
                # Создаем новый
                new_seo = SeoBlock.objects.create(slug=slug, **seo_data)
                film.seo_block = new_seo
        else:  # Если slug пустой, отвязываем/удаляем SEO блок
            if film.seo_block:
                film.seo_block.delete()
            film.seo_block = None

        film.save()
        messages.success(request, f"Фильм «{film.title}» успешно сохранен.")
        return redirect('core:admin_films')

    # GET-запрос
    if not film.gallery:
        gallery = Gallery.objects.create(name_gallery=f"Film_{film.pk}_gallery")
        film.gallery = gallery
        film.save()

    gallery_images = film.gallery.images.all()

    context = {
        'film': film,
        'seo_block': film.seo_block,
        'gallery_images': gallery_images,
    }
    return render(request, 'core/adminlte/edit_film.html', context)


# Акции и скидки и новости
def admin_news(request):
    # Логика POST-запросов (создание/удаление) остается без изменений
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            NewsPromotionPage.objects.create(name="НОВАЯ НОВОСТЬ", status=True, is_promotion=False)

        if action == "delete":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(NewsPromotionPage, pk=item_id, is_promotion=False)
            item.delete()


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
    gallery_images = item.gallery_banner.images.all() if item.gallery_banner else []

    # Обработка POST-запроса
    if request.method == "POST":
        item.status = 'status' in request.POST
        item.name_ru = request.POST.get('name_ru', '').strip()
        item.name_en = request.POST.get('name_en', '').strip()
        item.description_ru = request.POST.get('description_ru', '').strip()
        item.description_en = request.POST.get('description_en', '').strip()
        item.url_movie = request.POST.get('url_movie', '').strip()
        publication_date = request.POST.get('publicationDate')
        if publication_date:
            item.time_created = publication_date


        # Главная картинка
        if 'main_image' in request.FILES:
            if item.main_image:
                item.main_image.delete()
            item.main_image = request.FILES['main_image']

        # Обновление файлов в галерее
        if item.gallery_banner:
            for image_obj in item.gallery_banner.images.all():
                field_name = f"{image_obj.pk}-image"
                if field_name in request.FILES:
                    if image_obj.image:
                        image_obj.image.delete()
                    image_obj.image = request.FILES[field_name]
                    image_obj.save()

        # SEO-блок с поддержкой переводов
        slug = request.POST.get("slug", "").strip()

        if slug:
            # Проверяем на конфликт slug'ов (логика без изменений)
            conflicting_seo = SeoBlock.objects.filter(slug=slug).exclude(
                pk=getattr(item.seo_block, 'pk', None)).first()
            if conflicting_seo:
                messages.error(request, f"URL (slug) '{slug}' уже используется. Выберите уникальный URL.")
            else:
                # Собираем все переводимые данные для SEO-блока в один словарь
                seo_data = {
                    'title_seo_ru': request.POST.get("title_seo_ru", "").strip(),
                    'title_seo_en': request.POST.get("title_seo_en", "").strip(),
                    'keywords_seo_ru': request.POST.get("keywords_seo_ru", "").strip(),
                    'keywords_seo_en': request.POST.get("keywords_seo_en", "").strip(),
                    'description_seo_ru': request.POST.get("description_seo_ru", "").strip(),
                    'description_seo_en': request.POST.get("description_seo_en", "").strip()
                }

                if item.seo_block:
                    # Если блок уже есть, обновляем его поля
                    SeoBlock.objects.filter(pk=item.seo_block.pk).update(slug=slug, **seo_data)
                else:
                    # Если блока нет, создаем новый с slug и всеми данными
                    new_seo = SeoBlock.objects.create(slug=slug, **seo_data)
                    item.seo_block = new_seo
        else:
            # Если slug пустой, удаляем SEO-блок (логика без изменений)
            if item.seo_block:
                item.seo_block.delete()
            item.seo_block = None

        item.save()
        messages.success(request, f"Запись «{item.name}» успешно сохранена.")

        # "Умный" редирект в зависимости от типа записи
        if item.is_promotion:
            return redirect('core:admin_promotion')
        else:
            return redirect('core:admin_news')

    # --- GET-запрос: просто готовим данные для отображения ---

    # Создаем галерею, если ее нет, чтобы получить ID для JS
    if not item.gallery_banner:
        gallery = Gallery.objects.create(name_gallery=f"Gallery for Item {item.pk}")
        item.gallery_banner = gallery
        item.save()

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

        if action == "delete":
            item_id = request.POST.get("item_id")
            item = get_object_or_404(NewsPromotionPage, pk=item_id, is_promotion=True)
            item.delete()


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
            page_name = page.name
            page.delete()
            messages.success(request, f"Страница '{page_name}' успешно удалена.")
            # ИСПРАВЛЕНО: Добавляем редирект
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

    if request.method == 'POST':
        action = request.POST.get('action')

        # Обработка атомарных действий
        if action == 'delete_main_image':
            if page.main_image:
                page.main_image.delete(save=True)
            messages.success(request, "Главное изображение удалено.")
            return redirect('core:edit_other_page', page_name=page.name)

        # Обновление основных полей
        page.status = 'status' in request.POST
        page.title_ru = request.POST.get('title_ru', '')
        page.title_en = request.POST.get('title_en', '')
        page.description_ru = request.POST.get('description_ru', '')
        page.description_en = request.POST.get('description_en', '')

        if 'main_image' in request.FILES:
            if page.main_image: page.main_image.delete()
            page.main_image = request.FILES['main_image']

        if page.gallery:
            for image_obj in page.gallery.images.all():
                field_name = f"{image_obj.pk}-image"
                if field_name in request.FILES:
                    if image_obj.image: image_obj.image.delete()
                    image_obj.image = request.FILES[field_name]
                    image_obj.save()


        # Обновление SEO-блока с поддержкой переводов
        slug = request.POST.get('slug', '').strip()
        if slug:
            conflicting_seo = SeoBlock.objects.filter(slug=slug).exclude(id=page.seo_block_id).first()
            if conflicting_seo:
                messages.error(request, f"URL (slug) '{slug}' уже используется другой записью.")
                # Не сохраняем, а возвращаем пользователя на страницу для исправления
                # Мы не делаем редирект, чтобы не потерять уже введенные данные
                context = {
                    'page': page,
                    'slides': page.gallery.images.all() if page.gallery else [],
                    'seo_block': page.seo_block,
                }
                return render(request, 'core/adminlte/edit_other_page.html', context)
            else:
                seo_data = {
                    'title_seo_ru': request.POST.get("title_seo_ru", "").strip(),
                    'title_seo_en': request.POST.get("title_seo_en", "").strip(),
                    'keywords_seo_ru': request.POST.get("keywords_seo_ru", "").strip(),
                    'keywords_seo_en': request.POST.get("keywords_seo_en", "").strip(),
                    'description_seo_ru': request.POST.get("description_seo_ru", "").strip(),
                    'description_seo_en': request.POST.get("description_seo_en", "").strip()
                }
                if page.seo_block:
                    SeoBlock.objects.filter(pk=page.seo_block.pk).update(slug=slug, **seo_data)
                else:
                    new_seo = SeoBlock.objects.create(slug=slug, **seo_data)
                    page.seo_block = new_seo
        elif page.seo_block:
            page.seo_block.delete()
            page.seo_block = None

        page.save()
        messages.success(request, f"Страница «{page.title}» успешно сохранена.")
        return redirect('core:edit_other_page', page_name=page.name)

        # --- Логика для галереи ---

    # GET-запрос
    if not hasattr(page, 'gallery') or not page.gallery:
        gallery = Gallery.objects.create(name_gallery=f"OtherPage_{page.pk}_gallery")
        page.gallery = gallery
        page.save()

    slides = page.gallery.images.all()

    context = {
        'page': page,
        'slides': slides,
        'seo_block': page.seo_block,
    }

    return render(request, 'core/adminlte/admin_edit_page_wrapper.html', context)


def other_page_detail(request, page_name):
    # Ищем страницу по имени и обязательно проверяем, что она активна (status=True)
    page = get_object_or_404(OtherPage, name=page_name, status=True)
    seo_block = page.seo_block
    slides = []
    if page.gallery:
        # `images` - это related_name, который мы указали в модели Image:
        # gallery = models.ForeignKey(..., related_name='images')
        slides = page.gallery.images.all()

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
    # Создаем объект Paginator. 1 - количество пользователей на странице.
    paginator = Paginator(users_list, 20)

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


    context = {
        'user_to_edit': user_to_edit,
        'success': success,
        'errors': errors,
        'gender_choices': CustomUser.GENDER_CHOICES,
        'language_choices': CustomUser.LANGUAGE_CHOICES,
        'city_choices': CustomUser.CITY_CHOICES,
    }
    return render(request, 'core/adminlte/edit_users.html', context)

# рассылка

# --- ФУНКЦИИ ДЛЯ СТРАНИЦЫ УПРАВЛЕНИЯ РАССЫЛКОЙ ---

def admin_mailing(request):
    """
    Отображает страницу управления рассылками и обрабатывает
    действия, требующие перезагрузки страницы (загрузка/удаление шаблонов).
    """
    # --- Обрабатываем только действия, которые приходят от обычных форм ---
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'upload_template':
            template_file = request.FILES.get('template_file')
            if template_file:
                template_name = template_file.name
                MailingTemplate.objects.create(name=template_name, file=template_file)
                messages.success(request, f"Шаблон '{template_name}' успешно загружен.")
            else:
                messages.error(request, "Необходимо выбрать файл для загрузки.")
            return redirect('core:admin_mailing')

        elif action == 'delete_template':
            template_id = request.POST.get('template_id')
            if template_id:
                template = get_object_or_404(MailingTemplate, id=template_id)
                template.delete()
                messages.success(request, f"Шаблон '{template.name}' удален.")
            else:
                messages.error(request, "Ошибка при удалении: не найден ID шаблона.")
            return redirect('core:admin_mailing')

    # --- Готовим данные для отображения страницы (GET-запрос) ---
    templates = MailingTemplate.objects.all()[:5]
    all_users_count = CustomUser.objects.exclude(email__exact='').count()
    last_campaign = MailingCampaign.objects.order_by('-started_at').first()

    initial_percentage = 0
    if last_campaign and last_campaign.total_recipients > 0:
        initial_percentage = round((last_campaign.sent_count / last_campaign.total_recipients) * 100)

    context = {
        'templates': templates,
        'all_users_count': all_users_count,
        'last_campaign': last_campaign,
        'initial_percentage': initial_percentage,
    }
    return render(request, 'core/adminlte/admin_mailing.html', context)


# --- API-ФУНКЦИИ ДЛЯ РАБОТЫ С JAVASCRIPT (БЕЗ ПЕРЕЗАГРУЗКИ СТРАНИЦЫ) ---

@require_POST
def start_mailing_api(request):
    if MailingCampaign.objects.filter(status=MailingCampaign.Status.IN_PROGRESS).exists():
        return JsonResponse({'status': 'error', 'message': 'Предыдущая рассылка еще не завершена.'}, status=400)

    selected_template_ids = request.POST.getlist('template_ids[]')
    if not selected_template_ids:
        return JsonResponse({'status': 'error', 'message': 'Не выбраны шаблоны для рассылки.'}, status=400)

    # ---  ОПРЕДЕЛЕНИЯ ПОЛУЧАТЕЛЕЙ ---
    send_to = request.POST.get('send_to')  # Получаем значение радио-кнопки
    send_to_all = True
    recipients_ids = []
    total_recipients = 0

    if send_to == 'all':
        send_to_all = True
        total_recipients = CustomUser.objects.exclude(email__exact='').count()
    elif send_to == 'selective':
        send_to_all = False
        # Получаем строку JSON с ID и преобразуем ее в список Python
        recipients_ids_str = request.POST.get('recipients', '[]')
        try:
            recipients_ids = json.loads(recipients_ids_str)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Некорректный формат списка получателей.'}, status=400)

        if not recipients_ids:
            return JsonResponse(
                {'status': 'error', 'message': 'Для выборочной рассылки не выбран ни один пользователь.'}, status=400)
        total_recipients = len(recipients_ids)
    else:
        return JsonResponse({'status': 'error', 'message': 'Не указан тип получателей.'}, status=400)

    # Создаем объект кампании со всеми нужными данными
    campaign = MailingCampaign.objects.create(
        total_recipients=total_recipients,
        send_to_all=send_to_all,
        recipients=recipients_ids
    )
    campaign.templates.set(selected_template_ids)

    task = send_mailing_task.delay(campaign_id=campaign.id)

    campaign.task_id = task.id
    campaign.save()

    return JsonResponse({'status': 'success', 'message': 'Рассылка запущена!', 'task_id': task.id})


def get_mailing_status_api(request):
    task_id = request.GET.get('task_id')  # <--- Получаем ID из GET-параметра

    campaign = None
    if task_id:
        # Если клиент точно знает, какую задачу искать
        try:
            campaign = MailingCampaign.objects.get(task_id=task_id)
        except MailingCampaign.DoesNotExist:
            # Если такой задачи нет, отдаем последнюю, чтобы избежать ошибки
            campaign = MailingCampaign.objects.order_by('-started_at').first()
    else:
        # Поведение по умолчанию для первоначальной загрузки страницы
        campaign = MailingCampaign.objects.order_by('-started_at').first()

    if not campaign:
        return JsonResponse({'status_code': 'no_campaign', 'message': 'Еще не было ни одной рассылки.'})

    percentage = 0
    if campaign.total_recipients > 0:
        percentage = round((campaign.sent_count / campaign.total_recipients) * 100)

    # Ограничиваем проценты сверху, на случай рассинхрона
    if percentage > 100:
        percentage = 100

    data = {
        'status_code': campaign.status,
        'status_display': campaign.get_status_display(),
        'sent': campaign.sent_count,
        'total': campaign.total_recipients,
        'percentage': percentage,
        'task_id': campaign.task_id,
        'is_running': campaign.status == MailingCampaign.Status.IN_PROGRESS,
    }
    return JsonResponse(data)

@xframe_options_sameorigin
def mailing_choice(request):
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
    # Создаем объект Paginator. 1 - количество пользователей на странице.
    paginator = Paginator(users_list, 10)

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
    return render(request, 'core/adminlte/mailing_choice.html',context)


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


        if delete_id:
            cinema_to_delete = get_object_or_404(Cinema, pk=delete_id)
            cinema_to_delete.delete()


    cinemas = Cinema.objects.all().order_by('name')
    return render(request, 'core/adminlte/admin_cinema.html', {'cinemas': cinemas})


def cinemas(request):
    cinemas = Cinema.objects.all()
    return render(request, 'core/user/cinemas.html', {'cinemas': cinemas})


def edit_cinema(request, cinema_pk):
    cinema = get_object_or_404(Cinema, pk=cinema_pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        delete_hall_id = request.POST.get('delete_hall_id')

        # --- Обработка атомарных действий ---
        if action == 'add_hall':
            Hall.objects.create(cinema=cinema, number_hall="Новый зал")
            messages.success(request, "Новый зал успешно добавлен.")
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        if delete_hall_id:
            hall_to_delete = get_object_or_404(Hall, pk=delete_hall_id, cinema=cinema)
            hall_to_delete.delete()
            messages.success(request, "Зал удален.")
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        if action == 'delete_logo':
            if cinema.logo: cinema.logo.delete(save=True)
            messages.success(request, "Логотип удален.")
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        if action == 'delete_main_image':
            if cinema.main_image: cinema.main_image.delete(save=True)
            messages.success(request, "Главный баннер удален.")
            return redirect('core:edit_cinema', cinema_pk=cinema.pk)

        # --- Если ни одно из вышеперечисленных действий не было выполнено,
        #     значит, это основное сохранение формы. ---

        cinema.name_ru = request.POST.get('name_ru', '').strip()
        cinema.name_en = request.POST.get('name_en', '').strip()
        cinema.description_ru = request.POST.get('description_ru', '').strip()
        cinema.description_en = request.POST.get('description_en', '').strip()
        cinema.conditions_ru = request.POST.get('conditions_ru', '').strip()
        cinema.conditions_en = request.POST.get('conditions_en', '').strip()

        if 'logo' in request.FILES:
            if cinema.logo: cinema.logo.delete()
            cinema.logo = request.FILES['logo']
        if 'main_image' in request.FILES:
            if cinema.main_image: cinema.main_image.delete()
            cinema.main_image = request.FILES['main_image']

        if cinema.gallery:
            for image_obj in cinema.gallery.images.all():
                field_name = f"{image_obj.pk}-image"
                if field_name in request.FILES:
                    if image_obj.image: image_obj.image.delete()
                    image_obj.image = request.FILES[field_name]
                    image_obj.save()

        slug = request.POST.get('slug', '').strip()
        if slug:
            # Ищем ДРУГОЙ SeoBlock с таким же slug
            conflicting_seo = SeoBlock.objects.filter(slug=slug).exclude(id=cinema.seo_block_id).first()
            if conflicting_seo:
                messages.error(request, f"URL (slug) '{slug}' уже используется другой записью.")
            else:
                seo_data = {
                    'title_seo_ru': request.POST.get("title_seo_ru", "").strip(),
                    'title_seo_en': request.POST.get("title_seo_en", "").strip(),
                    'keywords_seo_ru': request.POST.get("keywords_seo_ru", "").strip(),
                    'keywords_seo_en': request.POST.get("keywords_seo_en", "").strip(),
                    'description_seo_ru': request.POST.get("description_seo_ru", "").strip(),
                    'description_seo_en': request.POST.get("description_seo_en", "").strip()
                }
                if cinema.seo_block:
                    # Если блок уже есть, обновляем его
                    SeoBlock.objects.filter(pk=cinema.seo_block.pk).update(slug=slug, **seo_data)
                else:
                    # Если блока нет, создаем новый и привязываем
                    new_seo = SeoBlock.objects.create(slug=slug, **seo_data)
                    cinema.seo_block = new_seo

        elif cinema.seo_block:
            # Если slug стерли, удаляем блок
            cinema.seo_block.delete()
            cinema.seo_block = None

        # 4. Финальное сохранение объекта cinema
        cinema.save()

        messages.success(request, f"Кинотеатр «{cinema.name}» успешно сохранен.")
        return redirect('core:edit_cinema', cinema_pk=cinema.pk)

    # GET-запрос
    if not cinema.gallery:
        gallery = Gallery.objects.create(name_gallery=f"Cinema_{cinema.pk}_gallery")
        cinema.gallery = gallery
        cinema.save()

    slides = cinema.gallery.images.all()
    halls = cinema.halls.all().order_by('number_hall')

    context = {
        'cinema': cinema,
        'halls': halls,
        'slides': slides,
        'seo_block': cinema.seo_block,
    }
    return render(request, 'core/adminlte/edit_cinema.html', context)


def cinema_card(request, pk):
    cinema = get_object_or_404(Cinema, pk=pk)
    halls = cinema.halls.all()
    seo_block = cinema.seo_block

    # Находим все сеансы, которые проходят СЕГОДНЯ
    # в залах, принадлежащих ЭТОМУ кинотеатру.
    today_sessions = MovieSession.objects.filter(
        hall__cinema=cinema,
        date=date.today()
    ).select_related('film').order_by('time')  # Сортируем по времени

    context = {
        'cinema': cinema,
        'halls': halls,
        'seo_block': seo_block,
        'today_sessions': today_sessions,
    }

    return render(request, 'core/user/cinema_card.html', context)


def edit_halls(request, hall_pk):
    hall = get_object_or_404(Hall, pk=hall_pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_scheme_image':
            if hall.scheme_image: hall.scheme_image.delete(save=True)

        if action == 'delete_banner_image':
            if hall.banner_image: hall.banner_image.delete(save=True)


        # ---  ОСНОВНОЕ СОХРАНЕНИЕ ---
        hall.number_hall_ru = request.POST.get('number_hall_ru', '').strip()
        hall.number_hall_en = request.POST.get('number_hall_en', '').strip()
        hall.description_ru = request.POST.get('description_ru', '').strip()
        hall.description_en = request.POST.get('description_en', '').strip()

        if 'scheme_image' in request.FILES:
            hall.scheme_image = request.FILES['scheme_image']
        if 'banner_image' in request.FILES:
            hall.banner_image = request.FILES['banner_image']

        # --- Обновление файлов в галерее ---
        if hall.gallery:
            for image_obj in hall.gallery.images.all():
                field_name = f"{image_obj.pk}-image"
                if field_name in request.FILES:
                    # Если у слайда уже была картинка, удаляем старую
                    if image_obj.image:
                        image_obj.image.delete(save=False)  # save=False, так как сохраним ниже

                    # Присваиваем новый файл
                    image_obj.image = request.FILES[field_name]
                    image_obj.save()  # Сохраняем сам объект Image

        slug = request.POST.get('slug', '').strip()
        if slug:
            # Ищем другой SeoBlock с таким же slug, который НЕ принадлежит текущему залу
            conflicting_seo = SeoBlock.objects.filter(slug=slug).exclude(id=hall.seo_block_id).first()

            if conflicting_seo:
                # Если такой блок найден - выдаем ошибку и не сохраняем
                messages.error(request,
                               f"URL (slug) '{slug}' уже используется другой записью. Пожалуйста, выберите уникальный URL.")
            else:
                seo_data = {
                    'title_seo_ru': request.POST.get("title_seo_ru", "").strip(),
                    'title_seo_en': request.POST.get("title_seo_en", "").strip(),
                    'keywords_seo_ru': request.POST.get("keywords_seo_ru", "").strip(),
                    'keywords_seo_en': request.POST.get("keywords_seo_en", "").strip(),
                    'description_seo_ru': request.POST.get("description_seo_ru", "").strip(),
                    'description_seo_en': request.POST.get("description_seo_en", "").strip()
                }
                if hall.seo_block:
                    # Если у зала уже был SEO блок, обновляем его
                    SeoBlock.objects.filter(pk=hall.seo_block.pk).update(slug=slug, **seo_data)
                else:
                    # Если блока не было, создаем новый
                    new_seo = SeoBlock.objects.create(slug=slug, **seo_data)
                    hall.seo_block = new_seo  # Привязываем к залу


        elif hall.seo_block:
            # Если slug стерли, удаляем связанный блок
            hall.seo_block.delete()
            hall.seo_block = None

        # Сохраняем hall в самом конце
        hall.save()
        messages.success(request, f"Зал «{hall.number_hall}» успешно сохранен.")
        return redirect('core:edit_hall', hall_pk=hall.pk)

    # GET-запрос
    if not hall.gallery:
        gallery = Gallery.objects.create(name_gallery=f"Hall_{hall.pk}_gallery")
        hall.gallery = gallery
        hall.save()

    slides = hall.gallery.images.all()
    context = {
        'hall': hall,
        'slides': slides,
        'seo_block': hall.seo_block,
    }
    return render(request, 'core/adminlte/edit_halls.html', context)


def card_hall(request, pk):
    """
    Отображает детальную страницу одного зала.
    """
    hall = get_object_or_404(Hall, pk=pk)
    sibling_halls = hall.cinema.halls.all().order_by('number_hall')

    # Находим все сеансы, которые проходят СЕГОДНЯ
    # именно в ЭТОМ зале.
    today_sessions = MovieSession.objects.filter(
        hall=hall,
        date=date.today()
    ).select_related('film').order_by('time')  # Сортируем по времени

    context = {
        'hall': hall,
        'cinema': hall.cinema,
        'halls': sibling_halls,
        'seo_block': hall.seo_block,
        'today_sessions': today_sessions,
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


# Расписание
def schedule(request):
    f_is_3d = request.GET.get('is_3d')
    f_is_dbox = request.GET.get('is_dbox')
    f_is_vip = request.GET.get('is_vip')
    f_cinema_id = request.GET.get('cinema')
    f_date_str = request.GET.get('date')
    f_film_id = request.GET.get('film')
    f_hall_id = request.GET.get('hall')

    # 1. Получаем диапазон дат: от сегодня на 7 дней вперед
    today = date.today()
    end_date = today + timedelta(days=6)  # 7 дней, включая сегодняшний

    # 2. Фильтруем все сеансы, которые попадают в наш недельный диапазон
    sessions_qs = MovieSession.objects.filter(date__gte=date.today()).select_related('film', 'hall', 'hall__cinema')

    # --- 3. Применяем фильтры, если они были переданы ---
    if f_is_3d == 'on':
        sessions_qs = sessions_qs.filter(is_3d=True)

    if f_is_dbox == 'on':
        sessions_qs = sessions_qs.filter(is_dbox=True)

    if f_is_vip == 'on':
        sessions_qs = sessions_qs.filter(is_vip=True)

    if f_cinema_id:
        sessions_qs = sessions_qs.filter(hall__cinema__id=f_cinema_id)

    if f_film_id:
        sessions_qs = sessions_qs.filter(film__id=f_film_id)

    if f_hall_id:
        sessions_qs = sessions_qs.filter(hall__id=f_hall_id)

    # Фильтр по дате особенный: если дата выбрана, показываем только ее.
    # Если нет - показываем 7 дней.
    if f_date_str:
        try:
            selected_date = datetime.strptime(f_date_str, '%Y-%m-%d').date()
            sessions_qs = sessions_qs.filter(date=selected_date)
            end_date = selected_date
        except ValueError:
            # Если передана некорректная дата, просто игнорируем фильтр
            end_date = date.today() + timedelta(days=6)
    else:
        # Если дата не выбрана, показываем расписание на неделю
        end_date = date.today() + timedelta(days=6)
        sessions_qs = sessions_qs.filter(date__lte=end_date)

    # 4. Группируем сеансы по датам
    sessions_by_date = defaultdict(list)
    for session in sessions_qs:
        sessions_by_date[session.date].append(session)

    # Преобразуем в обычный dict для шаблона, отсортировав по дате
    sorted_sessions_by_date = dict(sorted(sessions_by_date.items()))

    # 5. Получаем данные для выпадающих списков в фильтрах
    context = {
        'sessions_by_date': sorted_sessions_by_date,
        'cinemas': Cinema.objects.all(),
        'films': Film.objects.filter(status=Film.Status.NOW_SHOWING),
        'halls': Hall.objects.select_related('cinema').all(),
        'dates': [today + timedelta(days=i) for i in range(7)],  # Генерируем список дат для фильтра
        'request': request,
    }
    return render(request, 'core/user/schedule.html', context)


# Бронь билетов
def ticket_reservation(request, session_id):
    """
    Эта view теперь только отображает начальное состояние страницы.
    Вся динамика обрабатывается через API.
    """
    session = get_object_or_404(MovieSession, id=session_id)

    # Получаем начальный список занятых мест
    booked_tickets = Ticket.objects.filter(session=session)
    booked_seats = [f"{ticket.row}-{ticket.seat}" for ticket in booked_tickets]

    hall_layout = {'rows': range(1, 11), 'seats': range(1, 11)}
    BOOKING_FEE = 3

    user_ticket_count = 0
    user_total_spent = 0
    if request.user.is_authenticated:
        user_tickets = booked_tickets.filter(user=request.user)
        user_ticket_count = user_tickets.count()
        user_total_spent = sum(ticket.price for ticket in user_tickets)

    context = {
        'session': session,
        'hall_layout': hall_layout,
        'initial_booked_seats': json.dumps(booked_seats),  # Передаем только начальное состояние
        'booking_fee': BOOKING_FEE,
        'user_ticket_count': user_ticket_count,
        'user_total_spent': user_total_spent,
    }
    return render(request, 'core/user/ticket_reservation.html', context)


def get_session_seats_api(request, session_id):
    """
    Возвращает список всех занятых мест для данного сеанса в формате JSON.
    """
    session = get_object_or_404(MovieSession, id=session_id)
    booked_tickets = Ticket.objects.filter(session=session)
    booked_seats = [f"{ticket.row}-{ticket.seat}" for ticket in booked_tickets]
    return JsonResponse({'booked_seats': booked_seats})


@login_required
@require_POST
def process_booking_api(request, session_id):
    """
    Обрабатывает AJAX-запрос на бронирование или покупку билетов.
    """
    session = get_object_or_404(MovieSession, id=session_id)
    BOOKING_FEE = 3

    try:
        data = json.loads(request.body)
        selected_seats = data.get('selected_seats', [])
        action = data.get('action')

        if not selected_seats or not action:
            return JsonResponse({'status': 'error', 'message': 'Некорректные данные запроса.'}, status=400)

        if action == 'book':
            ticket_status = Ticket.Status.BOOKED
            price_per_ticket = BOOKING_FEE
        elif action == 'buy':
            ticket_status = Ticket.Status.PAID
            price_per_ticket = session.price
        else:
            return JsonResponse({'status': 'error', 'message': 'Неизвестное действие.'}, status=400)

        with transaction.atomic():
            # Проверяем, не заняты ли места
            seat_queries = [Q(row=s.split('-')[0], seat=s.split('-')[1]) for s in selected_seats]
            combined_query = reduce(operator.or_, seat_queries)
            if Ticket.objects.filter(session=session).filter(combined_query).exists():
                return JsonResponse({'status': 'error', 'message': 'Извините, одно или несколько мест уже заняты. Обновите страницу.'}, status=409) # 409 Conflict

            # Создаем билеты
            tickets_to_create = [
                Ticket(session=session, user=request.user, row=int(s.split('-')[0]), seat=int(s.split('-')[1]), status=ticket_status, price=price_per_ticket)
                for s in selected_seats
            ]
            Ticket.objects.bulk_create(tickets_to_create)

        return JsonResponse({'status': 'success', 'message': f'Успешно! Билетов: {len(selected_seats)}.'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Ошибка формата данных.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Произошла внутренняя ошибка сервера: {e}'}, status=500)


# --- API VIEWS ДЛЯ УПРАВЛЕНИЯ ГАЛЕРЕЯМИ (AJAX) ---

@require_POST
@user_passes_test(is_superuser)
def gallery_add_slide(request):
    """
    Создает новый пустой слайд (объект Image) для указанной галереи.
    """
    gallery_id = request.POST.get('gallery_id')
    if not gallery_id:
        return JsonResponse({'status': 'error', 'message': 'Gallery ID не указан.'}, status=400)

    try:
        gallery = Gallery.objects.get(id=gallery_id)
        # Создаем новый объект Image, связанный с этой галереей
        new_image = Image.objects.create(gallery=gallery)
        # Возвращаем данные нового слайда, чтобы JS мог его отрисовать
        return JsonResponse({
            'status': 'success',
            'slide': {
                'id': new_image.id,
                'image_url': '',  # URL пока пустой
            }
        })
    except Gallery.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Галерея не найдена.'}, status=404)


@require_POST
@user_passes_test(is_superuser)
def gallery_delete_slide(request):
    """
    Удаляет слайд (объект Image) по его ID.
    """
    slide_id = request.POST.get('slide_id')
    if not slide_id:
        return JsonResponse({'status': 'error', 'message': 'Slide ID не указан.'}, status=400)

    try:
        image_to_delete = Image.objects.get(id=slide_id)
        image_to_delete.delete()  # Django позаботится об удалении файла
        return JsonResponse({'status': 'success', 'message': 'Слайд удален.'})
    except Image.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Слайд не найден.'}, status=404)

