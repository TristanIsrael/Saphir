import os

DEVMODE = os.getenv("DEVMODE", "") != ""
print(f"DEVMODE is {DEVMODE}")
TOPIC_ANALYSIS = "saphir/analysis"
TOPIC_ERROR = "saphir/error"
ANTIVIRUS_NEEDED = 2
