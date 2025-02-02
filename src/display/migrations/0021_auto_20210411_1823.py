# Generated by Django 3.1.8 on 2021-04-11 18:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('display', '0020_auto_20210407_1257'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='is_featured',
            field=models.BooleanField(default=True, help_text='A featured contest is visible on the global map and in the event list. If it is not featured, a direct link is requiredto access it.'),
        ),
        migrations.AddField(
            model_name='navigationtask',
            name='is_featured',
            field=models.BooleanField(default=True, help_text='A featured navigation task is visible in the contest details of a featured contest. Contestants on the global map are also tagged as part of the navigation task'),
        ),
        migrations.AlterField(
            model_name='contest',
            name='is_public',
            field=models.BooleanField(default=False, help_text='A public contest is visible to people who are not logged and does not require special privileges'),
        ),
        migrations.AlterField(
            model_name='navigationtask',
            name='scorecard',
            field=models.ForeignKey(help_text='Reference to an existing scorecard name. Currently existing scorecards: <function NavigationTask.<lambda> at 0x7f5091aee048>', on_delete=django.db.models.deletion.PROTECT, to='display.scorecard'),
        ),
    ]
