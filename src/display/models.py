import datetime
import math
from collections import namedtuple
from plistlib import Dict
from typing import List
import cartopy.crs as ccrs
from django.core.exceptions import ObjectDoesNotExist

from django.db import models

# Create your models here.
from display.coordinate_utilities import calculate_distance_lat_lon, calculate_bearing
from display.my_pickled_object_field import MyPickledObjectField
from display.utilities import get_distance_to_other_gates


def user_directory_path(instance, filename):
    return "aeroplane_{0}/{1}".format(instance.registration, filename)


class Aeroplane(models.Model):
    registration = models.CharField(max_length=20)

    def __str__(self):
        return self.registration


Waypoint = namedtuple("Waypoint", "name latitude longitude start_point finish_point is_secret")


class Track(models.Model):
    name = models.CharField(max_length=200)
    waypoints = MyPickledObjectField(default=list)
    starting_line = MyPickledObjectField(default=list)

    def __str__(self):
        return self.name

    @classmethod
    def create(cls, name: str, waypoints: List[Dict]) -> "Track":
        waypoints = cls.add_gate_data(waypoints)
        waypoints = cls.legs(waypoints)
        starting_line = cls.create_starting_line(waypoints)
        object = cls(name=name, waypoints=waypoints, starting_line=starting_line)
        object.save()
        return object

    @staticmethod
    def add_gate_data(waypoints: List[Dict]) -> List[Dict]:
        """
        Changes waypoint dictionaries

        :param waypoints:
        :return:
        """
        gates = [item for item in waypoints if item["type"] in ("tp", "secret")]
        for index in range(len(gates) - 1):
            gates[index + 1]["gate_line"] = create_perpendicular_line_at_end(gates[index]["longitude"],
                                                                             gates[index]["latitude"],
                                                                             gates[index + 1]["longitude"],
                                                                             gates[index + 1]["latitude"],
                                                                             gates[index + 1]["width"] * 1852)
        gates[0]["gate_line"] = create_perpendicular_line_at_end(gates[1]["longitude"],
                                                                 gates[1]["latitude"],
                                                                 gates[0]["longitude"],
                                                                 gates[0]["latitude"],
                                                                 gates[0]["width"] * 1852)
        return waypoints

    @staticmethod
    def create_starting_line(gates) -> Dict:
        return {
            "name": "Starting line",
            "latitude": gates[0]["latitude"],
            "longitude": gates[0]["longitude"],
            "gate_line": create_perpendicular_line_at_end(gates[1]["longitude"],
                                                          gates[1]["latitude"],
                                                          gates[0]["longitude"],
                                                          gates[0]["latitude"],
                                                          40),
            "inside_distance": 0,
            "outside_distance": 0,
        }

    @staticmethod
    def insert_gate_ranges(waypoints):
        for main_gate in waypoints:
            distances = list(get_distance_to_other_gates(main_gate, waypoints).values())
            minimum_distance = min(distances)
            main_gate["inside_distance"] = minimum_distance * 2 / 3
            main_gate["outside_distance"] = 2000 + minimum_distance * 2 / 3

    @staticmethod
    def legs(waypoints) -> Dict:
        gates = [item for item in waypoints if item["type"] in ("tp", "secret")]
        for index in range(1, len(gates)):
            gates[index]["distance"] = -1
            gates[index]["gate_distance"] = calculate_distance_lat_lon(
                (gates[index - 1]["latitude"], gates[index - 1]["longitude"]),
                (gates[index]["latitude"], gates[index]["longitude"])) * 1000  # Convert to metres
        tp_gates = [item for item in waypoints if item["type"] == "tp"]
        for index in range(1, len(tp_gates)):
            tp_gates[index]["bearing"] = calculate_bearing(
                (tp_gates[index - 1]["latitude"], tp_gates[index - 1]["longitude"]),
                (tp_gates[index]["latitude"], tp_gates[index]["longitude"]))
            tp_gates[index]["distance"] = calculate_distance_lat_lon(
                (tp_gates[index - 1]["latitude"], tp_gates[index - 1]["longitude"]),
                (tp_gates[index]["latitude"], tp_gates[index]["longitude"])) * 1000  # Convert to metres
        for index in range(1, len(tp_gates) - 1):
            tp_gates[index]["is_procedure_turn"] = is_procedure_turn(tp_gates[index]["bearing"],
                                                                     tp_gates[index + 1]["bearing"])
            tp_gates[index]["turn_direction"] = "ccw" if bearing_difference(tp_gates[index]["bearing"],
                                                                            tp_gates[index + 1][
                                                                                "bearing"]) > 0 else "cw"
        Track.insert_gate_ranges(waypoints)
        return waypoints


def bearing_difference(bearing1, bearing2) -> float:
    return (bearing2 - bearing1 + 540) % 360 - 180


def is_procedure_turn(bearing1, bearing2) -> bool:
    """
    Return True if the turn is more than 90 degrees

    :param bearing1: degrees
    :param bearing2: degrees
    :return:
    """
    return abs(bearing_difference(bearing1, bearing2)) > 90


def create_perpendicular_line_at_end(x1, y1, x2, y2, length):
    pc = ccrs.PlateCarree()
    epsg = ccrs.epsg(3857)
    x1, y1 = epsg.transform_point(x1, y1, pc)
    x2, y2 = epsg.transform_point(x2, y2, pc)
    slope = (y2 - y1) / (x2 - x1)
    dy = math.sqrt((length / 2) ** 2 / (slope ** 2 + 1))
    dx = -slope * dy
    x1, y1 = pc.transform_point(x2 + dx, y2 + dy, epsg)
    x2, y2 = pc.transform_point(x2 - dx, y2 - dy, epsg)
    return [x1, y1, x2, y2]


class Team(models.Model):
    pilot = models.CharField(max_length=200)
    navigator = models.CharField(max_length=200, blank=True)
    aeroplane = models.ForeignKey(Aeroplane, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        if len(self.navigator) > 0:
            return "{} and {} in {}".format(self.pilot, self.navigator, self.aeroplane)
        return "{} in {}".format(self.pilot, self.aeroplane)


class Contest(models.Model):
    name = models.CharField(max_length=200)
    track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True)
    server_address = models.CharField(max_length=200, blank=True)
    server_token = models.CharField(max_length=200, blank=True)
    start_time = models.DateTimeField()
    finish_time = models.DateTimeField()

    def __str__(self):
        return "{}: {}".format(self.name, self.start_time.isoformat())


class Contestant(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    takeoff_time = models.DateTimeField()
    minutes_to_starting_point = models.FloatField(default=5)
    finished_by_time = models.DateTimeField(null=True)
    ground_speed = models.FloatField(default=70)
    contestant_number = models.IntegerField()
    traccar_device_name = models.CharField(max_length=100)

    def __str__(self):
        return "{}: {} in {}".format(self.contestant_number, self.team, self.contest)

    @property
    def gate_times(self) -> Dict:
        crossing_times = {}
        gates = [item for item in self.contest.track.waypoints if item["type"] in ("tp", "secret")]
        crossing_time = self.takeoff_time + datetime.timedelta(minutes=self.minutes_to_starting_point)
        crossing_times[gates[0]["name"]] = crossing_time
        for gate in gates[1:]:
            crossing_time += datetime.timedelta(hours=(gate["gate_distance"] / 1852) / self.ground_speed)
            if gate.get("is_procedure_turn", False):
                crossing_time += datetime.timedelta(minutes=1)
            crossing_times[gate["name"]] = crossing_time
        return crossing_times

    @classmethod
    def get_contestant_for_device_at_time(cls, device: str, stamp: datetime.datetime):
        try:
            return cls.objects.get(traccar_device_name=device, takeoff_time__lte=stamp, finished_by_time__gte=stamp)
        except ObjectDoesNotExist:
            return None


class ContestantTrack(models.Model):
    contestant = models.OneToOneField(Contestant, on_delete=models.CASCADE)
    score_log = MyPickledObjectField(default=list)
    score_per_gate = MyPickledObjectField(default=dict)
    score = models.FloatField(default=0)
    current_state = models.CharField(max_length=200, default="Waiting...")
    current_leg = models.CharField(max_length=100, default="")

    @classmethod
    def get_contestant_track_for_device_at_time(cls, device: str, stamp: datetime.datetime):
        contestant = Contestant.get_contestant_for_device_at_time(device, stamp)
        if contestant:
            return cls.objects.get_or_create(contestant=contestant)[0]
        return None

    def update_score(self, score_per_gate, score, score_log):
        self.score = score
        self.score_per_gate = score_per_gate
        self.score_log = score_log
        self.save()

    def updates_current_state(self, state: str):
        if self.current_state != state:
            self.current_state = state
            self.save()

    def update_current_leg(self, current_leg: str):
        if self.current_leg != current_leg:
            self.current_leg = current_leg
            self.save()
