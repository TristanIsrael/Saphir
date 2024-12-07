from libsaphir._abstract_antivirus_controller import AbstractAntivirusController
from psec import EtatComposant, Parametres, Cles
from libsaphir import FileStatus
import subprocess, threading, os

class ClamAntivirusController(AbstractAntivirusController):
    
    __state = EtatComposant.UNKNOWN

    def __init__(self):
        super().__init__("ClamAV", "ClamAV Antivirus controller")

    def _on_api_ready(self) -> None:
        self.info("ClamAV antivirus controller is starting.")        
        self.__state = EtatComposant.STARTING

        # Verify the daemon is ready
        threading.Timer(0.5, self.__ping_clamd).start()
    
    def _analyse_file(self, filepath: str) -> None:
        if self.__state != EtatComposant.READY:
            self.error("The component is not ready.")
            return        
        
        storage_filepath = "{}{}".format(Parametres().parametre(Cles.STORAGE_PATH_DOMU), filepath)

        if not os.path.exists(storage_filepath):
            self.error("The file {} does not exist or is not accessible.".format(storage_filepath))
            return

        self.update_status(filepath, FileStatus.FileAnalysing, 0)

        cmd = ["clamdscan", storage_filepath]        
        proc = subprocess.run(cmd, capture_output=True)
        success = False
        details = ""
        if proc.returncode == 0:
            success = True
        elif proc.returncode == 1:
            success = False
            '''Output example:
              /private/tmp/eicar.txt: Eicar-Signature FOUND\n\n----------- SCAN SUMMARY -----------\nInfected files: 1\nTime: 0.011 sec (0 m 0 s)\nStart Date: 2024:12:04 10:04:36\nEnd Date:   2024:12:04 10:04:36\n', stderr=b'
            '''
            if len(proc.stdout) == 0:
                self.error("Clamdscan command produced no output")
                return
            
            result = proc.stdout.decode().split("\n\n", 1)[0]
            details = result.split(":")[1].strip()
        elif proc.returncode == 2:
            success = False
            details = proc.stderr.decode()
        
        self.publish_result(filepath, success, details)

    def _get_component_state(self):
        return self.__state

    def __ping_clamd(self):
        cmd = ["clamdscan", "--ping", "1"]
        proc = subprocess.run(cmd, capture_output=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode > 0:
            threading.Timer(0.5, self.__ping_clamd).start()
        else:
            self.__state = EtatComposant.READY
            self.debug("Antivirus is ready. The storage path is {}".format(Parametres().parametre(Cles.STORAGE_PATH_DOMU)))
            self.component_state_changed()
