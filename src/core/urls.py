from django.urls import path
from . import views


app_name = 'core'

urlpatterns = [

#---ADMIN PAGE---
    path('adminlte/', views.admin_stats, name='admin_stats'),
    path("adminlte/admin_banner_slider", views.admin_banner_slider, name="admin_banner_slider"),
    path('adminlte/admin_films', views.admin_films, name='admin_films'),
    path('adminlte/admin_cinema', views.admin_cinema, name='admin_cinema'),

    path('adminlte/admin_news', views.admin_news, name='admin_news'),
    path('adminlte/edit_news', views.edit_news, name='edit_news'),
    path("adminlte/admin_news/", views.admin_news, name="admin_news"),
    path("adminlte/admin_news/<int:pk>/edit/", views.edit_news, name="edit_news"),

    path('adminlte/admin_promotion', views.admin_promotion, name='admin_promotion'),

    path("adminlte/edit/<str:page_name>/", views.edit_other_page, name="edit_other_page"),
    path('adminlte/admin_other_page', views.admin_other_page, name='admin_other_page'),
    path('adminlte/admin_home_page', views.admin_home_page, name='admin_home_page'),
    path('adminlte/admin_about_cinema_page', views.admin_about_cinema_page, name='admin_about_cinema_page'),
    path('adminlte/admin_cafe_page', views.admin_cafe_page, name='admin_cafe_page'),
    path("adminlte/admin_vip_hall_page", views.admin_vip_hall_page, name="admin_vip_hall_page"),
    path("adminlte/admin_advertising_page", views.admin_advertising_page, name="admin_advertising_page"),
    path('adminlte/admin_child_room_page', views.admin_child_room_page, name='admin_child_room_page'),
    path('adminlte/admin_contacts_page', views.admin_contacts_page, name='admin_contacts_page'),
    path('adminlte/admin_users_page', views.admin_users_page, name='admin_users_page'),



    path('adminlte/admin_users', views.admin_users, name='admin_users'),
    path('adminlte/admin_mailing', views.admin_mailing, name='admin_mailing'),

#---PAGE---
    path('', views.index, name='home'),


    path('poster', views.poster, name='poster'),
    path('film_page', views.film_page, name='film_page'),


    path('schedule', views.schedule, name='schedule'),
    path('ticket_reservation', views.ticket_reservation, name='ticket_reservation'),


    path('soon', views.soon, name='soon'),


    path('cinemas', views.cinemas, name='cinemas'),
    path('cinema_card', views.cinema_card, name='cinema_card'),
    path('card_hall', views.card_hall, name='card_hall'),


    path('stocks', views.stocks, name='stocks'),
    path('stock/<int:pk>/', views.stocks_card, name='stock_card'),


    path('about_cinema', views.about_cinema, name='about_cinema'),
    path('news', views.news, name='news'),
    path('advertising', views.advertising, name='advertising'),
    path('vip_hall', views.vip_hall, name='vip_hall'),
    path('cafe', views.cafe, name='cafe'),
    path('mob_app', views.mob_app, name='mob_app'),
    path('contacts', views.contacts, name='contacts'),

]