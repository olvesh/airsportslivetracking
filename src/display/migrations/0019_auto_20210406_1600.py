# Generated by Django 3.1.7 on 2021-04-06 15:44
import datetime

import dateutil
from django.db import migrations, models
import django.db.models.deletion


def fix_log(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    ContestantTrack = apps.get_model("display", "ContestantTrack")
    ScoreLogEntry = apps.get_model("display", "ScoreLogEntry")
    for track in ContestantTrack.objects.using(db_alias).all():
        for item in track.score_log:
            ScoreLogEntry.objects.create(contestant=track.contestant, time=datetime.datetime.now(datetime.timezone.utc),
                                         gate=item["gate"], message=item["message"], string=item["string"],
                                         points=item["points"],
                                         planned=dateutil.parser.parse(item["planned"]) if item["planned"] else None,
                                         actual=dateutil.parser.parse(item["actual"]) if item["actual"] else None,
                                         offset_string=item["offset_string"])


def fix_cards(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    ContestantTrack = apps.get_model("display", "ContestantTrack")
    for track in ContestantTrack.objects.using(db_alias).all():
        for card in track.playingcard_set.all():
            card.contestant = track.contestant
            card.save()


def fix_actual_gates_times(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    ContestantTrack = apps.get_model("display", "ContestantTrack")
    ActualGateTime = apps.get_model("display", "ActualGateTime")
    for track in ContestantTrack.objects.using(db_alias).all():
        for name, time in track.gate_actual_times.items():
            ActualGateTime.objects.create(contestant=track.contestant, gate=name, time=time)


class Migration(migrations.Migration):
    dependencies = [
        ('display', '0018_auto_20210406_1544'),
    ]

    operations = [
        migrations.RunPython(fix_log),
        migrations.RunPython(fix_cards),
        migrations.RunPython(fix_actual_gates_times),
        migrations.RemoveField(
            model_name='contestanttrack',
            name='gate_actual_times',
        ),
        migrations.RemoveField(
            model_name='contestanttrack',
            name='score_log',
        ),
        migrations.RemoveField(
            model_name='contestanttrack',
            name='score_per_gate',
        ),
        migrations.RemoveField(
            model_name='playingcard',
            name='contestant_track',
        ),
        migrations.AlterField(
            model_name='contest',
            name='autosum_scores',
            field=models.BooleanField(default=True,
                                      help_text='If true, contest summary points for a team will be updated with the new sum when any task is updated'),
        ),
        migrations.AlterField(
            model_name='navigationtask',
            name='scorecard',
            field=models.ForeignKey(
                help_text='Reference to an existing scorecard name. Currently existing scorecards: <function NavigationTask.<lambda> at 0x7f12552c38c8>',
                on_delete=django.db.models.deletion.PROTECT, to='display.scorecard'),
        ),
    ]
