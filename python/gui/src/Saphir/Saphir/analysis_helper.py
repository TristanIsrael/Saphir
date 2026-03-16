from libsaphir import FileStatus

class AnalysisHelper(): 

    @staticmethod
    def update_file_result(files:dict, filepath:str, success:bool, av_component:str, details:str, analysis_components:list) -> tuple[bool, int]:
        """ Updates the result of the analysis in the files queue         
        """
        
        file = files[filepath]
        AnalysisHelper.__update_file_fields(file, success, av_component, details, analysis_components)
        
        clean = AnalysisHelper.evaluate_result_consensus(file)
        if AnalysisHelper.is_analysis_finished(files, filepath):
            if clean:
                file["status"] = FileStatus.FileClean
            else:
                file["status"] = FileStatus.FileInfected

            # Now we unlock the file
            #file["locked"] = False
        else:
            file["status"] = FileStatus.FileAnalysing
                
        return clean, file.get("size", 0)

    @staticmethod
    def update_archive_result(archive_file:dict, filepath: str, success:bool, av_component:str, details:str, analysis_components:list) -> tuple[bool, int]:
        """ Updates the result of the analysis for a file located in an archive """
        
        # First we update the fields of the file inside the archive
        file = AnalysisHelper.get_file_in_archive(archive_file, filepath)        
        AnalysisHelper.__update_file_fields(file, success, av_component, details, analysis_components)

        # We have to update the archive progress too
        archive_file["progress"] = AnalysisHelper.calculate_archive_progress(archive_file)

        # The status of the archive depends on its files results
        clean = AnalysisHelper.evaluate_result_consensus_archive(archive_file)
        if AnalysisHelper.get_archive_progress(archive_file) == 100.0:
            if clean:
                archive_file["status"] = FileStatus.FileClean            
            else:
                archive_file["status"] = FileStatus.FileInfected

            # Now we unlock the file
            #file["locked"] = False
        else:
            archive_file["status"] = FileStatus.FileAnalysing        
            
        return clean, archive_file.get("size", 0)
        
    @staticmethod
    def get_file_progress(files:dict, filepath:str) -> float:
        """ Returns the analysis progress for the file. 
        
        The progress must have been calculated before
        """

        file = files[filepath]
        return file.get("progress", 0)
    
    @staticmethod
    def get_archive_progress(archive_file:dict) -> float:
        """ Returns the analysis progress for the archive. 
        
        The progress must have been calculated before
        """

        return archive_file.get("progress", 0)

    @staticmethod
    def is_analysis_finished(files:dict, filepath:str) -> bool:
        """ Indicated whether all the analysis components have finished analysing the file """

        file = files.get(filepath, {})
        return file.get("progress", 0) == 100.0

    @staticmethod
    def __update_file_fields(file:dict, success:bool, av_component:str, details:str, analysis_components:list):
        """ Updates the fields for the file after an analysis
        
        If all the analysis components have finished working the progress will be 100.0, otherwise the 
        progress will be equal to the proportion of components that have finished working.

        +args
        """

        results = file.get("results", {})
        av = results.get(av_component, {})

        # Premier passage : pas d'état pour le fichier, on prend le nouvel état
        # Deuxième passage : si le fichier était clean et qu'il ne l'est plus alors il passe à infecté
        #                    si le fichier n'était pas clean, on ne tient pas compte de son nouvel état
        av["result"] = "Clean" if success else "Infected"
        av["details"] = details
        results[av_component] = av
        file["results"] = results

        progress = 0 if len(analysis_components) == 0 else 100 * len(results) / len(analysis_components)
        file["progress"] = progress        

    @staticmethod
    def get_file_in_archive(archive_file:dict, filepath:str) -> dict:
        """ Returns the information of a file located in an archive """

        return archive_file.get("content", {}).get(filepath, {})

    @staticmethod
    def evaluate_result_consensus(file:dict) -> bool:
        """ Evaluates whether the file is clean or not.

        The analysis results are checked and if there is one failure the file
        is declared infected.
        """

        results = file.get("results", {})
    
        for entry in results.values():
            if entry.get("result") == "Infected":
                return False
            
        return True
    
    @staticmethod
    def evaluate_result_consensus_archive(archive_file:dict) -> bool:
        """ Evaluates whether the file located in an archive is clean or not.
        
        The decision is made by the function :func:`evaluate_result_consensus`.
        """

        clean = True
        
        for f in list(archive_file.get("content", {}).values()):
            clean = clean and AnalysisHelper.evaluate_result_consensus(f)

        return clean
    
    @staticmethod
    def calculate_archive_progress(archive_file:dict) -> float:
        """ Calculates the progress of the whole archive """

        # We calculate the mean of the progress of the files
        nb_files = len(archive_file.get("content", {}))
        sum_progress = 0.0

        for file in list(archive_file.get("content", {}).values()):
            sum_progress = sum_progress + file.get("progress", 0.0)

        return sum_progress / nb_files

    @staticmethod
    def is_file_completed(file:dict) -> bool:
        """ Returns whether the analysis is finished on a file 
        
        The analysis is finished when the progress is 100% or when the status is clean, 
        infected or error.
        """

        progress = file.get("progress", 0)
        status = file.get("status", FileStatus.FileStatusUndefined)
        
        return progress == 100 \
            or status in [
                FileStatus.FileAnalysisError,
                FileStatus.FileClean,
                FileStatus.FileCopyError,
                FileStatus.FileInfected
                ]

    @staticmethod
    def get_repository_size(files:dict):
        """ The repository size depends on the files currently locked in and not started 
        
        The files that have been requested for download are counted so they are virtually in
        the repository even when there are not currently downloaded or fully downloaded.
        """
        
        count = sum(1 for d in files.values() if d.get("locked", False))
        return count
