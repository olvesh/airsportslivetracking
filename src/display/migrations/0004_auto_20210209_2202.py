# Generated by Django 3.1 on 2021-02-09 22:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('display', '0003_auto_20210209_1955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='navigationtask',
            name='scorecard',
            field=models.ForeignKey(help_text='Reference to an existing scorecard name. Currently existing scorecards: <function NavigationTask.<lambda> at 0x7f32fe876e18>', on_delete=django.db.models.deletion.PROTECT, to='display.scorecard'),
        ),
        migrations.AlterField(
            model_name='person',
            name='app_tracking_id',
            field=models.CharField(editable=False, max_length=28),
        ),
    ]
