from django.urls import path
from . import views


app_name = 'core'

urlpatterns = [

#---ADMIN PAGE---
    path('adminlte/', views.admin_stats, name='admin_stats'),
    path("adminlte/admin_banner_slider", views.admin_banner_slider, name="admin_banner_slider"),

    path('adminlte/films', views.admin_films, name='admin_films'),
    path('adminlte/films/edit/<int:film_pk>/', views.edit_film, name='edit_film'),
    path('', views.index, name='home'),
    path('soon/', views.soon, name='soon'),
    path('poster/', views.poster, name='poster'),
    path('film/<int:film_pk>/', views.film_page, name='film_page'),
    path('search/', views.search_results, name='search_results'),
    path('api/search-films/', views.live_search_films, name='live_search_films'),


    path('adminlte/admin_news', views.admin_news, name='admin_news'),
    path('adminlte/edit_news', views.edit_news, name='edit_news'),
    path("adminlte/admin_news/", views.admin_news, name="admin_news"),
    path("adminlte/admin_news/<int:pk>/edit/", views.edit_news, name="edit_news"),
    path('adminlte/admin_promotion', views.admin_promotion, name='admin_promotion'),


    path('adminlte/pages', views.admin_other_page, name='admin_other_page'),
    path('admin/pages/edit/<str:page_name>/', views.edit_other_page, name='edit_other_page'),
    path('adminlte/home_page', views.admin_home_page, name='admin_home_page'),
    path('adminlte/contacts', views.admin_contacts_page, name='admin_contacts_page'),



    path('adminlte/users/', views.admin_users, name='admin_users'),
    path('adminlte/users/edit/<int:user_pk>/', views.edit_users, name='edit_user'),



    path('adminlte/mailing/', views.admin_mailing, name='admin_mailing'),
    path('adminlte/mailing/choice/', views.mailing_choice, name='mailing_choice'),
    # НОВЫЕ МАРШРУТЫ ДЛЯ AJAX
    path('api/mailing/start/', views.start_mailing_api, name='start_mailing_api'),
    path('api/mailing/status/', views.get_mailing_status_api, name='get_mailing_status_api'),

#---PAGE---



    path('schedule/', views.schedule, name='schedule'),
    path('ticket_reservation/<int:session_id>/', views.ticket_reservation, name='ticket_reservation'),


    path('stocks', views.stocks, name='stocks'),
    path('stock/<int:pk>/', views.stocks_card, name='stock_card'),
    path('news', views.news, name='news'),


    path('page/<str:page_name>/', views.other_page_detail, name='other_page_detail'),

    path('contacts', views.contacts, name='contacts'),



    # --- Админ-панель ---
    path('adminlte/admin_cinema', views.admin_cinema, name='admin_cinema'),
    path('adminlte/edit_cinema/<int:cinema_pk>/', views.edit_cinema, name='edit_cinema'),
    path('adminlte/edit_halls/<int:hall_pk>/', views.edit_halls, name='edit_hall'),
    # --- Пользовательская часть (эти URL у вас уже правильные) ---
    path('cinemas/', views.cinemas, name='cinemas'),
    path('cinemas/<int:pk>/', views.cinema_card, name='cinema_card'),
    path('halls/<int:pk>/', views.card_hall, name='card_hall'),

]