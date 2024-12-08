from enum import Enum

class FileStatus(Enum):
    FileStatusUndefined, FileAvailableInRepository, FileAnalysing, FileAnalysisError, FileClean, FileInfected = range(6)
