from datetime import timedelta

import dateutil
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.views.generic import View, TemplateView, ListView
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import logging
import urllib.request
import os

from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveAPIView, get_object_or_404
from rest_framework.response import Response

from display.forms import ImportTrackForm
from display.models import Contest, Track, ContestantTrack, Contestant
from display.serialisers import ContestSerialiser, ContestantTrackSerialiser
from influx_facade import InfluxFacade

logger = logging.getLogger(__name__)


def frontend_view(request, pk):
    return render(request, "display/root.html", {"contest_id": pk, "live_mode": "true"})


def frontend_view_offline(request, pk):
    return render(request, "display/root.html", {"contest_id": pk, "live_mode": "false"})


class RetrieveContestApi(RetrieveAPIView):
    serializer_class = ContestSerialiser
    queryset = Contest.objects.all()
    lookup_field = "pk"


class ContestList(ListView):
    model = Contest


@api_view(["GET"])
def get_data_from_time_for_contest(request, contest_pk):
    contest = get_object_or_404(Contest, pk=contest_pk)  # type: Contest
    influx = InfluxFacade()
    from_time = request.GET.get("from_time", (contest.start_time - timedelta(minutes=30)).isoformat())
    logger.info("Fetching data from time {}".format(from_time))
    result_set = influx.get_positions_for_contest(contest_pk, from_time)
    annotation_results = influx.get_annotations_for_contest(contest_pk, from_time)
    positions = []
    annotations = []
    global_latest_time = None
    for contestant in contest.contestant_set.all():
        logger.debug("Contestant_pk: {}".format(contestant.pk))
        position_data = list(result_set.get_points(tags={"contestant": str(contestant.pk)}))
        logger.debug(position_data)
        if len(position_data):
            latest_time = dateutil.parser.parse(position_data[-1]["time"])
            global_latest_time = latest_time if not global_latest_time else max(latest_time, global_latest_time)
            contest_data = {
                "contestant_id": contestant.pk,
                "position_data": position_data
            }
            positions.append(contest_data)
        annotation_data = list(annotation_results.get_points(tags={"contestant": str(contestant.pk)}))
        if len(annotation_data):
            annotations.append({"contestant_id": contestant.pk, "annotations": annotation_data})

    return Response({"latest_time": global_latest_time, "positions": positions, "annotations": annotations,
                     "contestant_tracks": [ContestantTrackSerialiser(item).data for item in
                                           ContestantTrack.objects.filter(contestant__contest=contest)]})


@api_view(["GET"])
def get_data_from_time_for_contestant(request, contestant_pk):
    contestant = get_object_or_404(Contestant, pk=contestant_pk)  # type: Contestant
    influx = InfluxFacade()
    from_time = request.GET.get("from_time", (contestant.contest.start_time - timedelta(minutes=30)).isoformat())
    logger.info("Fetching data from time {}".format(from_time))
    result_set = influx.get_positions_for_contestant(contestant_pk, from_time)
    annotation_results = influx.get_annotations_for_contestant(contestant_pk, from_time)
    positions = []
    annotations = []
    global_latest_time = None
    logger.debug("Contestant_pk: {}".format(contestant.pk))
    position_data = list(result_set.get_points(tags={"contestant": str(contestant.pk)}))
    logger.debug(position_data)
    if len(position_data):
        latest_time = dateutil.parser.parse(position_data[-1]["time"])
        global_latest_time = latest_time
        contest_data = {
            "contestant_id": contestant.pk,
            "position_data": position_data
        }
        positions.append(contest_data)
    annotation_data = list(annotation_results.get_points(tags={"contestant": str(contestant.pk)}))
    if len(annotation_data):
        annotations.append({"contestant_id": contestant.pk, "annotations": annotation_data})
    if hasattr(contestant, "contestantstrack"):
        contestant_track = [ContestantTrackSerialiser(contestant.contestanttrack).data]
    else:
        contestant_track = []
    return Response({"latest_time": global_latest_time, "positions": positions, "annotations": annotations,
                     "contestant_tracks": contestant_track})


def import_track(request):
    form = ImportTrackForm()
    if request.method == "POST":
        form = ImportTrackForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data["name"]
            data = request.FILES['file'].readlines()
            track_data = []
            for line in data[1:]:
                line = [item.strip() for item in line.decode(encoding="UTF-8").split(",")]
                track_data.append({"name": line[0], "longitude": float(line[1]), "latitude": float(line[2]),
                                   "type": line[3], "width": float(line[4])})
            Track.create(name=name, waypoints=track_data)
            return redirect("/")
    return render(request, "display/import_track_form.html", {"form": form})
