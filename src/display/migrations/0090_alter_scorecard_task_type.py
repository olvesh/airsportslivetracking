# Generated by Django 4.1.7 on 2023-03-26 17:29

import display.fields.my_pickled_object_field
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('display', '0089_auto_20230317_1329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scorecard',
            name='task_type',
            field=display.fields.my_pickled_object_field.MyPickledObjectField(default=list, editable=False, help_text='List of task types supported by the scorecard'),
        ),
    ]
