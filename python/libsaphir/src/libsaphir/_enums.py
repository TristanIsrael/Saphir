from enum import Enum

class FileStatus(Enum):
    FileStatusUndefined, GettingFile, FileAvailableInRepository, FileAnalysing, FileAnalysisError, FileClean, FileInfected, FileCopyError, FileCopySuccess = range(9)
