from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # По умолчанию считаем регистрацию локальной
        auth_provider = 'local'
        # Если есть связь с social-auth (Google), меняем на google
        if hasattr(instance, 'social_auth') and instance.social_auth.filter(provider='google-oauth2').exists():
            auth_provider = 'google'
        UserProfile.objects.create(user=instance, auth_provider=auth_provider)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Безопасно: создаём профиль, если его нет
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    profile.save()