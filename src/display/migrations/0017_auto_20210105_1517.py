# Generated by Django 3.1.5 on 2021-01-05 15:17

from django.db import migrations
def delete_clubs(apps, schema_editor):
    Club = apps.get_model('display', 'Club')
    Club.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('display', '0016_auto_20210104_1604'),
    ]

    operations = [
        migrations.RunPython(delete_clubs)
    ]
