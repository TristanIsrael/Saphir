import os

DEVMODE = os.getenv("DEVMODE", True)
print("DEVMODE is {}".format(DEVMODE))
TOPIC_ANALYSE = "saphir/analysis"
TOPIC_ERREUR = "saphir/error"
ANTIVIRUS_NEEDED = 2