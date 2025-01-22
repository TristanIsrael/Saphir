from libsaphir._abstract_antivirus_controller import AbstractAntivirusController
from psec import EtatComposant, Parametres, Cles
from libsaphir import FileStatus
import subprocess, threading, os

class EeaAntivirusController(AbstractAntivirusController):
    
    __lxc_cmd = ["lxc-attach", "-n", "saphir-eset-container", "--"]
    __state = EtatComposant.UNKNOWN


    def __init__(self):
        super().__init__("ESET", "ESET Endpoint Antivirus controller")


    def _on_api_ready(self) -> None:
        self.info("ESET antivirus controller is starting.")        
        self.__state = EtatComposant.STARTING

        # Verify the daemon is ready
        threading.Timer(0.5, self.__ping_eea).start()
    

    def _analyse_file(self, filepath: str) -> None:
        if self.__state != EtatComposant.READY:
            self.error("The component is not ready.")
            return        
        
        storage_filepath = "{}{}".format(Parametres().parametre(Cles.STORAGE_PATH_DOMU), filepath)

        if not os.path.exists(storage_filepath):
            self.error("The file {} does not exist or is not accessible.".format(storage_filepath))
            return

        self.update_status(filepath, FileStatus.FileAnalysing, 0)

        # The command will be executed in the container        
        eset_cmd = ["/opt/eset/eea/sbin/odscan", "-s", "--profile='@In-depth scan'", storage_filepath]
        proc = subprocess.run(self.__lxc_cmd + eset_cmd, capture_output=True)
        success = False
        details = ""
        if proc.returncode == 0:
            success = True
        else:
            success = False
        
        self.publish_result(filepath, success, details)
        

    def _get_component_state(self):
        return self.__state


    def _stop_immediately(self):
        cmd = ["killall", "-9", "odscan"]
        subprocess.run(self.__lxc_cmd + cmd)


    #######################
    ## Private functions
    #
    def __ping_eea(self):
        # We verify whether de LXC container is ready
        cmd = "lxc-info -n saphir-container-eset | grep '^State' | awk '{{print $2}}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode > 0:            
            threading.Timer(0.5, self.__ping_eea).start()
        else:
            state = result.stdout.strip()
            if state == "RUNNING":
                self.__state = EtatComposant.READY
                self.debug("Antivirus is ready. The storage path is {}".format(Parametres().parametre(Cles.STORAGE_PATH_DOMU)))
                self.component_state_changed()
