# Generated by Django 4.1.7 on 2023-07-18 12:12

from django.db import migrations
import location_field.models.plain


class Migration(migrations.Migration):

    dependencies = [
        ('display', '0101_alter_useruploadedmap_attribution'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='location',
            field=location_field.models.plain.PlainLocationField(default=(0, 0), max_length=63),
            preserve_default=False,
        ),
    ]
