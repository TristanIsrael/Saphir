import os

DEVMODE = os.getenv("DEVMODE", False)
print("DEVMODE is {}".format(DEVMODE))
TOPIC_ANALYSE = "saphir/analysis"
TOPIC_ERREUR = "saphir/error"
ANTIVIRUS_NEEDED = 2