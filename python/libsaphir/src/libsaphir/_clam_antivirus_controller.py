from libsaphir._abstract_antivirus_controller import AbstractAntivirusController
from safecor import ComponentState, Constants
from libsaphir import FileStatus
import subprocess, threading, os

class ClamAntivirusController(AbstractAntivirusController):
    
    __state = ComponentState.UNKNOWN

    def __init__(self):
        super().__init__("ClamAV", "Clam Antivirus controller")

    def _on_api_ready(self) -> None:
        self.info("Clam antivirus controller is starting.")
        self.__state = ComponentState.STARTING

        # Verify the daemon is ready
        threading.Timer(0.5, self.__ping_clamd).start()
    
    def _analyse_file(self, filepath: str) -> None:
        print("CLAMAV analyse file", filepath)
        
        if self.__state != ComponentState.READY:
            self.error("The component is not ready.")
            return
        
        storage_filepath = f"{Constants.DOMU_REPOSITORY_PATH}{filepath}"

        if not os.path.exists(storage_filepath):
            errstr = f"The file {storage_filepath} does not exist or is not accessible."
            self.error(errstr)
            self.publish_result(filepath, False, errstr)
            self.analysis_finished(False)
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
            # Output example:
            #  /private/tmp/eicar.txt: Eicar-Signature FOUND\n\n----------- SCAN SUMMARY -----------\nInfected files: 1\nTime: 0.011 sec (0 m 0 s)\nStart Date: 2024:12:04 10:04:36\nEnd Date:   2024:12:04 10:04:36\n', stderr=b'
            if len(proc.stdout) == 0:
                self.error("Clamdscan command produced no output")
                return
            
            result = proc.stdout.decode().split("\n\n", 1)[0]
            details = result.split(":")[1].strip()
        elif proc.returncode == 2:
            success = False
            details = proc.stderr.decode()
        
        self.publish_result(filepath, success, details)
        self.analysis_finished(True)
        

    def _get_component_state(self):
        return self.__state


    def _stop_immediately(self):
        subprocess.run(["killall", "-9", "clamdscan"])


    def _get_component_version(self) -> str:
        proc = subprocess.run(["clamscan", "--version"], capture_output=True)
        if proc.returncode == 0:
            return proc.stdout.decode().strip()
        else:
            return "#err"

    def _get_component_description(self) -> str:
        proc = subprocess.run("clamconf | sed -n '/Software settings/,$p'", capture_output=True, shell=True)
        if proc.returncode == 0:
            return proc.stdout.decode().strip()
        else:
            return "#err"
        
    def _restart(self, domain_name: str):
        if domain_name != "saphir-av-clamav":
            return

        self.component_state_changed(ComponentState.OFF)
        subprocess.run("reboot", check=False)

    #######################
    ## Private functions
    #
    def __ping_clamd(self):
        
        cmd = ["clamdscan", "--ping", "1"]
        proc = subprocess.run(cmd, capture_output=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode > 0:
            threading.Timer(0.5, self.__ping_clamd).start()
        else:
            self.__state = ComponentState.READY
            self.debug(f"Antivirus is ready. The storage path is {Constants.DOMU_REPOSITORY_PATH}")
            self.component_state_changed()
