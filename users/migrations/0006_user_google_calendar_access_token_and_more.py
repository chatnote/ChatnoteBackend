# Generated by Django 4.2.3 on 2023-11-23 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_google_drive_access_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='google_calendar_access_token',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='google_calendar_email',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='google_calendar_google_user_id',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='google_calendar_refresh_token',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]