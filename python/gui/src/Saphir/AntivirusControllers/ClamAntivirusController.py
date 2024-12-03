from abstract_antivirus_controller import AbstractAntivirusController
from psec import Api, EtatComposant

class ClamAntivirusController(AbstractAntivirusController):
    
    __state = EtatComposant.UNKNOWN

    def __init__(self):
        super().__init__("ClamAV", "ClamAV Antivirus controller")

    def _on_ready(self) -> None:
        Api().info("ClamAV antivirus controller is starting.")
        self.__state = EtatComposant.STARTING
    
    def _analyse_file(self, filepath: str) -> None:
        if self.__state != EtatComposant.READY:
            Api().error("The component is not ready.")
            return        

    def _get_component_state(self):
        return self.__state