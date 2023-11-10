# Generated by Django 4.2.3 on 2023-11-10 01:37

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sources', '0007_notionpage_deleted_at_notionpage_is_delete'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('source', models.CharField(blank=True, choices=[('notion', 'notion'), ('google_calendar', 'google_calendar'), ('gmail', 'gmail'), ('google_drive', 'google_drive')], null=True)),
                ('name', models.CharField(blank=True, max_length=30)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('icon', models.CharField(blank=True, max_length=200)),
                ('limit_count', models.IntegerField(blank=True, default=None, null=True)),
                ('is_available', models.BooleanField(default=False)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='datasyncstatus',
            name='account_name',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='datasyncstatus',
            name='deleted_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='datasyncstatus',
            name='is_delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='datasyncstatus',
            name='source',
            field=models.CharField(blank=True, choices=[('notion', 'notion'), ('google_calendar', 'google_calendar'), ('gmail', 'gmail'), ('google_drive', 'google_drive')], null=True),
        ),
        migrations.AlterField(
            model_name='originaldocument',
            name='source',
            field=models.CharField(blank=True, choices=[('notion', 'notion'), ('google_calendar', 'google_calendar'), ('gmail', 'gmail'), ('google_drive', 'google_drive')], null=True),
        ),
        migrations.CreateModel(
            name='DataSourceUpvote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sources.datasource')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='datasyncstatus',
            name='data_source',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='sources.datasource'),
        ),
        migrations.AddField(
            model_name='originaldocument',
            name='data_source',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='sources.datasource'),
        ),
    ]
