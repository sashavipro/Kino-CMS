from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import CustomUser
import re  # Импортируем модуль для регулярных выражений


# ----USERS-----
def registrarion_view(request):
    errors = []
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Валидация
        if not all([username, email, password, password2]):
            errors.append('Все поля обязательны для заполнения.')
        if password != password2:
            errors.append('Пароли не совпадают.')
        if CustomUser.objects.filter(username=username).exists():
            errors.append('Пользователь с таким псевдонимом уже существует.')
        if CustomUser.objects.filter(email=email).exists():
            errors.append('Пользователь с таким email уже существует.')

        if not errors:
            user = CustomUser.objects.create_user(email=email, username=username, password=password)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('users:profile')

    return render(request, 'users/auth/registration.html', {'errors': errors})


def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('users:profile')
        else:
            error = 'Неверный логин или пароль.'

    return render(request, 'users/auth/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('core:home')


@login_required
def profile_view(request):
    user = request.user
    success = False
    errors = []

    if request.method == 'POST':
        # Обновление данных пользователя
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.username = request.POST.get('username', user.username)
        user.address = request.POST.get('address', user.address)
        user.city = request.POST.get('city', user.city)
        user.birthday = request.POST.get('birthday') or None
        user.card_number = request.POST.get('card_number', user.card_number)
        user.gender = request.POST.get('gender', user.gender)
        user.language = request.POST.get('language', user.language)

        # Валидация и обновление E-mail
        email = request.POST.get('email')
        if email and email != user.email:
            if CustomUser.objects.filter(email=email).exclude(pk=user.pk).exists():
                errors.append('Этот email уже используется.')
            else:
                user.email = email

        # Валидация и обновление телефона
        phone = request.POST.get('phone')
        phone_regex = r'^\+?1?\d{9,15}$'
        if phone and not re.match(phone_regex, phone):
            errors.append('Введите корректный номер телефона.')
        else:
            user.phone = phone

        # Обновление пароля
        password = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password or password2:
            if password == password2:
                user.set_password(password)
            else:
                errors.append('Пароли не совпадают.')

        if not errors:
            user.clean()  # Очистка полей перед сохранением
            user.save()
            success = True

    # Передаем в шаблон варианты выбора для рендеринга
    context = {
        'user': user,
        'success': success,
        'errors': errors,
        'gender_choices': CustomUser.GENDER_CHOICES,
        'language_choices': CustomUser.LANGUAGE_CHOICES,
        'city_choices': CustomUser.CITY_CHOICES,
    }
    return render(request, 'users/auth/profile.html', context)