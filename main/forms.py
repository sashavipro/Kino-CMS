from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.core.validators import RegexValidator

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        max_length=60,
        widget=forms.EmailInput(attrs={'class': 'input-register form-control',
                                       'placeholder': 'Your email'})
    )

    username = forms.CharField(
        required=True,
        max_length=60,
        widget=forms.TextInput(attrs={'class': 'input-register form-control',
                                      'placeholder': 'Your username'})
    )

    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'input-register form-control',
                                          'placeholder': 'Your password'})
    )

    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'input-register form-control',
                                          'placeholder': 'Confirm your password'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

        def clean_email(self):
            email = self.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('This email is already in use.')

        def save(self, commit=True):
            user = super().save(commit=False)
            user.username = None
            if commit:
                user.save()
            return user


class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='username',
        widget=forms.TextInput(attrs={'autofocus': True,
                                      'class': 'input-register form-control',
                                      'placeholder': 'Your username'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'input-register form-control',
                                          'placeholder': 'Your password'})
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Invalid email or password.')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('This account is inactive.')
        return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Enter a valid phone number.")],
        widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Your phone'})
    )

    email = forms.EmailField(
        required=False,
        max_length=60,
        widget=forms.EmailInput(attrs={'class': 'input-register form-control', 'placeholder': 'Your email'})
    )

    username = forms.CharField(
        label='username',
        widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Your username'})
    )

    password1 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'input-register form-control', 'placeholder': 'Your password'})
    )

    password2 = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            attrs={'class': 'input-register form-control', 'placeholder': 'Confirm your password'})
    )

    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=False
    )

    language = forms.ChoiceField(
        choices=User.LANGUAGE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=False
    )

    city = forms.ChoiceField(
        choices=User.CITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'address', 'city', 'birthday',
                  'card_number', 'gender', 'language')

        widgets = {
            'email': forms.EmailInput(
                attrs={'class': 'input-register form-control', 'placeholder': 'Your email'}),

            'city': forms.Select(
                attrs={'class': 'form-select'}),

            'birthday': forms.DateInput(
                attrs={'type': 'date', 'class': 'input-register form-control'}),

            'gender': forms.RadioSelect(
                choices=User.GENDER_CHOICES, attrs={'class': 'form-check-input'}),

            'language': forms.RadioSelect(
                choices=User.LANGUAGE_CHOICES, attrs={'class': 'form-check-input'}),

            'first_name': forms.TextInput(
                attrs={'class': 'input-register form-control', 'placeholder': 'Your first name'}),

            'last_name': forms.TextInput(
                attrs={'class': 'input-register form-control', 'placeholder': 'Your last name'}),

            'username': forms.TextInput(
                attrs={'class': 'input-register form-control', 'placeholder': 'Your username'}),

            'phone': forms.TextInput(
                attrs={'class': 'input-register form-control', 'placeholder': 'Your phone'}),

            'address': forms.TextInput(
                attrs={'class': 'input-register form-control', 'placeholder': 'Your address'}),

            'card_number': forms.TextInput(
                attrs={'class': 'input-register form-control', 'placeholder': 'Your card number'}),

        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('This email is already in use.')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('email'):
            cleaned_data['email'] = self.instance.email

            for field in ['first_name', 'last_name', 'address', 'card_number', 'language', 'gender', 'phone',
                          'birthday', 'city']:
                if cleaned_data.get(field):
                    cleaned_data[field] = strip_tags(cleaned_data[field])
                return cleaned_data
