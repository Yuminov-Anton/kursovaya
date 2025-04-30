
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Service, ServiceVariant, Order, SupportMessage

class ServiceVariantInline(admin.TabularInline):
    model = ServiceVariant
    extra = 1
    verbose_name = "Вид услуги"
    verbose_name_plural = "Виды услуги"

# --- Service ---
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'master', 'duration', 'is_active')
    list_filter = ('is_active', 'master')
    search_fields = ('name', 'master')
    ordering = ('name',)
    inlines = [ServiceVariantInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active'),
            'description': 'Основная информация об услуге'
        }),
        ('Детали услуги', {
            'fields': ('duration', 'master'),
            'description': 'Длительность и мастер услуги'
        }),
    )
    actions = ['make_active', 'make_inactive']

    @admin.action(description="Сделать выбранные услуги активными")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Сделать выбранные услуги неактивными")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    class Media:
        css = {
            'all': ('admin/custom_admin.css',)
        }

# --- UserProfile Inline для User ---
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Профиль пользователя'
    fk_name = 'user'
    ordering_field = None  # Для совместимости с Unfold

# --- Кастомный UserAdmin ---
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_phone_number', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'userprofile__phone_number')

    def get_phone_number(self, obj):
        return obj.userprofile.phone_number if hasattr(obj, 'userprofile') else '-'
    get_phone_number.short_description = 'Телефон'

# Перерегистрируем User с кастомным админом
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# --- UserProfile отдельная админка ---
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'auth_provider')
    search_fields = ('user__username', 'user__email', 'phone_number')
    list_filter = ('auth_provider', 'user__date_joined')
    verbose_name = "Профиль пользователя"
    verbose_name_plural = "Профили пользователей"

# --- Кастомизация заголовков админки ---
admin.site.site_header = "Gracefully Beauty — Администрирование"
admin.site.site_title = "Gracefully Beauty — Админ"
admin.site.index_title = "Панель управления Gracefully Beauty"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'service', 'variant', 'date', 'time', 'status', 'created_at')
    list_editable = ('status',)  # Теперь статус можно менять прямо в списке!
    list_filter = ('status', 'service', 'date')
    search_fields = ('client__user__username', 'client__phone_number', 'service__name')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('client', 'service', 'variant', 'date', 'time', 'status'),
            'description': 'Информация о заказе'
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'description': 'Дата и время создания заказа'
        }),
    )
    readonly_fields = ('created_at',)
    verbose_name = "Заказ"
    verbose_name_plural = "Заказы"

@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email', 'is_from_support', 'created_at', 'text')
    list_filter = ('is_from_support', 'created_at', 'user')
    search_fields = ('email', 'text')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    