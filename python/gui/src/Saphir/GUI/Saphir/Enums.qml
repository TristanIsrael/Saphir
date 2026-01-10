pragma Singleton
import QtQuick

QtObject {

    enum FileStatus {
        FileAnalysing,
        FileClean,
        FileInfected,
        FileCopyError,
        FileAnalysisError
    }

}
