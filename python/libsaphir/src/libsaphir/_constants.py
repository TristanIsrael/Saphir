import os

DEVMODE = os.getenv("DEVMODE", False)
print("DEVMODE is {}".format(DEVMODE))
TOPIC_ANALYSE = "saphir/analysis"
ANTIVIRUS_NEEDED = 1