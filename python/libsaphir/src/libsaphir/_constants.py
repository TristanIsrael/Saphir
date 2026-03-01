import os

DEVMODE = os.getenv("DEVMODE", False)
print(f"DEVMODE is {DEVMODE}")
TOPIC_ANALYSE = "saphir/analysis"
TOPIC_ERREUR = "saphir/error"
ANTIVIRUS_NEEDED = 2