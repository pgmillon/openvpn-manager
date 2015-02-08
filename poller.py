#!/vagrant/flask/bin/python

import threading
import time
import requests


config = {
    "SERVER_URL": "http://127.0.0.1:5000"
}


class ConnectionPoller(threading.Thread):

    active = True

    def __int__(self):
        threading.Thread.__init__(self)

    def run(self):
        while self.active:
            try:
                for connection in requests.get(config["SERVER_URL"] + "/api/connections").json()["objects"]:
                    connected = False
                    for processUrl in connection["processes"]:
                        process = requests.get(config["SERVER_URL"] + processUrl).json()
                        if 1 == process["status"]:
                            connected = True
                        else:
                            requests.delete(config["SERVER_URL"] + processUrl)
                    if connection.get("active", False) and "auto" == connection["configuration"].get("connect") and not connected:
                        requests.post(config["SERVER_URL"] + "/api/connections/%d/connect" % connection["id"])
                time.sleep(5)
            except KeyboardInterrupt:
                self.stop()
                print

    def stop(self):
        self.active = False

ConnectionPoller().run()