from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр."
    )

    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        null=True,  # Разрешаем NULL для существующих записей
        blank=True,  # Разрешаем пустые значения в формах
        default=None,  # Значение по умолчанию NULL
        help_text="Формат: 89991234567",
        error_messages={
            'unique': 'Пользователь с таким номером телефона уже существует.'
        }
    )

    # Новое поле для хранения способа регистрации
    AUTH_PROVIDER_CHOICES = [
        ('local', 'Локальная'),
        ('google', 'Google'),
    ]
    auth_provider = models.CharField(
        max_length=32,
        choices=AUTH_PROVIDER_CHOICES,
        default='local',
        verbose_name='Способ регистрации',
        help_text='Через что зарегистрирован пользователь: локально или через Google'
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

    def clean(self):
        # Проверяем уникальность профиля для пользователя только при создании
        if not self.pk and UserProfile.objects.filter(user=self.user).exists():
            raise ValidationError({
                'user': f'Профиль для пользователя {self.user.username} уже существует.'
            })
        # Не требуем phone_number на уровне модели, если он уже проверяется в форме
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Service(models.Model):
    name = models.CharField("Название услуги", max_length=100)
    description = models.TextField("Описание", blank=True)
    duration = models.CharField("Длительность", max_length=50)
    master = models.CharField("Мастер", max_length=100)
    details = models.TextField("Детали/Виды услуги", blank=True)
    is_active = models.BooleanField("Активна", default=True)

    def __str__(self):
        return self.name

class ServiceVariant(models.Model):
    service = models.ForeignKey(Service, related_name='variants', on_delete=models.CASCADE, verbose_name="Услуга")
    variant_name = models.CharField("Вид услуги", max_length=100)
    price = models.DecimalField("Цена", max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.service.name} — {self.variant_name} ({self.price} ₽)"
    
class Order(models.Model):
    client = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='orders')
    variant = models.ForeignKey(ServiceVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    date = models.DateField()
    time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=32,
        choices=[
            ('pending', 'В обработке'),
            ('confirmed', 'Подтверждён'),
            ('completed', 'Выполнен'),
            ('cancelled', 'Отменён'),
        ],
        default='pending'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        unique_together = ('service', 'date', 'time', 'service')  # Защита от дублей по услуге, дате, времени и мастеру

    def __str__(self):
        return f"{self.client} - {self.service} ({self.date} {self.time})"
    
class SupportMessage(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Пользователь")
    email = models.EmailField("Почта", blank=True)
    text = models.TextField("Сообщение")
    is_from_support = models.BooleanField("От поддержки", default=False)
    created_at = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Сообщения поддержки"
        ordering = ['created_at']

    def __str__(self):
        who = "Поддержка" if self.is_from_support else (self.user.username if self.user else self.email)
        return f"{who}: {self.text[:30]}"