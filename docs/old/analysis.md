# Analysis

This documents contains different analyses about design or problems investigation.

## ESET OOM crash with a 180 MB file (pgadmin4-7.8-x64.exe)

ESET works like a charm with a 2GB file but this particular file makes the whole container crash because OOM...

Data:
- Total RAM capacity: 2 GB
- Available RAM before the analysis: 
- Process crashing: odscan, systemd
- Size of /mnt/upper after the boot: 8 740 bytes
- Size of /mnt/upper after the crash: 8 752 bytes
- The Domain has 10 vCPUs

Observations:
- The memory remains stable for several minutes and suddenly it grows and crashed immediately
- Just before the crash we can see the process `systemd` passing #1 in CPU usage -> suspected to be the process that causes the OOM

Analysis of the file (pgadmin4-7.8-x64.exe):
- Setup made with Innosetup
- Original size: 183,4 Mo
- Uncompressed size: 870,7 Mo
- 14 527 files

Explanation:
- The file contains one or more archives that are uncompressed in the temporary disk
- The memory get saturated by the files extracted and the files they contain

Solution:
- Add a temporary disk for /tmp

