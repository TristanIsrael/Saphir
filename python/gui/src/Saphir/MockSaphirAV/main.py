import sys, os, time
from pathlib import Path
from psec import Parametres, Cles

#curdir = os.path.dirname(__file__)
#libdir = os.path.realpath(curdir+"/../../../../../PSEC/python/lib/src") # Pour le débogage local
#sys.path.append(libdir)
from mock_saphir_av_controller import MockSaphirAVController

if __name__ == "__main__":
    Parametres().set_parametre(Cles.IDENTIFIANT_DOMAINE, "mock-saphir-av")

    mockPsecController = MockSaphirAVController()

    # Indiquer le chemin de la socket de messagerie du domaine mockav
    mockPsecController.start(socket_path= "/dev/ttys013")
    