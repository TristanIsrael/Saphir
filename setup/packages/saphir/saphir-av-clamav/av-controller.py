from psec import MqttFactory, Api
from libsaphir import ClamAntivirusController

if __name__ == "__main__":
    c = ClamAntivirusController()
    c.start()
