from enum import Enum

class FileStatus(Enum):
    FileStatusUndefined, FileAvailableInRepository, FileAnalysing, FileAnalysisError, FileClean, FileInfected, FileCopyError, FileCopySuccess = range(8)
