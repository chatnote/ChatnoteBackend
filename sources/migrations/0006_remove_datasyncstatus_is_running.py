# Generated by Django 4.2.3 on 2023-10-16 13:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sources', '0005_remove_notionpage_subpage_counts_notionpage_page_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datasyncstatus',
            name='is_running',
        ),
    ]
