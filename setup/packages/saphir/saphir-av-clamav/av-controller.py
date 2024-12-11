from psec import MqttFactory, Api
from libsaphir import ClamAntivirusController
import threading

lock = threading.Event()

if __name__ == "__main__":
    #mqtt_client = MqttFactory.create_mqtt_client_domu("av-clamav")

    c=ClamAntivirusController()
    c.start()
