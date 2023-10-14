# Generated by Django 4.2.3 on 2023-10-10 13:16

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataSyncStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('source', models.CharField(blank=True, choices=[('notion', 'notion')], null=True)),
                ('is_running', models.BooleanField(default=False)),
                ('last_sync_datetime', models.DateTimeField(blank=True, default=None, null=True)),
                ('cur_page_count', models.IntegerField(blank=True, default=None, null=True)),
                ('total_page_count', models.IntegerField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='OriginalDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_delete', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(null=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('url', models.CharField(blank=True, default=None, max_length=500, null=True)),
                ('title', models.TextField(blank=True, default='')),
                ('text', models.TextField(blank=True, default='')),
                ('text_hash', models.TextField(blank=True, default='')),
                ('source', models.CharField(blank=True, choices=[('notion', 'notion')], null=True)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
    ]