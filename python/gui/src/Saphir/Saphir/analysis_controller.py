from PySide6.QtCore import QObject, Property, Signal
from . import AnalysisState, AnalysisMode, AnalysisHelper
from libsaphir import TOPIC_ANALYSIS, FileStatus, BIG_FILE_SIZE_IN_MB, MOUNT_ARCHIVES
from safecor import Api, Topics, MqttHelper, Constants, FileHelper, DiskState
import threading
from threading import Lock
import time

class AnalysisController(QObject):
    ''' Cette classe contrôle la façon dont se déroule l'analyse des fichiers
    sélectionnés par l'utilisateur.

    En fonction des capacité de la machine, l'analyse peut être parallélisée ou 
    séquentielle et utiliser plus ou moins en ressources.
    '''

    __analysis_state = AnalysisState.AnalysisStopped
    __files:dict
    __analysis_components = []
    __repository_capacity = 1
    #__repository_size = 0
    __files_copy_queue_size = 0
    __start_times = {}
    __clean_files_count = 0
    __clean_files_size = 0
    __infected_files_count = 0
    __infected_files_size = 0
    __archive_mounted_name = None
    __archive_mounted_filepath = None
    __archive_file = {}
    __queue_lock = Lock()
    __repository_lock = Lock()

    # Signals
    stateChanged = Signal(AnalysisState)
    resultsChanged = Signal()
    fileUpdated = Signal(str, list)
    systemUsed = Signal()
    iterationDone = Signal(float)

    def __init__(self, files:dict, analysis_components:list, source_disk:str, analysis_mode_:AnalysisMode, parent:QObject|None=None) -> None:
        """ Instanciates a new Analysis controller
        
        The files list is provided by the Application controller and is a reference.
        """
        QObject.__init__(self, parent)

        self.__files = files
        self.__source_disk = source_disk
        self.__analysis_components = analysis_components
        self.__analysis_mode = analysis_mode_

        Api().add_message_callback(self.__on_api_message)
        Api().subscribe(Topics.NEW_FILE)
        Api().subscribe(Topics.DELETED_FILE)
        #Api().subscribe(Topics.ERROR)
        Api().subscribe(f"{TOPIC_ANALYSIS}/response")
        Api().subscribe(f"{TOPIC_ANALYSIS}/status")
        Api().subscribe(f"{TOPIC_ANALYSIS}/error")
        Api().subscribe(f"{Topics.SYSTEM_INFO}/response")
        Api().subscribe(Topics.DISK_STATE)
        Api().subscribe(f"{Topics.LIST_FILES}/response")

        # On demande les infos sur le système parce qu'on veut affiner le nombre
        # de fichiers analysés en même temps
        Api().request_system_info()

    def set_source_disk(self, source_disk:str):
        self.__source_disk = source_disk

    def start_analysis(self) -> None:
        Api().info("Starting the analysis", "AnalysisController")

        self.__set_analysis_state(AnalysisState.AnalysisRunning)
        self.__files_copy_queue_size = 0
        Api().publish(f"{TOPIC_ANALYSIS}/resume", {})

        # Itération sur la liste des fichiers de façon asynchrone
        # pour copier les fichiers dans le dépôt au fur et à mesure
        # à concurrence de la place disponible dans le dépôt
        threading.Timer(0.5, self.__do_copy_files_into_repository).start()

    def stop_analysis(self) -> None:
        Api().info("Stopping the analysis", "AnalysisController")
        Api().publish(f"{TOPIC_ANALYSIS}/stop", {})
        Api().clear_sys_usb_queues()
        self.__set_analysis_state(AnalysisState.AnalysisStopped)

    def reset(self):
        self.__clean_files_count = 0
        self.__clean_files_size = 0
        self.__infected_files_count = 0
        self.__infected_files_size = 0
        self.__files_copy_queue_size = 0
        self.__start_times = {}
        self.__repository_size = 0


    ######
    ## Private functions
    #
    def __on_api_message(self, topic:str, payload:dict) -> None:
        #Api().debug("Message received on topic {}".format(topic), "AnalysisController")
        #print("[AnalysisController]", topic, payload)
        
        if topic == Topics.NEW_FILE:
            if not MqttHelper.check_payload(payload, ["disk", "filepath"]):
                Api().error(f"Malformed message for topic {topic}")
                return
            
            disk = payload.get("disk")

            if disk != Constants.STR_REPOSITORY:
                # We ignore the files if they are not in the source disk
                return

            filepath = payload.get("filepath", "")
            fingerprint = payload.get("source_fingerprint", "")
            
            self.__on_file_available(filepath, fingerprint)
        elif topic == f"{TOPIC_ANALYSIS}/response":
            if not MqttHelper.check_payload(payload, ["component", "filepath", "success", "details"]):
                Api().error(f"Malformed message for topic {topic}")
                return
                        
            self.__handle_result(payload.get("component", ""), payload.get("filepath", ""), payload.get("success", False), payload.get("details", ""))
        elif topic == f"{TOPIC_ANALYSIS}/status":
            return # Ignored
            if not MqttHelper.check_payload(payload, ["filepath", "status", "progress"]):
                Api().error(f"Malformed message for topic {topic}")
                return
            
            self.__handle_status(payload.get("filepath", ""), FileStatus(payload.get("status", 0)), payload.get("progress", 0))
        elif topic == f"{TOPIC_ANALYSIS}/error":
            if not MqttHelper.check_payload(payload, ["disk", "filepath", "error"]):
                # On filtre pour ne pas provoquer de boucle infinie
                return
            
            self.__handle_error(payload)
        elif topic == f"{Topics.SYSTEM_INFO}/response":
            if not MqttHelper.check_payload(payload, ["system"]):
                Api().warn(f"Wrong response format for system info response. Using {self.__repository_capacity} scans in parallel.")
                return
            
            self.__handle_sysinfo(payload)
        elif topic == Topics.DISK_STATE:
            if not MqttHelper.check_payload(payload, ["disk", "state"]):
                Api().error(f"Malformed message for topic {topic}")
                return
            
            disk = payload.get("disk", "")
            state = payload.get("state", "")
            
            # We only monitor the state mounted for the archives
            if state == DiskState.MOUNTED.value:
                self.__on_archive_mounted(disk)
        elif topic == f"{Topics.LIST_FILES}/response":
            # We only monitor this message when we mounted an archive before
            if self.__archive_mounted_name is None:
                return
            
            if not MqttHelper.check_payload(payload, ["disk", "files"]):
                Api().error(f"Malformed message for topic {topic}")
                return
            
            disk = payload.get("disk", "")
            files = payload.get("files", [])

            self.__on_list_files_received(disk, files)
        elif topic == Topics.DELETED_FILE:
            if not MqttHelper.check_payload(payload, ["disk", "filepath"]):
                Api().error(f"Malformed message for topic {topic}")
                return
            
            disk = payload.get("disk", "")
            filepath = payload.get("filepath", "")

            if disk == Constants.STR_REPOSITORY:
                self.__on_deleted_file(disk, filepath)


    def __on_file_available(self, filepath:str, fingerprint:str) -> None:
        with self.__queue_lock:            
            self.__files_copy_queue_size -= 1

            try:
                # If any file has been read the system becomes dirty
                self.systemUsed.emit()

                file = self.__files[filepath] if self.__archive_mounted_name is None else self.__archive_file.get("content", {}).get(filepath, {})

                file["status"] = FileStatus.FileAvailableInRepository
                file["fingerprint"] = fingerprint
                self.fileUpdated.emit(filepath, ["status"])

                # Next step is to analyse the file
                payload = {
                    "filepath": filepath
                }
                Api().publish(f"{TOPIC_ANALYSIS}/request", payload)
            except Exception as e:
                print("An error occured when handling the new_file notification")
                print(e)

    def __on_deleted_file(self, disk:str, filepath:str):
        print(f"The file {filepath} has been removed from the repository")

        with self.__queue_lock:
            file = self.__files[filepath]
            file["locked"] = False

    def __on_list_files_received(self, disk:str, files:list):
        with self.__queue_lock:
            # If we receive a files list, it means that we have mounted a disk
            if len(files) > 0:
                for file in files:
                    if file["type"] == "folder":
                        continue

                    file["disk"] = disk
                    filepath = f"{file.get("path")}{"/" if file.get("path") != "/" else ""}{file.get("name")}"
                    file["filepath"] = filepath
                    file["status"] = FileStatus.FileStatusUndefined
                    file["selected"] = True
                    file["inqueue"] = True
                    
                    # Update the files list
                    if "content" in self.__archive_file:
                        archive_content = self.__archive_file["content"]
                    else:
                        self.__archive_file["content"] = {}
                        archive_content = self.__archive_file["content"]
                    
                    archive_content[filepath] = file

    def __on_archive_mounted(self, disk:str):
        # When an archive has been mounted we need to query its files list
        # And insert them into the analysis queue
        self.__archive_mounted_name = disk
        file = self.__files.get(self.__archive_mounted_filepath, {})
        self.__archive_file = file
        Api().get_files_list(disk, True)

    def __handle_sysinfo(self, payload:dict):
        # We look at the CPU count in the system information
        system_info = payload.get("system", {})
        machine_info = system_info.get("machine", {})
        cpu_info = machine_info.get("cpu", {})
        #cpu_count = cpu_info.get("count", self.__repository_capacity)
        #because of bug #54
        cpu_count = 8

        # TODO: en théorie il faudrait que la quantité de fichiers analysés en parallèle
        # corresponde à la quantité de coeurs divisée par la quantité d'antivirus utilisés.
        # Pour l'instant, nous sommes en phase d'obervation et l'algorithme sera ajusté
        # en fonction des performances observées.
        self.__repository_capacity = cpu_count

        Api().info(f"Repository capacity is set to {self.__repository_capacity} files")


    def __handle_status(self, filepath:str, status:FileStatus, progress:int):
        return # Unused
        '''
        with self.__queue_lock:
            if self.__archive_mounted_name is not None:
                # If this is an archive we ignore the status
                return
            
            file = self.__files[filepath]
            file["status"] = status

            if progress > file.get("progress", 0):
                file["progress"] = progress
            
            self.fileUpdated.emit(filepath, ["progress"])'''
        

    def __handle_result(self, component:str, filepath:str, success:bool, details:str):
        # We work in a critical sectionn because this function may be called by
        # multiple threads at the same time
        with self.__queue_lock:
            # If the file is in an archive we put the results in the file content field
            # We gather all the results inside this file entity
            if self.__archive_mounted_name is None:
                clean, file_size = AnalysisHelper.update_file_result(self.__files, filepath, success, component, details, self.__analysis_components)            
                self.fileUpdated.emit(filepath, ["status", "progress"])
            else:
                clean, file_size = AnalysisHelper.update_archive_result(self.__archive_file, filepath, success, component, details, self.__analysis_components) 
                # We update the status only at the end
                self.fileUpdated.emit(self.__archive_mounted_filepath, ["progress"])
            
            if self.__archive_mounted_name is None:
                # If this is a regular file
                if AnalysisHelper.is_analysis_finished(self.__files, filepath):
                    if clean:
                        self.__clean_files_count += 1
                        self.__clean_files_size += file_size
                    else:
                        self.__infected_files_count += 1
                        self.__infected_files_size += file_size
                    
                    start_time = self.__start_times.get(filepath, time.time())
                    duration = time.time() - start_time
                    self.iterationDone.emit(duration)

                    self.resultsChanged.emit()

                    # Free the slot in the repository
                    Api().delete_file(filepath, Constants.STR_REPOSITORY)
            else:
                file = AnalysisHelper.get_file_in_archive(self.__archive_file, filepath)
                if file.get("progress", 0) == 100:
                    # Free the slot in the repository for the file in the archive
                    Api().delete_file(filepath, Constants.STR_REPOSITORY)

                # If this is a file in an archive
                if self.__archive_file.get("progress", 0) == 100:
                    if clean:
                        self.__clean_files_count += 1
                        self.__clean_files_size += file_size
                    else:
                        self.__infected_files_count += 1
                        self.__infected_files_size += file_size

                    self.fileUpdated.emit(self.__archive_mounted_filepath, ["status", "progress"])
                    self.resultsChanged.emit()

                    # We finished analyzing the image so we clean...
                    Api().unmount(self.__archive_mounted_name)
                    self.__archive_mounted_name = None
                    self.__archive_mounted_filepath = None
                    self.__archive_file = {}

                    start_time = self.__start_times.get(filepath, time.time())
                    duration = time.time() - start_time
                    self.iterationDone.emit(duration)                

                # Free the slot in the repository for the archive
                #Api().delete_file(self.__archive_mounted_filepath, Constants.STR_REPOSITORY)
                #self.__repository_size = self.__repository_size - 1 # TODO: asynchronously after the file has been deleted                    

            #print(f"File {filepath}, status={"clean" if clean else "infected"}, success={success}, component={component}")        

    def __handle_error(self, payload):
        print("Error received:", payload)

        '''filepath = payload.get("filepath", "")

        file = self.__files[filepath]
        
        #Api().warn(f"There was an error with the file {filepath}: {error}")
        file["status"] = FileStatus.FileAnalysisError
        file["progress"] = 100
        self.__infected_files_count += 1
        self.__infected_files_size += file["size"]
        self.fileUpdated.emit(filepath, ["status", "progress"])
        self.resultsChanged.emit()

        Api().delete_file(filepath, Constants.STR_REPOSITORY)
        self.__repository_size -= 1'''

    
    def __do_copy_files_into_repository(self):
        # We copy files in the repository until it is full (__repository_size)
        # We handle a local value to avoid sending queries to Safecor
        limit = self.__get_repository_free_slots()

        if limit <= 0:
            threading.Timer(0.5, self.__do_copy_files_into_repository).start()
            return

        files = self.__get_next_group_of_files(limit)
        print("group limit", limit)
        print("next group:", files)

        with self.__queue_lock:
            for file in files:
                file["locked"] = True

                if file.get("inqueue", False) or self.__analysis_mode == AnalysisMode.AnalyseWholeSource:
                    filepath = file.get("filepath", None)

                    if filepath is None:
                        continue
                    
                    if MOUNT_ARCHIVES and BIG_FILE_SIZE_IN_MB > -1 and file.get("size", 0) > BIG_FILE_SIZE_IN_MB and FileHelper.is_archive_file(file["name"]):
                        # If the file is big and is an archive we mount it
                        # If there is an archive inside an archive there will be problems...
                        file["status"] = FileStatus.FileAnalysing
                        self.fileUpdated.emit(self.__archive_mounted_name, [file["status"]])
                        self.__archive_mounted_filepath = file["filepath"]
                        Api().mount_file(self.__source_disk, file["filepath"])
                    else:
                        file["status"] = FileStatus.FileAnalysing

                        if self.__archive_mounted_name is None:
                            self.fileUpdated.emit(filepath, [file["status"]])
                        else:
                            self.fileUpdated.emit(self.__archive_mounted_name, [file["status"]])

                        source_disk = self.__source_disk if self.__archive_mounted_name is None else self.__archive_mounted_name

                        Api().read_file(source_disk, filepath)
                        
                        self.__start_times[filepath] = time.time()
                        self.__files_copy_queue_size += 1
                            
        if self.__analysis_state == AnalysisState.AnalysisRunning and (len(self.__files) > 0 or len(self.__archive_file.get("content", {})) > 0):
            threading.Timer(0.5, self.__do_copy_files_into_repository).start()
        else:
            print("No more file to analyse... Exiting loop")

    def __get_repository_free_slots(self):
        """
        Returns the free slots in the repository, which means the number of files
        that can be downloaded before the repository is full.

        The goal is to fill the repository but not overflow it.
        """

        nb_files = self.__repository_capacity - AnalysisHelper.get_repository_size(self.__files)
        #print("free slots=", nb_files)
        return nb_files

    def __get_next_group_of_files(self, size_limit):
        """ Returns a new group of files to analyze

        The quantity of files depends on the argument size_limit provided.
        To avoid unexpected behaviours the single files are provided before the archives
        and only one archive is provided at a time.
        An archive is returned only when there is no other file currently being analyzed        
        """

        group = []
        files_list = self.__files if self.__archive_mounted_name is None else self.__archive_file.get("content", {})

        # First of all we filter the files to consider only those whose state 
        # is "undefined" in the workflow
        filtered = {k:f for k,f in files_list.items() if not f.get("locked", False) and f.get("status", FileStatus.FileStatusUndefined) == FileStatus.FileStatusUndefined}
        
        for f in filtered.values():
            # First we get the next non-archive files that is not currently being analyzed
            if not FileHelper.is_archive_file(f.get("name", "")):
                group.append(f)
            else:
                # If this is an archive
                if MOUNT_ARCHIVES and f.get("size", 0) > BIG_FILE_SIZE_IN_MB:
                    # If the file has to be mounted
                    continue 
                else:
                    # If we don't mount archives, we simply add the file
                    group.append(f)
                        
            if len(group) >= size_limit:
                # We stop adding files when the queue is full
                break

        # If the group is empty and we still have archives we put them
        # one by one after their analysis is completed
        # The repository size is not reliable because the file may be
        # being read when the function is called again. So we use
        # another property that indicates that the analysis is ongoing
        # on that file.
        if MOUNT_ARCHIVES and len(group) == 0 and AnalysisHelper.get_repository_size(self.__files) == 0 and self.get_working_files_count() == 0:
            for f in filtered.values():
                if FileHelper.is_archive_file(f.get("name", "")) and not AnalysisHelper.is_file_completed(f):
                    group.append(f)
                    break # We return only one archive

        #print("next group of files:", group)

        return group

    def get_working_files_count(self) -> int:
        """ Returns the number of files currently being worked on
        
        Those files are in a state different from Undefined
        """

        files_list = self.__files if self.__archive_mounted_name is None else self.__archive_file.get("content", {})
        
        return len(
            {k:f for k,f in files_list.items() if
                f.get("status", None) in [
                    FileStatus.FileAnalysing,
                    FileStatus.FileAvailableInRepository,
                    FileStatus.FileCopySuccess
                    ]
            }
        )
    
    ######
    ## Getters and setters
    #
    def get_analysis_state(self) -> AnalysisState:
        return self.__analysis_state
    
    def get_clean_files_count(self) -> int:
        return self.__clean_files_count
    
    def get_clean_files_size(self) -> int:
        return self.__clean_files_size
    
    def get_infected_files_count(self) -> int:
        return self.__infected_files_count
    
    def get_infected_files_size(self) -> int:
        return self.__infected_files_size
    
    def __set_analysis_state(self, state:AnalysisState):
        self.__analysis_state = state
        self.stateChanged.emit(state)

    def get_repository_capacity(self):
        return self.__repository_capacity    

        #with self.__repository_lock:
        #    return self.__repository_size
        
    #def inc_repository_size(self):
    #    with self.__repository_lock:
    #        self.__repository_size += 1

    #def dec_repository_size(self):
    #    with self.__repository_lock:
    #        self.__repository_size -= 1
    
    def get_queue_size(self):
        return len(self.__files)
    
    state = Property(int, get_analysis_state, notify= stateChanged)
