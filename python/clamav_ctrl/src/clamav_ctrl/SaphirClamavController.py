from libsaphir import AbstractAntivirusController
from psec import Commande

class SaphirClamavController(AbstractAntivirusController):

    def _execute_command_analyse_file(self, command:Commande):
        pass