import {protocol, server} from "./constants.js";
import axios from "axios";

export class TraccarDevice {
    constructor(id, name, status, lastUpdate, category) {
        this.id = id;
        this.name = name;
        this.status = status;
        this.lastUpdate = lastUpdate;
        this.category = category;
        this.devices = [];
    }
}

export class TraccarDeviceList {
    constructor() {
        this.finished = false;
        this.fetchDevices()
    }

    fetchDevices() {
        this.finished = false;
        axios.get(protocol + "://" + server + "/api/devices", {withCredentials: true}).then(res => {
            console.log("Device data:")
            console.log(res)
            this.devices = res.data.map((data) => {
                return new TraccarDevice(data.id, data.name, data.status, data.lastUpdate, data.category);
            })
            this.finished = true;
        });
    }

    deviceById(id) {
        while (!this.finished) {
        }
        return this.devices.find(device => device.id === id);
    }

    deviceByName(name) {
        while (!this.finished) {
        }
        return this.devices.find(device => device.name === name);
    }

}