# Generated by Django 2.2.16 on 2022-06-25 09:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('titles', '0002_title_rating'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='title',
            name='rating',
        ),
    ]
