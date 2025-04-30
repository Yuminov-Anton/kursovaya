from .models import UserProfile

def set_auth_provider_google(backend, user, *args, **kwargs):
    if backend.name == 'google-oauth2':
        profile, created = UserProfile.objects.get_or_create(user=user)
        if profile.auth_provider != 'google':
            profile.auth_provider = 'google'
            profile.save()