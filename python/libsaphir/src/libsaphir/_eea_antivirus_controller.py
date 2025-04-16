from libsaphir._abstract_antivirus_controller import AbstractAntivirusController
from psec import EtatComposant, Parametres, Cles
from libsaphir import FileStatus
import subprocess, threading, os, json, re

class EeaAntivirusController(AbstractAntivirusController):

    # lxc-attach -n saphir-container-eset -- /opt/eset/eea/bin/odscan -s --profile='@In-depth scan' /bin; echo EXIT_CODE:$?
    # lxc-attach -n saphir-container-eset -- /opt/eset/eea/bin/odscan -s --profile='@In-depth scan' /mnt/storage/benchfile_100ko_1; echo EXIT_CODE:$?

    #__lxc_cmd = ["lxc-attach", "-n", "saphir-container-eset", "--"]
    __state = EtatComposant.UNKNOWN


    def __init__(self):
        super().__init__(
            component_name="ESET", 
            component_description="ESET Endpoint Antivirus controller", 
            max_workers=1)


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
        # Errors management:
        #   - if lxc-attach ends with a return code > 0 then the lxc-attach failed
        #   - if lxc-attach ends with a return code = 0 then the lxc-attach succeeded and the stdout contains information to retrieve the log.
        #
        # The command lslog gives more details about the scan
        #eset_cmd = ["/opt/eset/eea/bin/odscan", "-s", "--profile=@In-depth scan", "--show-scan-info", storage_filepath]
        #proc = subprocess.run(self.__lxc_cmd + eset_cmd, capture_output=True)
        proc = subprocess.run(["/usr/lib/saphir/bin/scan-file.sh", storage_filepath])
        success = False
        details = ""

        # The return code of the command is for the execution of lxc-attach
        if proc.returncode == 0:
            # We extract the scan id from the scan info
            if proc.stdout != "":
                # The scan has completed
                log_name = self.__extract_log_name(proc.stdout.decode().strip())

                if log_name == "":
                    self.error("Une erreur s'est produite durant l'analyse du résultat : {} (log_name est vide)".format(proc.stdout))
                    self.update_status(filepath, FileStatus.FileAnalysisError, 100)
                    return 

                completed, success, details = self.__analyse_log(filepath, log_name)
                if completed:
                    self.publish_result(filepath, success, details)
                else:
                    # L'erreur sera gérée dans __analyse_log
                    return
            else:
                # The scan did not complete
                self.error("Une erreur s'est produite durant l'exécution de l'analyse : {} {}".format(proc.stdout, proc.stderr))
                self.update_status(filepath, FileStatus.FileAnalysisError, 100)
                return                
                            
        else:            
            self.error("Une erreur s'est produite : odscan {} {}.".format(proc.stdout, proc.stderr))
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
        

    def __extract_log_name(self, stdout:str) -> str:
        # Typical stdout:
        #        " 
        #           {
        #               "type":0,
        #               "session_id":6,
        #               "log_name":"ndlnJ78oi"
        #           }
        #        "

        data = json.loads(stdout)
        log_name = data.get("log_name", "")
        return log_name

    def __analyse_log(self, filepath, log_name) -> tuple:
        success = False

        # Typical stdout:
        # Triggered by: root
        # Time started: 04/02/25 20:24:12
        # Time of completion: 04/02/25 20:24:12
        # Duration: 00:00:00
        # Scanned targets: /mnt/storage/benchfile_100ko_1
        # Detections occurred: 0
        # Cleaned: 0
        # Not scanned: 0
        # Scanned: 1

        # Get the log data
        #eset_cmd = ["/opt/eset/eea/sbin/lslog", "--ods-details={}".format(log_name)]
        #proc = subprocess.run(self.__lxc_cmd + eset_cmd, capture_output=True)
        proc = subprocess.run(["/usr/lib/saphir/bin/get-scan-result.sh", log_name])
        if proc.returncode > 0:
            self.error("Une erreur interne s'est produite : lslog {} {}.".format(proc.stdout, proc.stderr))
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            return False, False, ""
        
        if proc.stdout != "":
            completed = True
        else:
            self.error("Une erreur interne s'est produite : journal manquant {} {}.".format(proc.stdout, proc.stderr))
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            return False, False, ""
        
        log_data = proc.stdout.decode().strip()

        re_detections_occurred = re.search(r"Detections occurred:\s*(\d+)", log_data)
        re_scanned = re.search(r"Scanned:\s*(\d+)", log_data)
        re_not_scanned = re.search(r"Not scanned:\s*(\d+)", log_data)

        if re_detections_occurred:
            detections_occurred = int(re_detections_occurred.group(1))
        else:
            detections_occurred = 0

        if re_scanned:
            scanned = int(re_scanned.group(1))
        else:
            scanned = 0

        if re_not_scanned:
            not_scanned = int(re_not_scanned.group(1))
        else:
            not_scanned = 0

        if scanned == 1 and not_scanned == 0:
            success = detections_occurred == 0
            return completed, success, ""
        elif scanned == 0: # and not_scanned > 0:
            self.error("Une erreur interne s'est produite : aucun fichier analysé {} {}.".format(proc.stdout, proc.stderr))
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            return False, False, ""
        
        return False, False, "Cas non géré"


    def _get_component_state(self):
        return self.__state


    def _stop_immediately(self):
        subprocess.run(["/usr/lib/saphir/bin/stop-all-scans.sh"])
        #subprocess.run(self.__lxc_cmd + cmd)


    def _get_component_version(self) -> str:
        proc = subprocess.run(["/usr/lib/saphir/bin/get-eea-version.sh"])
        if proc.returncode == 0:
            return proc.stdout.decode().strip()
        else:
            return "#err"


    def _get_component_description(self) -> str:
        proc = subprocess.run(["/usr/lib/saphir/bin/get-eea-description.sh"])
        if proc.returncode == 0:
            return proc.stdout.decode().strip()
        else:
            return "#err"
        
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
