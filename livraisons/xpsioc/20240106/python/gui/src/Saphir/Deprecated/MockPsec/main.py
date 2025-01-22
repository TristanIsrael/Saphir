import sys, os, time
from pathlib import Path

#curdir = os.path.dirname(__file__)
#libdir = os.path.realpath(curdir+"/../../../../../PSEC/python/lib/src") # Pour le débogage local
#sys.path.append(libdir)
from mock_psec_controller import MockPSECController

if __name__ == "__main__":
    mockPsecController = MockPSECController()
    mockPsecController.start()    