"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('social_django.urls', namespace='social')),
    path('', views.main, name='main'),
    path('account/', views.account_view, name='account'),
    path('account/change_password/', views.PasswordChangeView, name='change_password'),
    path('account/edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('logout/', views.LogoutView, name='logout'),
    path('order/<int:pk>', views.order, name='order'),
    path('service/<int:pk>/', views.service_detail, name='service_detail'),
    path('ajax/get_time_slots/', views.ajax_get_time_slots, name='ajax_get_time_slots'),
    path('support/chat/history/', views.support_chat_history, name='support_chat_history'),
    path('support/chat/send/', views.support_chat_send, name='support_chat_send'),
    path('support/operator/', views.support_operator_dashboard, name='support_operator_dashboard'),
    path('support/operator/chat/<str:chat_id>/', views.support_operator_chat, name='support_operator_chat'),
]