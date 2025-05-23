# Generated by Django 5.2 on 2025-04-25 15:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_alter_userprofile_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='auth_provider',
            field=models.CharField(choices=[('local', 'Локальная'), ('google', 'Google')], default='local', help_text='Через что зарегистрирован пользователь: локально или через Google', max_length=32, verbose_name='Способ регистрации'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, default=None, error_messages={'unique': 'Пользователь с таким номером телефона уже существует.'}, help_text='Формат: 89991234567', max_length=15, null=True, unique=True, validators=[django.core.validators.RegexValidator(message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр.", regex='^\\+?1?\\d{9,15}$')]),
        ),
    ]
