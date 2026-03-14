import os

DEVMODE = os.getenv("DEVMODE", "") != ""
print(f"DEVMODE is {DEVMODE}")
TOPIC_ANALYSIS = "saphir/analysis"
TOPIC_ERROR = "saphir/error"
ANTIVIRUS_NEEDED = 2
BIG_FILE_SIZE_IN_MB = -1 # Disabled in 3.0 (100*1024*1024 # 100 MB)

# If True the big archives (see BIG_FILE_SIZE_IN_MB) will be mounted and scanned as a disk
MOUNT_ARCHIVES = False
