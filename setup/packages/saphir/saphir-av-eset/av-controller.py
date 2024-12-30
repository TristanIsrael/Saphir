from psec import MqttFactory, Api
from libsaphir import EeaAntivirusController
import threading

lock = threading.Event()

if __name__ == "__main__":
    e=EeaAntivirusController()
    e.start()
