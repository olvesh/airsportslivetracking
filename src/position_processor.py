import json
import logging
import os
from pprint import pprint
from typing import Set, List

from secret_configuration import TRACCAR_ADDRESS
from traccar_facade import Traccar

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "live_tracking_map.settings")
    import django

    django.setup()

import websocket
from influx_facade import InfluxFacade
from display.models import Contestant
from display.track_calculator import Calculator

logger = logging.getLogger(__name__)
influx = InfluxFacade()
influx.drop_database()
influx.create_database()
traccar = Traccar()
devices = traccar.get_device_map()
logger.debug("Devices {}".format(devices))

calculators = {}


def add_positions_to_calculator(contestant: Contestant, positions: List):
    if contestant.pk not in calculators:
        calculators[contestant.pk] = Calculator(contestant, influx)
    calculator = calculators[contestant.pk]  # type: Calculator
    calculator.add_positions(positions)


def cleanup_calculators():
    for key, calculator in dict(calculators).items():
        if not calculator.is_alive():
            calculators.pop(key)


def build_and_push_position_data(data):
    received_positions = influx.store_positions(devices, data.get("positions", []))
    for contestant, positions in received_positions.items():
        add_positions_to_calculator(contestant, positions)
    cleanup_calculators()


def on_message(ws, message):
    data = json.loads(message)
    build_and_push_position_data(data)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    pass


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}

headers['Upgrade'] = 'websocket'

if __name__ == "__main__":
    websocket.enableTrace(True)
    cookies = traccar.session.cookies.get_dict()
    ws = websocket.WebSocketApp("ws://{}/api/socket".format(TRACCAR_ADDRESS),
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                header=headers,
                                cookie="; ".join(["%s=%s" % (i, j) for i, j in cookies.items()]))
    ws.run_forever()
