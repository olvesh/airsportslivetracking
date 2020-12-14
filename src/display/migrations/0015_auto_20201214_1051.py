# Generated by Django 3.1.4 on 2020-12-14 10:51

from django.db import migrations, models
import django.db.models.deletion


def create_missing_models(apps, schema_editor):
    NavigationTask = apps.get_model("display", "NavigationTask")
    Contest = apps.get_model("display", "Contest")
    Contestant = apps.get_model("display", "Contestant")
    Scorecard = apps.get_model("display", "Scorecard")
    Route = apps.get_model("display", "Route")
    Team = apps.get_model("display", "Team")
    Aeroplane = apps.get_model("display", "Aeroplane")
    Crew = apps.get_model("display", "Crew")

    missing_contest = NavigationTask.objects.filter(contest__isnull=True)
    if missing_contest.count() > 0:
        contest = Contest.objects.get_or_create(name="Placeholder")
        for navigation in missing_contest:
            navigation.contest = contest
            navigation.save()
    missing_scorecard = Contestant.objects.filter(scorecard__isnull=True)
    for missing in missing_scorecard:
        missing.scorecard = Scorecard.objects.get_or_create(name="default")[0]
        missing.save()
    missing_route = NavigationTask.objects.filter(route__isnull=True)
    if missing_route.count() > 0:
        route = Route.objects.create(name="default")
        for missing in missing_route:
            missing.route = route
            missing.save()
    missing_aeroplane = Team.objects.filter(aeroplane__isnull=True)
    if missing_aeroplane.count() > 0:
        aeroplane = Aeroplane.objects.get_or_create(registration="default")[0]
        for missing in missing_aeroplane:
            missing.aeroplane = aeroplane
            missing.save()
    missing_crew = Team.objects.filter(crew__isnull=True)
    if missing_crew.count() > 0:
        crew = Crew.objects.get_or_create(pilot="default")[0]
        for missing in missing_crew:
            missing.crew = crew
            missing.save()


class Migration(migrations.Migration):
    dependencies = [
        ('display', '0014_auto_20201212_1453'),
    ]

    operations = [
        migrations.RunPython(create_missing_models),        migrations.AlterModelOptions(
            name='navigationtask',
            options={'ordering': ('start_time', 'finish_time')},
        ),
        migrations.AlterField(
            model_name='contestant',
            name='scorecard',
            field=models.ForeignKey(
                help_text='Reference to an existing scorecard name. Currently existing scorecards: <function Contestant.<lambda> at 0x7fb942a836a8>',
                on_delete=django.db.models.deletion.PROTECT, to='display.scorecard'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='navigationtask',
            name='contest',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='display.contest'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='navigationtask',
            name='route',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='display.route'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='team',
            name='aeroplane',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='display.aeroplane'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='team',
            name='crew',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='display.crew'),
            preserve_default=False,
        ),
    ]
