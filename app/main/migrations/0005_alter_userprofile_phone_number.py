# Generated by Django 5.2 on 2025-04-09 18:00

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_alter_userprofile_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, error_messages={'unique': 'Пользователь с таким номером телефона уже существует.'}, help_text='Формат: +79991234567', max_length=15, null=True, unique=True, validators=[django.core.validators.RegexValidator(message="Номер телефона должен быть в формате: '+999999999'. До 15 цифр.", regex='^\\+?1?\\d{9,15}$')]),
        ),
    ]
