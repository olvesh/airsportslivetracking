#
from display.models import GateScore, Scorecard


def get_default_scorecard():
    scorecard, created = Scorecard.objects.get_or_create(name="NLF Precision 2020")
    scorecard.backtracking_penalty = 200
    scorecard.backtracking_grace_time_seconds = 5
    scorecard.use_procedure_turns = True
    regular_gate_score = GateScore.objects.get_or_create(extended_gate_width=6,  # used for PT
                                                  bad_crossing_extended_gate_penalty=0,
                                                  graceperiod_before=2,
                                                  graceperiod_after=2,
                                                  maximum_penalty=100,
                                                  penalty_per_second=3,
                                                  missed_penalty=100,
                                                  missed_procedure_turn_penalty=200)[0]
    scorecard.takeoff_gate_score = GateScore.objects.get_or_create(extended_gate_width=0,
                                                                            bad_crossing_extended_gate_penalty=0,
                                                                            graceperiod_before=0,
                                                                            graceperiod_after=60,
                                                                            maximum_penalty=200,
                                                                            penalty_per_second=200,
                                                                            missed_penalty=0,
                                                                            missed_procedure_turn_penalty=0)[0]
    scorecard.landing_gate_score = GateScore.objects.get_or_create(extended_gate_width=0,
                                                                            bad_crossing_extended_gate_penalty=0,
                                                                            graceperiod_before=0,
                                                                            graceperiod_after=60,
                                                                            maximum_penalty=0,
                                                                            penalty_per_second=0,
                                                                            missed_penalty=0,
                                                                            missed_procedure_turn_penalty=0)[0]
    scorecard.turning_point_gate_score = regular_gate_score
    scorecard.secret_gate_score = regular_gate_score
    scorecard.starting_point_gate_score = GateScore.objects.get_or_create(extended_gate_width=2,
                                                                                   bad_crossing_extended_gate_penalty=200,
                                                                                   graceperiod_before=2,
                                                                                   graceperiod_after=2,
                                                                                   maximum_penalty=100,
                                                                                   penalty_per_second=3,
                                                                                   missed_penalty=100,
                                                                                   missed_procedure_turn_penalty=200)[0]
    scorecard.finish_point_gate_score = regular_gate_score
    scorecard.save()

    return scorecard
