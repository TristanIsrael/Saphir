from psec import MqttFactory
from libsaphir import ClamAntivirusController

if __name__ == "__main__":
    mqtt_client = MqttFactory.create_mqtt_client_domu("saphir-clamav")

    c=clam_antivirus_controller(mqtt_client)
    c.start()

