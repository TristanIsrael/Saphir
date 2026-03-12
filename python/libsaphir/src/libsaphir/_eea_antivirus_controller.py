from libsaphir._abstract_antivirus_controller import AbstractAntivirusController
from safecor import ComponentState, System, Constants
from libsaphir import FileStatus
import subprocess
import threading
import os
import json
import re

class EeaAntivirusController(AbstractAntivirusController):
    """ This is the controller for ESET Endpoint Antivirus 
    
    The analysis is made in two synchronous steps:
    1 - Start the scan (odscan)
    2 - Verify the log (lslog)
    """

    # lxc-attach -n saphir-container-eset -- /opt/eset/eea/bin/odscan -s --profile='@In-depth scan' /bin; echo EXIT_CODE:$?
    # lxc-attach -n saphir-container-eset -- /opt/eset/eea/bin/odscan -s --profile='@In-depth scan' /mnt/storage/benchfile_100ko_1; echo EXIT_CODE:$?

    #__lxc_cmd = ["lxc-attach", "-n", "saphir-container-eset", "--"]
    __state = ComponentState.UNKNOWN
    #__analysis_running = []


    def __init__(self):
        super().__init__(
            component_name="ESET",
            component_description="ESET Endpoint Antivirus controller",
            max_workers=1
        )

        #threading.Timer(0.5, self.__monitor_analysis).start()


    def _on_api_ready(self) -> None:
        self.info("ESET antivirus controller is starting.")
        self.__state = ComponentState.STARTING

        # Verify the daemon is ready
        threading.Timer(0.5, self.__ping_eea).start()
    

    def _analyse_file(self, filepath: str) -> None:
        if self.__state != ComponentState.READY:
            self.error("The component is not ready.")
            
            self.analysis_finished(False)
            return
        
        #storage_filepath = "{}{}".format(Parametres().parametre(Cles.STORAGE_PATH_DOMU), filepath)
        storage_filepath = f"{Constants.DOMU_REPOSITORY_PATH}{filepath}"

        if not os.path.exists(storage_filepath):
            self.error(f"The file {storage_filepath} does not exist or is not accessible.")
            
            self.analysis_finished(False)
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
        proc = subprocess.run(["/usr/lib/saphir/bin/scan-file.sh", storage_filepath], capture_output=True)

        # The return code of the command is for the execution of lxc-attach
        if proc.returncode == 0:
            # We extract the scan id from the scan info
            if proc.stdout != "" and proc.stdout is not None:
                # The scan has completed
                log_name = self.__extract_log_name(proc.stdout.decode().strip())

                if log_name == "":
                    msg = f"An error occured during the scan of {filepath}"
                    self.error(f"An error occured during the analysis of the result: {proc.stdout} (log_name is empty)")
                    self.update_status(filepath, FileStatus.FileAnalysisError, 100)
                    self.publish_result(filepath, False, msg)

                    self.analysis_finished(False)
                    return
                
                # Now we analyse the log
                _, success, details = self.__analyse_log(filepath, log_name)
                status = FileStatus.FileClean if success else FileStatus.FileInfected
                # What if the analysis has not completed?
                self.update_status(filepath, status, 100)
                self.publish_result(filepath, success, details)
                self.analysis_finished(success)
                return
            else:
                # The scan did not complete                
                self.error(f"An error occured during the scan of the file {filepath} : stdout={proc.stdout}, stderr={proc.stderr}")
                self.update_status(filepath, FileStatus.FileAnalysisError, 100)
                self.publish_result(filepath, False, "An error occured during the analysis.")

                self.analysis_finished(False)
                return
        else:
            msg = f"An error occured: {self.__translate_odscan_return(proc.returncode)} ({proc.returncode})."
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            self.publish_result(filepath, False, msg)

            self.analysis_finished(False)
            return

    #def __monitor_analysis(self) -> None:
    #    ''' This function monitors ESET with the currently running analysis. 
    #
    #    When a analysis is finished it gets the information about the status and generates the
    #    notification to the system.
    #    '''
    #
    #    # We loop into the list of analysis running
    #    # We work on a copy of the list
    #    for work in self.__analysis_running[:]:
    #        filepath = work.get("filepath", "")
    #        log_name = work.get("log_name", "")
    #
    #        if filepath == "" or log_name == "":
    #            print("Error: filepath or log_name is empty")
    #            continue
    #
    #        completed, success, details = self.__analyse_log(filepath, log_name)
    #        if completed:
    #            # If completed we publish the result
    #            self.publish_result(filepath, success, details)
    #            # and we remove the analysis from the list
    #            self.__analysis_running.remove(work)
    #    
    #    threading.Timer(0.5, self.__monitor_analysis).start()

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
        ''' Verifies the scan log

        When the Completed field in the returned tuple is True it means that the analysis
        is finished and should not be monitored again.

        @return tuple (Completed:bool, Success:bool, Details:str)
        '''

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
        print(f"Analyze log of {log_name}")

        proc = subprocess.run(["/usr/lib/saphir/bin/get-scan-result.sh", log_name], capture_output=True)
        if proc.returncode > 0:
            self.debug(f"An internal error occured with lslog: {proc.stdout} {proc.stderr}.")
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            self.publish_result(filepath, False, "Une erreur interne s'est produite")
            return True, False, "Internal error"
        
        if proc.stdout == "":            
            self.debug(f"An internal error occured: missing log: {proc.stdout} {proc.stderr}.")
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            self.publish_result(filepath, False, "Une erreur interne s'est produite.")
            return True, False, "Missing log file"
        
        log_data = proc.stdout.decode().strip()

        # We first verify whether the scan is completed
        re_time_of_completion = re.search(r"Time of completion:\s*(\d+)", log_data)
        if not re_time_of_completion:
            # not completed
            print("missing time of completion")
            return False, False, ""
        else:
            time_of_completion = str(re_time_of_completion.group(1)).strip()
            if time_of_completion == "":
                # The analysis is not finished
                print("not finished")
                return False, False, ""

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

        # A file can contain multiple files so scanned can be > 1
        if scanned >= 1:
            success = detections_occurred == 0
            print(success)
            return True, success, f"Scanned files: {scanned}, Not scanned: {not_scanned}, Detections: {detections_occurred}"
        elif scanned == 0:
            print("error") 
            self.debug(f"An internal error occured. No file analysed {proc.stdout} {proc.stderr}.")
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            self.publish_result(filepath, False, "Une erreur interne s'est produite.")
            return True, False, "Internal error"
        
        print("non handled")
        return True, False, "Unhandled case"


    def _get_component_state(self):
        return self.__state


    def _stop_immediately(self):
        subprocess.run(["/usr/lib/saphir/bin/stop-all-scans.sh"])
        #subprocess.run(self.__lxc_cmd + cmd)


    def _get_component_version(self) -> str:
        proc = subprocess.run(["/usr/lib/saphir/bin/get-eea-version.sh"], capture_output=True)
        if proc.returncode == 0:
            if proc.stdout is not None:
                return proc.stdout.decode().strip()
        
        return "#err"


    def _get_component_description(self) -> str:
        description = "No information"
        licence = "No licence"

        # Get information about the binary
        proc = subprocess.run(["/usr/lib/saphir/bin/get-eea-description.sh"], capture_output=True)
        if proc.returncode == 0:
            if proc.stdout is not None:
                description = proc.stdout.decode().strip()
                #return proc.stdout.decode().strip()

        # Get information about the licence
        proc = subprocess.run(["/usr/lib/saphir/bin/get-eea-licence.sh"], capture_output=True)
        if proc.returncode == 0:
            if proc.stdout is not None:
                licence = proc.stdout.decode().strip()

        return f"{description}\nLicence information:\n{licence}"

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
                self.__state = ComponentState.READY
                self.debug(f"Antivirus is ready. The storage path is {Constants.DOMU_REPOSITORY_PATH}")
                self.component_state_changed()

    def __translate_odscan_return(self, returncode:int) -> str:
        if returncode == 0:
            return "no error"
        elif returncode == 1:
            return "malware found"
        elif returncode == 10:
            return "imcomplete analysis"
        elif returncode == 50:
            return "malware detected"
        elif returncode == 100:
            return "general error"
        
        return "unknown error"
