# Generated by Django 3.2.9 on 2021-11-14 10:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('display', '0049_auto_20211114_1018'),
    ]

    operations = [
        migrations.RenameField(
            model_name='prohibited',
            old_name='tooltip_offset',
            new_name='tooltip_position',
        ),
        migrations.AlterField(
            model_name='navigationtask',
            name='scorecard',
            field=models.ForeignKey(help_text='Reference to an existing scorecard name. Currently existing scorecards: <function NavigationTask.<lambda> at 0x7f8341ed7a60>', on_delete=django.db.models.deletion.PROTECT, to='display.scorecard'),
        ),
    ]
