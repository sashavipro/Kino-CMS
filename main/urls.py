from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
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
    path('stocks_card', views.stocks_card, name='stocks_card'),


    path('about_cinema', views.about_cinema, name='about_cinema'),
    path('news', views.news, name='news'),
    path('advertising', views.advertising, name='advertising'),
    path('cafe', views.cafe, name='cafe'),
    path('mob_app', views.mob_app, name='mob_app'),
    path('contacts', views.contacts, name='contacts'),
    path('vip_hall', views.vip_hall, name='vip_hall'),




    #---USER---
    path('login/', views.login_view, name='login'),
    path('registrarion/', views.registrarion_view, name='registration'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
