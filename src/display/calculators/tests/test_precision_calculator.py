import datetime
from unittest.mock import patch

import dateutil
import gpxpy

from django.test import TransactionTestCase

from display.calculators.calculator_utilities import load_track_points_traccar_csv
from display.calculators.contestant_processor import ContestantProcessor
from display.calculators.positions_and_gates import Gate
from display.calculators.tests.utilities import load_traccar_track
from display.utilities.route_building_utilities import (
    create_precision_route_from_gpx,
    calculate_extended_gate,
)
from display.models import (
    Aeroplane,
    NavigationTask,
    Team,
    Contestant,
    ContestantTrack,
    Crew,
    Contest,
    Person,
    TeamTestScore,
    EditableRoute,
)
from utilities.mock_utilities import TraccarMock
from redis_queue import RedisQueue


def calculator_runner(contestant, track):
    q = RedisQueue(contestant.pk)
    contestant_processor = ContestantProcessor(contestant, live_processing=False)
    for i in track:
        i["id"] = 0
        i["deviceId"] = ""
        i["attributes"] = {}
        i["device_time"] = dateutil.parser.parse(i["time"])
        q.append(i)
    q.append(None)
    contestant_processor.run()
    while not q.empty():
        q.pop()


def load_track_points(filename):
    with open(filename, "r") as i:
        gpx = gpxpy.parse(i)
    positions = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                positions.append(
                    {
                        "time": point.time.isoformat(),
                        "latitude": point.latitude,
                        "longitude": point.longitude,
                        "altitude": point.elevation if point.elevation else 0,
                        "speed": 0,
                        "course": 0,
                        "battery_level": 100,
                    }
                )
    return positions


@patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
@patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
@patch("display.signals.get_traccar_instance", return_value=TraccarMock)
class TestFullTrack(TransactionTestCase):
    @patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
    @patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
    @patch("display.signals.get_traccar_instance", return_value=TraccarMock)
    def setUp(self, *args):
        from display.default_scorecards import default_scorecard_fai_precision_2020

        self.scorecard = default_scorecard_fai_precision_2020.get_default_scorecard()
        with open("display/calculators/tests/NM.csv", "r") as file:
            with patch(
                "display.models.EditableRoute._create_route_and_thumbnail",
                lambda name, r: EditableRoute.objects.create(name=name, route=r),
            ):
                editable_route, _ = EditableRoute.create_from_csv("Test", file.readlines()[1:])
                route = editable_route.create_precision_route(True, self.scorecard)
        navigation_task_start_time = datetime.datetime(2020, 8, 1, 6, 0, 0).astimezone()
        navigation_task_finish_time = datetime.datetime(2020, 8, 1, 16, 0, 0).astimezone()
        aeroplane = Aeroplane.objects.create(registration="LN-YDB")

        self.navigation_task = NavigationTask.create(
            name="NM navigation_task",
            route=route,
            original_scorecard=self.scorecard,
            contest=Contest.objects.create(
                name="contest",
                start_time=datetime.datetime.now(datetime.timezone.utc),
                finish_time=datetime.datetime.now(datetime.timezone.utc),
                time_zone="Europe/Oslo",
            ),
            start_time=navigation_task_start_time,
            finish_time=navigation_task_finish_time,
        )
        crew = Crew.objects.create(member1=Person.objects.create(first_name="Mister", last_name="Pilot"))
        self.team = Team.objects.create(crew=crew, aeroplane=aeroplane)
        start_time, speed = datetime.datetime(2020, 8, 1, 9, 15, tzinfo=datetime.timezone.utc), 70
        # Required to make the time zone save correctly
        self.navigation_task.refresh_from_db()
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=6,
            air_speed=speed,
            wind_direction=165,
            wind_speed=8,
        )

    def test_team_test_score_updated(self, *args):
        self.contestant.contestanttrack.update_score(23)
        team_test_score = TeamTestScore.objects.get(team=self.team, task_test__navigation_task=self.navigation_task)
        self.assertEqual(23, team_test_score.points)

    def test_correct_scoring_correct_track_precision(self, *args):
        positions = load_track_points("display/calculators/tests/test_contestant_correct_track.gpx")
        calculator_runner(self.contestant, positions)
        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(222, contestant_track.score)  # 150.0,

    def test_secret_score_no_override(self, *args):
        expected_time = datetime.datetime(2017, 1, 1, tzinfo=datetime.timezone.utc)
        actual_time = datetime.datetime(2017, 1, 1, 0, 1, tzinfo=datetime.timezone.utc)
        waypoint = self.contestant.navigation_task.route.waypoints[1]
        gate = Gate(waypoint, expected_time, calculate_extended_gate(waypoint, self.scorecard))  # SC 1/1
        self.assertEqual("secret", gate.type)
        gate.passing_time = actual_time
        score = self.scorecard.get_gate_timing_score_for_gate_type(gate.type, gate.expected_time, gate.passing_time)
        print([str(item) for item in self.navigation_task.route.waypoints])
        self.assertEqual(100, score)

    # def test_secret_score_override(self, *args):
    #     gate_override = GateScoreOverride.objects.create(
    #         for_gate_types=["secret"],
    #         checkpoint_penalty_per_second=0,
    #         checkpoint_maximum_penalty=0,
    #         checkpoint_not_found=0,
    #     )
    #     self.contestant.gate_score_override.add(gate_override)
    #     expected_time = datetime.datetime(2017, 1, 1, tzinfo=datetime.timezone.utc)
    #     actual_time = datetime.datetime(2017, 1, 1, 0, 1, tzinfo=datetime.timezone.utc)
    #     waypoint = self.contestant.navigation_task.route.waypoints[1]
    #     gate = Gate(waypoint, expected_time,
    #                 calculate_extended_gate(waypoint, self.scorecard))  # SC 1/1
    #     self.assertEqual("secret", gate.type)
    #     gate.passing_time = actual_time
    #     score = self.scorecard.get_gate_timing_score_for_gate_type(gate.type,
    #                                                                gate.expected_time,
    #                                                                gate.passing_time)
    #     print([str(item) for item in self.navigation_task.route.waypoints])
    #     self.assertEqual(0, score)

    # def test_score_override(self, *args):
    #     positions = load_track_points("display/calculators/tests/test_contestant_correct_track.gpx")
    #     track_override = TrackScoreOverride.objects.create()
    #     gate_override = GateScoreOverride.objects.create(
    #         for_gate_types=["sp", "tp", "fp", "secret"],
    #         checkpoint_grace_period_after=10,
    #         checkpoint_grace_period_before=10,
    #         checkpoint_penalty_per_second=1,
    #         checkpoint_maximum_penalty=100,
    #         checkpoint_not_found=100,
    #         missing_procedure_turn_penalty=100
    #     )
    #     self.contestant.track_score_override = track_override
    #     self.contestant.save()
    #     self.contestant.gate_score_override.add(gate_override)
    #     calculator_runner( self.contestant, positions )
    #     contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
    #     self.assertEqual(21, contestant_track.score)

    def test_helge_track_precision(self, *args):
        start_time, speed = datetime.datetime(2020, 8, 1, 10, 55, tzinfo=datetime.timezone.utc), 75
        crew = Crew.objects.create(
            member1=Person.objects.create(first_name="Misters", last_name="Pilot", email="a@gg.com")
        )
        aeroplane = Aeroplane.objects.create(registration="LN-YDB")
        team = Team.objects.create(crew=crew, aeroplane=aeroplane)

        contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=team,
            takeoff_time=start_time,
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_device_id="contestant",
            contestant_number=2,
            minutes_to_starting_point=6,
            air_speed=speed,
            wind_direction=165,
            wind_speed=8,
        )
        positions = load_track_points("display/calculators/tests/Helge.gpx")
        calculator_runner(contestant, positions)
        contestant_track = ContestantTrack.objects.get(contestant=contestant)
        self.assertEqual(327, contestant_track.score)

    def test_correct_scoring_bad_track_precision(self, *args):
        positions = load_track_points("display/calculators/tests/Steinar.gpx")
        calculator_runner(self.contestant, positions)
        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(1800, contestant_track.score)

    def test_missed_procedure_turn(self, *args):
        positions = load_track_points("display/calculators/tests/jorgen_missed_procedure_turn.gpx")
        calculator_runner(self.contestant, positions)
        strings = [item.string for item in self.contestant.scorelogentry_set.all()]

        self.assertTrue("TP1: 200.0 points incorrect procedure turn" in strings)
        self.assertTrue("TP4: 200.0 points incorrect procedure turn" in strings)
        # This is a bit in question, but I think it is correct since he never crosses the extended gate line
        # The procedure turn is performed before the gate which causes backtracking, but also a miss
        # According to A.2.2.16 the should be no penalty for missing the procedure turn if the extended gate line
        # is not crossed.
        # self.assertTrue("TP6: 200 points missing procedure turn" in strings)
        self.assertFalse("TP6: 200.0 points missing procedure turn" in strings)


@patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
@patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
@patch("display.signals.get_traccar_instance", return_value=TraccarMock)
class Test2017WPFC(TransactionTestCase):
    @patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
    @patch("display.signals.get_traccar_instance", return_value=TraccarMock)
    def setUp(self, *args):
        with open("display/tests/demo_contests/2017_WPFC/Route-1-Blue.gpx", "r") as file:
            route = create_precision_route_from_gpx(file, True)
        navigation_task_start_time = datetime.datetime(2020, 8, 1, 6, 0, 0).astimezone()
        navigation_task_finish_time = datetime.datetime(2020, 8, 1, 16, 0, 0).astimezone()
        self.aeroplane = Aeroplane.objects.create(registration="LN-YDB")
        from display.default_scorecards import default_scorecard_fai_precision_2020

        self.navigation_task = NavigationTask.create(
            name="NM navigation_task",
            route=route,
            original_scorecard=default_scorecard_fai_precision_2020.get_default_scorecard(),
            contest=Contest.objects.create(
                name="contest",
                start_time=datetime.datetime.now(datetime.timezone.utc),
                finish_time=datetime.datetime.now(datetime.timezone.utc),
                time_zone="Europe/Oslo",
            ),
            start_time=navigation_task_start_time,
            finish_time=navigation_task_finish_time,
        )
        crew = Crew.objects.create(member1=Person.objects.create(first_name="Mister", last_name="Pilot"))
        self.team = Team.objects.create(crew=crew, aeroplane=self.aeroplane)
        self.scorecard = default_scorecard_fai_precision_2020.get_default_scorecard()
        # Required to make the time zone save correctly
        self.navigation_task.refresh_from_db()

    def test_101(self, *args):
        track = load_track_points(
            "display/tests/demo_contests/2017_WPFC/101_-_Aircraft-039_-_1._Nav._-_Navigation_Flight_Results_(Edition_2).gpx"
        )
        start_time, speed = datetime.datetime(2015, 1, 1, 7, 30, tzinfo=datetime.timezone.utc), 80
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=8,
            air_speed=speed,
            wind_direction=160,
            wind_speed=18,
        )
        calculator_runner(self.contestant, track)
        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(
            1065, contestant_track.score  # 1152,
        )  # Should be 1071, a difference of 78. Mostly caused by timing differences, I think.


# @patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
# @patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
# class TestScoreverride(TransactionTestCase):
#     @patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
#     @patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
#     def setUp(self, *args):
#         with open("display/calculators/tests/bugs_with_gate_score_overrides.json", "r") as file:
#             task_data = json.load(file)
#         from display.default_scorecards import default_scorecard_fai_precision_2020
#         self.scorecard = default_scorecard_fai_precision_2020.get_default_scorecard()
#         self.aeroplane = Aeroplane.objects.create(registration="LN-YDB")
#         contest = Contest.objects.create(name="contest",
#                                          start_time=datetime.datetime.now(
#                                              datetime.timezone.utc),
#                                          finish_time=datetime.datetime.now(
#                                              datetime.timezone.utc),
#                                          time_zone="Europe/Oslo")
#         user = get_user_model().objects.create(email="user")
#         request = Mock()
#         request.user = user
#         serialiser = ExternalNavigationTaskNestedTeamSerialiser(data=task_data, context={"contest": contest,
#                                                                                          "request": request})
#         serialiser.is_valid()
#         self.navigation_task = serialiser.save()
#         # Required to make the time zone save correctly
#         self.navigation_task.refresh_from_db()
#
#     def test_4(self, *args):
#         with open("display/calculators/tests/bugs_with_gate_score_overrides_track.json", "r") as file:
#             track_data = json.load(file)
#         contestant = self.navigation_task.contestant_set.first()
#         insert_gpx_file(contestant, base64.decodebytes(track_data["track_file"].encode("utf-8")))
#
#         contestant_track = ContestantTrack.objects.get(contestant=contestant)
#
#         self.assertEqual(8, contestant.gatecumulativescore_set.get(gate="SP").points)
#         self.assertEqual(23, contestant_track.score)


@patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
@patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
@patch("display.signals.get_traccar_instance", return_value=TraccarMock)
class TestNM2019(TransactionTestCase):
    @patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
    @patch("display.signals.get_traccar_instance", return_value=TraccarMock)
    def setUp(self, *args):
        from display.default_scorecards import default_scorecard_fai_precision_2020

        self.scorecard = default_scorecard_fai_precision_2020.get_default_scorecard()
        with open("display/calculators/tests/NM2019.gpx", "r") as file:
            with patch(
                "display.models.EditableRoute._create_route_and_thumbnail",
                lambda name, r: EditableRoute.objects.create(name=name, route=r),
            ):
                editable_route, _ = EditableRoute.create_from_gpx("Test", file.read().encode("utf-8"))
                route = editable_route.create_precision_route(True, self.scorecard)
        navigation_task_start_time = datetime.datetime(2020, 8, 1, 6, 0, 0).astimezone()
        navigation_task_finish_time = datetime.datetime(2020, 8, 1, 16, 0, 0).astimezone()
        self.aeroplane = Aeroplane.objects.create(registration="LN-YDB")
        self.navigation_task = NavigationTask.create(
            name="NM navigation_task",
            route=route,
            original_scorecard=self.scorecard,
            contest=Contest.objects.create(
                name="contest",
                start_time=datetime.datetime.now(datetime.timezone.utc),
                finish_time=datetime.datetime.now(datetime.timezone.utc),
                time_zone="Europe/Oslo",
            ),
            start_time=navigation_task_start_time,
            finish_time=navigation_task_finish_time,
        )
        crew = Crew.objects.create(member1=Person.objects.create(first_name="Mister", last_name="Pilot"))
        self.team = Team.objects.create(crew=crew, aeroplane=self.aeroplane)
        # Required to make the time zone save correctly
        self.navigation_task.refresh_from_db()

    def test_arild(self, *args):
        track = load_track_points("display/calculators/tests/arild2019.gpx")
        start_time, speed = datetime.datetime(2015, 1, 1, 14, 25, tzinfo=datetime.timezone.utc), 54
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=6,
            air_speed=speed,
            wind_direction=220,
            wind_speed=7,
        )
        calculator_runner(self.contestant, track)

        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(
            838, contestant_track.score
        )  # Should be 1071, a difference of 78. Mostly caused by timing differences, I think.

    def test_fredrik(self, *args):
        track = load_track_points("display/calculators/tests/fredrik2019.gpx")
        start_time, speed = datetime.datetime(2015, 1, 1, 12, 45, tzinfo=datetime.timezone.utc), 90
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=6,
            air_speed=speed,
            wind_direction=220,
            wind_speed=7,
        )
        calculator_runner(self.contestant, track)
        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        # Apparently the contestant crosses the finish line before starting the track, leading to everything to be missed.
        self.assertEqual(
            1000, contestant_track.score
        )  # Should be 1071, a difference of 78. Mostly caused by timing differences, I think.


@patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
@patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
@patch("display.signals.get_traccar_instance", return_value=TraccarMock)
class TestHamar23March2021(TransactionTestCase):
    @patch("display.calculators.contestant_processor.get_traccar_instance", return_value=TraccarMock)
    @patch("display.models.contestant.get_traccar_instance", return_value=TraccarMock)
    @patch("display.signals.get_traccar_instance", return_value=TraccarMock)
    def setUp(self, *args):
        from display.default_scorecards import default_scorecard_fai_precision_2020

        self.scorecard = default_scorecard_fai_precision_2020.get_default_scorecard()
        with open("display/calculators/tests/hamartest.kml", "r") as file:
            with patch(
                "display.models.EditableRoute._create_route_and_thumbnail",
                lambda name, r: EditableRoute.objects.create(name=name, route=r),
            ):
                editable_route, _ = EditableRoute.create_from_kml("Test", file)
                route = editable_route.create_precision_route(True, self.scorecard)
        navigation_task_start_time = datetime.datetime(2021, 3, 23, 6, 0, 0).astimezone()
        navigation_task_finish_time = datetime.datetime(2021, 3, 23, 19, 0, 0).astimezone()
        self.aeroplane = Aeroplane.objects.create(registration="LN-YDB")
        self.navigation_task = NavigationTask.create(
            name="NM navigation_task",
            route=route,
            original_scorecard=self.scorecard,
            contest=Contest.objects.create(
                name="contest",
                start_time=datetime.datetime.now(datetime.timezone.utc),
                finish_time=datetime.datetime.now(datetime.timezone.utc),
                time_zone="Europe/Oslo",
            ),
            start_time=navigation_task_start_time,
            finish_time=navigation_task_finish_time,
        )
        crew = Crew.objects.create(member1=Person.objects.create(first_name="Mister", last_name="Pilot"))
        self.team = Team.objects.create(crew=crew, aeroplane=self.aeroplane)
        # Required to make the time zone save correctly
        self.navigation_task.refresh_from_db()

    def test_kolaf(self, *args):
        track = load_track_points("display/calculators/tests/hamar_kolaf.gpx")
        start_time, speed = datetime.datetime(2021, 3, 23, 14, 25, tzinfo=datetime.timezone.utc), 70
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=6,
            adaptive_start=True,
            air_speed=speed,
            wind_direction=180,
            wind_speed=4,
        )
        calculator_runner(self.contestant, track)

        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(216, contestant_track.score)  # 15 points more than website

    def test_vjoycar(self, *args):
        track = load_track_points_traccar_csv(load_traccar_track("display/calculators/tests/vjoycarhamar.csv"))
        start_time, speed = datetime.datetime(2021, 3, 23, 14, 25, tzinfo=datetime.timezone.utc), 70
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=6,
            adaptive_start=True,
            air_speed=speed,
            wind_direction=180,
            wind_speed=4,
        )
        calculator_runner(self.contestant, track)
        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(213, contestant_track.score)

    def test_lt03(self, *args):
        track = load_track_points_traccar_csv(load_traccar_track("display/calculators/tests/lt03_hamar.csv"))
        start_time, speed = datetime.datetime(2021, 3, 23, 14, 25, tzinfo=datetime.timezone.utc), 70
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=6,
            adaptive_start=True,
            air_speed=speed,
            wind_direction=180,
            wind_speed=4,
        )
        calculator_runner(self.contestant, track)
        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(213, contestant_track.score)

    def test_kolaf_trackar(self, *args):
        track = load_track_points_traccar_csv(load_traccar_track("display/calculators/tests/kolaf_hamar.csv"))
        start_time, speed = datetime.datetime(2021, 3, 23, 14, 25, tzinfo=datetime.timezone.utc), 70
        self.contestant = Contestant.objects.create(
            navigation_task=self.navigation_task,
            team=self.team,
            takeoff_time=start_time,
            finished_by_time=start_time + datetime.timedelta(hours=2),
            tracker_start_time=start_time - datetime.timedelta(minutes=30),
            tracker_device_id="Test contestant",
            contestant_number=1,
            minutes_to_starting_point=6,
            adaptive_start=True,
            air_speed=speed,
            wind_direction=180,
            wind_speed=4,
        )
        calculator_runner(self.contestant, track)
        contestant_track = ContestantTrack.objects.get(contestant=self.contestant)
        self.assertEqual(213, contestant_track.score)  # same as website
        # Test that task test is updated
        self.assertTrue(hasattr(self.navigation_task, "tasktest"))
        task_test = self.navigation_task.tasktest
        self.assertEqual(213, task_test.teamtestscore_set.get(team=self.team).points)
