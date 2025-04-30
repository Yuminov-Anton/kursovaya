from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переопределяем стандартные сообщения об ошибках
        self.fields['username'].error_messages = {
            'unique': 'Пользователь с таким именем уже существует.',
            'invalid': 'Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_',
            'required': 'Это поле обязательно для заполнения.',
        }
        
        self.fields['email'].error_messages = {
            'invalid': 'Введите корректный email адрес.',
            'required': 'Это поле обязательно для заполнения.',
        }
        
        self.fields['password1'].error_messages = {
            'required': 'Это поле обязательно для заполнения.',
        }
        
        self.fields['password2'].error_messages = {
            'required': 'Это поле обязательно для заполнения.',
        }

        # Переопределяем сообщения валидации паролей
        self.error_messages['password_mismatch'] = 'Введенные пароли не совпадают.'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if UserProfile.objects.filter(phone_number=phone_number).exists():
            raise ValidationError('Пользователь с таким номером телефона уже существует.')
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Введенные пароли не совпадают.')

        return cleaned_data

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите имя пользователя',
            'class': 'form-control'
        }),
        error_messages={
            'required': 'Пожалуйста, введите имя пользователя',
        }
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Введите пароль',
            'class': 'form-control'
        }),
        error_messages={
            'required': 'Пожалуйста, введите пароль',
        }
    )

    error_messages = {
        'invalid_login': 'Неверное имя пользователя или пароль.',
        'inactive': 'Этот аккаунт неактивен.',
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login'
                )
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

class UserChangeForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Электронная почта")
    phone_number = forms.CharField(max_length=15, required=False, label="Телефон")

    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        # Подставляем телефон из профиля
        if self.user:
            try:
                profile = UserProfile.objects.get(user=self.user)
                self.fields['phone_number'].initial = profile.phone_number
            except UserProfile.DoesNotExist:
                pass

        self.fields['username'].error_messages = {
            'unique': 'Пользователь с таким именем уже существует.',
            'invalid': 'Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_',
            'required': 'Это п��ле обязательно для заполнения.',
        }
        self.fields['email'].error_messages = {
            'invalid': 'Введите корректный email адрес.',
            'required': 'Это поле обязательно для заполнения.',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise ValidationError('Поле "Телефон" обязательно для заполнения.')
        qs = UserProfile.objects.filter(phone_number=phone_number).exclude(user=self.instance)
        if qs.exists():
            raise ValidationError('Пользовате��ь с таким номером телефона уже существует.')
        return phone_number

    def save(self, commit=True):
        user = super().save(commit)
        phone_number = self.cleaned_data.get('phone_number')
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = phone_number
        profile.save()
        return user