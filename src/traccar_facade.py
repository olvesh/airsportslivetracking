import datetime
from typing import List, Dict

import requests
from requests import Session


class Traccar:
    def __init__(self, protocol, address, token):
        self.protocol = protocol
        self.address = address
        self.token = token
        self.base = "{}://{}".format(self.protocol, self.address)
        self.session = self.get_authenticated_session()
        self.device_map = None

    def get_authenticated_session(self) -> Session:
        session = requests.Session()
        string = self.base + "/api/session?token={}".format(self.token)
        response = session.get(string)
        if response.status_code != 200:
            raise Exception("Failed authenticating session: {}".format(response.text))
        return session

    def update_and_get_devices(self) -> List:
        return self.session.get(self.base + "/api/devices").json()

    def delete_device(self, device_id):
        response = self.session.delete(self.base + "/api/devices/{}".format(device_id))
        print(response)
        print(response.text)
        return response.status_code == 204

    def create_device(self, device_name):
        response = self.session.post(self.base + "/api/devices", json={"uniqueId": device_name, "name": device_name})
        print(response)
        print(response.text)
        if response.status_code == 200:
            return response.json()

    def delete_all_devices(self):
        devices = self.update_and_get_devices()
        for item in devices:
            self.delete_device(item["id"])
        return [item["name"] for item in devices]

    def get_device_map(self) -> Dict:
        self.device_map = {item["id"]: item["name"] for item in self.update_and_get_devices()}
        return self.device_map
