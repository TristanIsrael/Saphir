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

    See also: https://help.eset.com/essl/91/fr-FR/on_demand_scan_via_terminal.html
    """    

    def __init__(self):
        super().__init__(
            component_name="ESET",
            component_description="ESET Endpoint Antivirus controller",
            max_workers=1
        )

        self.__state = ComponentState.UNKNOWN


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

        details = self.__get_log_details_from_stdout(filepath, proc.stdout)

        # The file is clean if return code is 0
        # The file is infected if return code is 50
        # The file has not been fully analyzed if return code is 10
        if proc.returncode == 0:
            # File is clean
            self.update_status(filepath, FileStatus.FileClean, 100)
            self.publish_result(filepath, True, details)
            self.analysis_finished(True)
        elif proc.returncode == 10:
            # Incomplete scan
            self.update_status(filepath, FileStatus.FileClean, 100)
            self.publish_result(filepath, True, details)
            self.analysis_finished(True)
        elif proc.returncode == 50:
            # Threats detected
            self.update_status(filepath, FileStatus.FileInfected, 100)
            self.publish_result(filepath, False, details)
            self.analysis_finished(False)
        else:
            msg = f"An error occured: {self.__translate_odscan_return(proc.returncode)} ({proc.returncode})."
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            self.publish_result(filepath, False, msg)
            self.analysis_finished(False)
        
    def __get_log_details_from_stdout(self, filepath, stdout:bytes) -> str:
        if stdout != "" and stdout is not None:
            log_name = self.__extract_log_name(stdout.decode().strip())

            if log_name == "":
                msg = f"An error occured during the scan of {filepath}"
                self.error(f"An error occured during the analysis of the result: {stdout} (log_name is empty)")
                self.update_status(filepath, FileStatus.FileAnalysisError, 100)
                self.publish_result(filepath, False, msg)

                self.analysis_finished(False)
                return "An error occured with the log"
            
            # Now we analyse the log for information only, the scan status is given by the result code
            return self.__analyse_log(filepath, log_name)                
        else:
            # We have no log?... but it is not blocking
            self.error(f"The scan of {filepath} misses log information: stdout={stdout}")
            return "The scan has not log"

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

    def __analyse_log(self, filepath, log_name) -> str:
        ''' Verifies the scan log

        When the Completed field in the returned tuple is True it means that the analysis
        is finished and should not be monitored again.

        Typical stdout (return code 0 or 50):
          Triggered by: root
          Time started: 04/02/25 20:24:12
          Time of completion: 04/02/25 20:24:12
          Duration: 00:00:00
          Scanned targets: /mnt/storage/benchfile_100ko_1
          Detections occurred: 0 -> or more if return code is 50
          Cleaned: 0
          Not scanned: 0
          Scanned: 1

        or (return code 10):
          Triggered by: root
          Time started: 04/02/25 20:24:12
          Time of completion: 04/02/25 20:24:12
          Duration: 00:00:00
          Scanned targets: /mnt/storage/benchfile_100ko_1
          Detections occurred: 0
          Cleaned: 0
          Not scanned: 10
          Scanned: 100

        @return a string containing the text details about the scan
        '''

        # Get the log data
        print(f"Analyze the log of {log_name}")

        proc = subprocess.run(["/usr/lib/saphir/bin/get-scan-result.sh", log_name], capture_output=True)
        if proc.returncode > 0:
            self.debug(f"An internal error occured with lslog: {proc.stdout} {proc.stderr}.")
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            self.publish_result(filepath, False, "Une erreur interne s'est produite")
            return "Internal error"
        
        if proc.stdout == "":            
            self.debug(f"An internal error occured: missing log: {proc.stdout} {proc.stderr}.")
            self.update_status(filepath, FileStatus.FileAnalysisError, 100)
            self.publish_result(filepath, False, "Une erreur interne s'est produite.")
            return "Missing log file"
        
        log_data = proc.stdout.decode().strip()

        # We first verify whether the scan is completed
        #re_time_of_completion = re.search(r"Time of completion:\s*(\d+)", log_data)
        #if not re_time_of_completion:
        #    # not completed
        #    print("missing time of completion")
        #    return ""
        #else:
        #time_of_completion = str(re_time_of_completion.group(1)).strip()
        #    if time_of_completion == "":
        #        # The analysis is not finished
        #        print("not finished")
        #        return False, False, ""

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
        #success = detections_occurred == 0
        #print(success)
        details = f"Scanned files: {scanned}, Not scanned: {not_scanned}, Detections: {detections_occurred}"
        print(details)
        return details
        #elif scanned == 0:
        #    print("error") 
        #    self.debug(f"An internal error occured. No file analysed {proc.stdout} {proc.stderr}.")
        #    self.update_status(filepath, FileStatus.FileAnalysisError, 100)
        #    self.publish_result(filepath, False, "Une erreur interne s'est produite.")
        #    return True, False, "Internal error"
        
        #print("non handled")
        #return True, False, "Unhandled case"


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
